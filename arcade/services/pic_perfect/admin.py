import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from arcade.config.constants import PP_LEADERBOARD_TABLE
from arcade.core.dao.images_dao import ImagesDao
from arcade.core.dao.leaderboard_dao import LeaderboardDao
from arcade.core.dao.state_dao import StateDao
from arcade.core.dao.teams_dao import TeamsDao
from arcade.types import ChallengeState

logger = logging.getLogger(__name__)


class PicPerfectAdminService:
    """Interface for Pic Perfect challenge business logic."""

    def __init__(
        self,
        images_dao: ImagesDao,
        state_dao: StateDao,
        leaderboard_dao: LeaderboardDao,
        teams_dao: TeamsDao,
        challenge_id: str = "pic-perfect",
    ):
        """
        Initialize the Pic Perfect Admin service with required dependencies.

        Args:
            images_dao: Data access object for image operations
            state_dao: Data access object for challenge state operations
            leaderboard_dao: Data access object for leaderboard operations
            teams_dao: Data access object for team operations
            challenge_id: Identifier for the challenge
        """
        self.images_dao = images_dao
        self.state_dao = state_dao
        self.leaderboard_dao = leaderboard_dao
        self.teams_dao = teams_dao
        self.challenge_id = challenge_id

    def submit_hidden_image(self, image_url: str, prompt: str) -> Dict:
        """
        Submit the hidden original image (admin only).

        Args:
            image_url: URL to the original image
            prompt: Text prompt describing the image

        Returns:
            Dict containing submission status and any error messages

        Raises:
            ValueError: If hidden image already exists
        """
        # Check if challenge is in submission state
        challenge_state = self.state_dao.get_challenge_state(self.challenge_id)
        if not challenge_state:
            raise ValueError(f"Challenge {self.challenge_id} not initialized")

        if challenge_state.get("state") != ChallengeState.SUBMISSION.value:
            raise ValueError(
                f"Challenge is not in submission state. Current state: {challenge_state.get('state')}"
            )

        # Check if hidden image already exists
        existing_hidden = self.images_dao.get_hidden_image()
        if existing_hidden:
            raise ValueError("Hidden image already exists and cannot be replaced")

        # Submit hidden image
        try:
            result = self.images_dao.add_hidden_image(image_url, prompt)

            # Update challenge metadata to indicate hidden image is set
            metadata = challenge_state.get("metadata", {})
            metadata["hiddenImageSet"] = True
            metadata["hiddenImageRevealed"] = False

            self.state_dao.update_challenge_state(
                self.challenge_id, {"metadata": metadata}
            )

            return {
                "success": True,
                "message": "Hidden image submitted successfully",
                "timestamp": result.get("timestamp"),
                "image_url": image_url,
            }
        except Exception as e:
            logger.error(f"Error submitting hidden image: {str(e)}")
            return {"success": False, "message": str(e)}

    def calculate_scores(self) -> List[Dict]:
        """
        Calculate scores for all teams based on voting results.

        Scoring logic:
        - 3 points per vote received (deception points)
        - 10 points for correctly identifying hidden image (discovery points)

        Returns:
            List of team scores with deception, discovery, and total points
        """
        # Check if challenge is in scoring state
        challenge_state = self.state_dao.get_challenge_state(self.challenge_id)
        if not challenge_state:
            raise ValueError(f"Challenge {self.challenge_id} not initialized")

        if challenge_state.get("state") != ChallengeState.SCORING.value:
            raise ValueError(
                f"Challenge is not in scoring state. Current state: {challenge_state.get('state')}"
            )

        # Get all images to calculate deception points
        all_team_images = self.images_dao.get_all_images(exclude_teams=["HIDDEN_IMAGE"])

        # Count votes received by each team
        votes_received = {}
        for image in all_team_images:
            team_name = image.get("teamName")
            _votes_rec = image.get("votes", set())
            if "PLACEHOLDER" in _votes_rec:
                _votes_rec.remove("PLACEHOLDER")
            votes_received[team_name] = len(_votes_rec)

        # Calculate scores for each team
        team_scores = []
        for image in all_team_images:
            team_name = image.get("teamName")

            # Calculate deception points (3 points per vote received)
            deception_points = votes_received[team_name] * 3

            # Update score in leaderboard
            score_updates = {
                "deceptionPoints": deception_points,
            }

            votes_given = list(image.get("votesGiven", set()))
            discovery_points = 10 if "HIDDEN_IMAGE" in votes_given else 0

            total_points = deception_points + discovery_points

            score_updates["discoveryPoints"] = discovery_points
            score_updates["totalPoints"] = total_points

            # Update leaderboard
            self.leaderboard_dao.update_score(
                self.challenge_id, team_name, score_updates
            )

            # Add to results
            team_scores.append(
                {
                    "teamName": team_name,
                    "deceptionPoints": deception_points,
                    "discoveryPoints": discovery_points,
                    "totalPoints": total_points,
                    "votesReceived": votes_received[team_name],
                }
            )

        # Sort by total points
        team_scores.sort(key=lambda x: x["totalPoints"], reverse=True)

        return team_scores

    def finalize_challenge(self) -> Dict:
        """
        Finalize the challenge, calculate final scores, and transition to completed state.

        This method:
        1. Calculates final scores for all teams
        2. Updates the leaderboard with final results
        3. Transitions the challenge state to COMPLETE using StateDao
        4. Records the end time of the challenge
        5. Updates metadata to indicate the hidden image is revealed

        Returns:
            Dict containing success status, number of teams scored, and any error messages
        """
        try:
            # Calculate final scores
            team_scores = self.calculate_scores()

            # Update challenge state to COMPLETE
            challenge_state = self.state_dao.get_challenge_state(self.challenge_id)
            if not challenge_state:
                raise ValueError(f"Challenge {self.challenge_id} not initialized")

            # Update metadata to reveal hidden image
            metadata = challenge_state.get("metadata", {})
            metadata["hiddenImageRevealed"] = True

            # Finalize challenge
            self.state_dao.update_challenge_state(
                self.challenge_id,
                {
                    "state": ChallengeState.COMPLETE.value,
                    "metadata": metadata,
                    "endTime": datetime.now().isoformat(),
                },
            )

            return {
                "success": True,
                "message": "Challenge finalized successfully",
                "teams_scored": len(team_scores),
                "final_leaderboard": team_scores,
            }
        except Exception as e:
            logger.error(f"Error finalizing challenge: {str(e)}")
            return {"success": False, "message": str(e)}

    def transition_challenge_state(self, target_state: ChallengeState) -> Dict:
        """
        Transition the challenge to a new state.

        Args:
            target_state: The state to transition to

        Returns:
            Dict containing success status, previous state, current state, and any error messages

        Raises:
            ValueError: If the state transition is not valid
        """
        try:
            # Get current challenge state
            challenge_state = self.state_dao.get_challenge_state(self.challenge_id)
            if not challenge_state:
                raise ValueError(f"Challenge {self.challenge_id} not initialized")

            current_state = ChallengeState(challenge_state.get("state"))

            # Validate state transition
            if not self._is_valid_transition(current_state, target_state):
                raise ValueError(
                    f"Invalid state transition from {current_state.value} to {target_state.value}"
                )

            # Update challenge state
            self.state_dao.update_challenge_state(
                self.challenge_id, {"state": target_state.value}
            )

            return {
                "success": True,
                "message": f"Challenge state transitioned from {current_state.value} to {target_state.value}",
                "previous_state": current_state.value,
                "current_state": target_state.value,
            }
        except Exception as e:
            logger.error(f"Error transitioning challenge state: {str(e)}")
            return {"success": False, "message": str(e)}

    def _is_valid_transition(
        self, current_state: ChallengeState, target_state: ChallengeState
    ) -> bool:
        """
        Check if a state transition is valid.

        Valid transitions:
        - LOCKED -> SUBMISSION
        - SUBMISSION -> VOTING (if all teams have submitted)
        - SUBMISSION -> LOCKED
        - VOTING -> SCORING (if voting period is complete)
        - VOTING -> LOCKED
        - SCORING -> COMPLETE
        - SCORING -> LOCKED
        - COMPLETE -> LOCKED

        Args:
            current_state: Current challenge state
            target_state: Target challenge state

        Returns:
            Boolean indicating if the transition is valid
        """
        if current_state == ChallengeState.LOCKED:
            return target_state == ChallengeState.SUBMISSION

        if current_state == ChallengeState.SUBMISSION:
            if target_state == ChallengeState.VOTING:
                return self.can_transition_to_voting()
            return target_state == ChallengeState.LOCKED

        if current_state == ChallengeState.VOTING:
            if target_state == ChallengeState.SCORING:
                return self.can_transition_to_scoring()
            return target_state == ChallengeState.LOCKED

        if current_state == ChallengeState.SCORING:
            return target_state in [ChallengeState.COMPLETE, ChallengeState.LOCKED]

        if current_state == ChallengeState.COMPLETE:
            return target_state == ChallengeState.LOCKED

        return False

    def can_transition_to_voting(self) -> bool:
        """
        Check if the challenge can transition to voting phase.

        Returns:
            Boolean indicating if all teams have submitted entries
        """
        # Get all teams
        all_teams = self.teams_dao.get_all_teams()
        total_teams = len(all_teams)

        # Get all submitted images
        all_images = self.images_dao.get_all_images()
        submitted_team_names = [image.get("teamName") for image in all_images]

        # Check if hidden image exists
        hidden_image = self.images_dao.get_hidden_image()
        if not hidden_image:
            return False

        # All teams must have submitted and hidden image must exist
        return len(submitted_team_names) == total_teams and total_teams > 0

    def can_transition_to_scoring(self) -> bool:
        """
        Check if the challenge can transition to scoring phase.

        Returns:
            Boolean indicating if voting period should be closed
        """
        # Get all teams with image submissions
        all_images = self.images_dao.get_all_images()
        participating_teams = [image.get("teamName") for image in all_images]
        total_teams = len(participating_teams)

        # Check which teams have used all their votes
        for team_name in participating_teams:
            remaining_votes = self.images_dao.get_votes_remaining(team_name)
            if remaining_votes > 0:
                return False

        # All teams must have used all their votes
        return total_teams > 0

    def start_challenge(
        self, image_url: str, prompt: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Initialize challenge and set hidden image in one operation (admin only).

        This method:
        1. Initializes the challenge with the given configuration
        2. Sets the hidden image
        3. Updates challenge metadata

        Args:
            image_url: URL to the original image
            prompt: Text prompt describing the image
            config: Optional challenge configuration parameters

        Returns:
            Dict containing success status, challenge state, and hidden image status
        """
        try:
            # Initialize challenge if not already initialized
            challenge_state = self.state_dao.get_challenge_state(self.challenge_id)

            if not challenge_state:
                # Initialize challenge with default or custom config
                self.state_dao.initialize_challenge(self.challenge_id, config)

                # Reset leaderboard if it exists
                self.leaderboard_dao.reset_leaderboard(self.challenge_id)

            # Set challenge state to SUBMISSION
            self.state_dao.update_challenge_state(
                self.challenge_id, {"state": ChallengeState.SUBMISSION.value}
            )

            # Submit hidden image
            hidden_result = self.submit_hidden_image(image_url, prompt)

            return {
                "success": True,
                "message": "Challenge started successfully",
                "challenge_state": ChallengeState.SUBMISSION.value,
                "hidden_image_status": hidden_result,
            }
        except Exception as e:
            logger.error(f"Error starting challenge: {str(e)}")
            return {"success": False, "message": str(e)}
