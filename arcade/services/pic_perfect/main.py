import logging
from typing import Any, Dict, List, Optional

from arcade.config.constants import MAX_VOTES_PER_TEAM, PP_LEADERBOARD_TABLE
from arcade.core.dao.images_dao import ImagesDao
from arcade.core.dao.leaderboard_dao import LeaderboardDao
from arcade.core.dao.state_dao import StateDao
from arcade.core.dao.teams_dao import TeamsDao
from arcade.types import ChallengeState

logger = logging.getLogger(__name__)


class PicPerfectService:
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
        Initialize the Pic Perfect service with required dependencies.

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

    def submit_team_image(self, team_name: str, image_url: str, prompt: str) -> Dict:
        """
        Submit a team's generated image to the challenge.

        Args:
            team_name: Identifier of the submitting team
            image_url: URL to the generated image
            prompt: Text prompt used to generate the image

        Returns:
            Dict containing submission status, timestamp, and any error messages

        Raises:
            ValueError: If team has already submitted an image
        """
        # Check if challenge is in submission state
        challenge_state = self.state_dao.get_challenge_state(self.challenge_id)
        if not challenge_state:
            raise ValueError(f"Challenge {self.challenge_id} not initialized")

        if challenge_state.get("state") != ChallengeState.SUBMISSION.value:
            raise ValueError(
                f"Challenge is not in submission state. Current state: {challenge_state.get('state')}"
            )

        # Check if team is registered
        team = self.teams_dao.get_team(team_name)
        if not team:
            raise ValueError(f"Team {team_name} is not registered")

        # Submit image
        try:
            result = self.images_dao.add_image(team_name, image_url, prompt)

            # Update leaderboard with team's image URL
            self.leaderboard_dao.update_score(
                self.challenge_id,
                team_name,
                {
                    "imageUrl": image_url,
                    "totalPoints": 0,
                    "deceptionPoints": 0,
                    "discoveryPoints": 0,
                },
            )

            return {
                "success": True,
                "message": "Image submitted successfully",
                "timestamp": result.get("timestamp"),
                "team_name": team_name,
                "image_url": image_url,
            }
        except Exception as e:
            logger.error(f"Error submitting image for team {team_name}: {str(e)}")
            return {"success": False, "message": str(e)}

    def cast_votes(self, team_name: str, voted_teams: List[str]) -> Dict:
        """
        Cast votes from a team to other teams' images.

        Args:
            team_name: Identifier of the voting team
            voted_teams: List of team identifiers receiving votes

        Returns:
            Dict containing voting results, list of successfully voted teams, and remaining votes

        Raises:
            ValueError: If team tries to vote more than MAX_VOTES_PER_TEAM times
                       If team tries to vote for their own image
                       If team tries to vote for the same image multiple times
        """
        # Check if challenge is in voting state
        challenge_state = self.state_dao.get_challenge_state(self.challenge_id)
        if not challenge_state:
            raise ValueError(f"Challenge {self.challenge_id} not initialized")

        if challenge_state.get("state") != ChallengeState.VOTING.value:
            raise ValueError(
                f"Challenge is not in voting state. Current state: {challenge_state.get('state')}"
            )

        # Verify team has submitted an image
        team_image = self.images_dao.get_team_image(team_name)
        if not team_image:
            raise ValueError(
                f"Team {team_name} has not submitted an image and cannot vote"
            )

        # Cast votes
        try:
            result = self.images_dao.vote_on_image(team_name, voted_teams)
            remaining_votes = self.images_dao.get_votes_remaining(team_name)

            # Check if team voted for the hidden image
            hidden_image = self.images_dao.get_hidden_image()
            if hidden_image and "HIDDEN_IMAGE" in voted_teams:
                # Team correctly identified the hidden image, award 10 discovery points
                self.leaderboard_dao.update_score(
                    self.challenge_id,
                    team_name,
                    {"discoveryPoints": 10, "votedForHidden": True},
                )

            return {
                "success": True,
                "message": "Votes cast successfully",
                "voted_teams": result.get("voted_for", []),
                "remaining_votes": remaining_votes,
            }
        except Exception as e:
            logger.error(f"Error casting votes for team {team_name}: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_voting_pool(self, requesting_team: str) -> List[Dict]:
        """
        Get all images available for voting, excluding the requesting team's image.

        Args:
            requesting_team: Identifier of the team requesting the voting pool

        Returns:
            List of image details (team name, image URL, prompt) for voting
        """
        # Check if challenge is in voting state
        challenge_state = self.state_dao.get_challenge_state(self.challenge_id)
        if not challenge_state:
            raise ValueError(f"Challenge {self.challenge_id} not initialized")

        if challenge_state.get("state") != ChallengeState.VOTING.value:
            raise ValueError(
                f"Challenge is not in voting state. Current state: {challenge_state.get('state')}"
            )

        # Get all images excluding the requesting team (hidden image is included by default)
        images = self.images_dao.get_all_images(exclude_teams=requesting_team)

        return images

    def get_team_status(self, team_name: str) -> Dict:
        """
        Get a team's current submission and voting status.

        Args:
            team_name: Identifier of the team to check

        Returns:
            Dict containing submission status, image details (if submitted),
            list of teams voted for, and remaining votes
        """
        # Get team image
        team_image = self.images_dao.get_team_image(team_name)

        # Get voting status
        votes_given = self.images_dao.get_votes_given_by_team(team_name)
        votes_remaining = self.images_dao.get_votes_remaining(team_name)

        # Get team score from leaderboard
        team_score = self.leaderboard_dao.get_team_score(self.challenge_id, team_name)

        return {
            "has_submitted": team_image is not None,
            "image_details": team_image if team_image else None,
            "votes_given": votes_given,
            "votes_remaining": votes_remaining,
            "score": team_score,
        }

    def get_leaderboard(self) -> Dict:
        """
        Get the current leaderboard with team rankings and scores.

        Returns:
            Dict containing:
            - List of teams with scores, ranked by total points
            - Hidden image details
            - Current challenge state
        """
        # Get leaderboard
        leaderboard = self.leaderboard_dao.get_leaderboard(self.challenge_id)

        # Get challenge state
        challenge_state = self.state_dao.get_challenge_state(self.challenge_id)

        # Get hidden image (only include if challenge is complete)
        hidden_image = None
        if (
            challenge_state
            and challenge_state.get("state") == ChallengeState.COMPLETE.value
        ):
            hidden_image = self.images_dao.get_hidden_image()

        return {
            "leaderboard": leaderboard,
            "hidden_image": hidden_image,
            "challenge_state": (
                challenge_state.get("state") if challenge_state else None
            ),
        }
