from typing import Any, Dict, List, Optional

from arcade.types import ChallengeState


class IPicPerfectService:
    """Interface for Pic Perfect challenge business logic."""

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
        ...

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
        ...

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
        ...

    def get_voting_pool(self, requesting_team: str) -> List[Dict]:
        """
        Get all images available for voting, excluding the requesting team's image.

        Args:
            requesting_team: Identifier of the team requesting the voting pool

        Returns:
            List of image details (team name, image URL, prompt) for voting
        """
        ...

    def get_team_status(self, team_name: str) -> Dict:
        """
        Get a team's current submission and voting status.

        Args:
            team_name: Identifier of the team to check

        Returns:
            Dict containing submission status, image details (if submitted),
            list of teams voted for, and remaining votes
        """
        ...

    def calculate_scores(self) -> List[Dict]:
        """
        Calculate scores for all teams based on voting results.

        Scoring logic:
        - 3 points per vote received (deception points)
        - 10 points for correctly identifying hidden image (discovery points)

        Returns:
            List of team scores with deception, discovery, and total points
        """
        ...

    def get_leaderboard(self) -> Dict:
        """
        Get the current leaderboard with team rankings and scores.

        Returns:
            Dict containing:
            - List of teams with scores, ranked by total points
            - Hidden image details
            - Current challenge state
        """
        ...

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
        ...

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
        ...

    def get_submission_status(self) -> Dict:
        """
        Get the status of team submissions.

        Checks which teams have submitted images against the total registered teams.

        Returns:
            Dict containing counts of teams submitted, total teams, list of pending teams,
            and a flag indicating if the challenge can transition to voting phase
        """
        ...

    def get_voting_status(self) -> Dict:
        """
        Get the status of team voting.

        Checks which teams have used all their votes against the total participating teams.

        Returns:
            Dict containing counts of teams that have completed voting, total teams,
            list of pending teams, and a flag indicating if the challenge can transition to scoring phase
        """
        ...

    def can_transition_to_voting(self) -> bool:
        """
        Check if the challenge can transition to voting phase.

        Returns:
            Boolean indicating if all teams have submitted entries
        """
        ...

    def can_transition_to_scoring(self) -> bool:
        """
        Check if the challenge can transition to scoring phase.

        Returns:
            Boolean indicating if voting period should be closed
        """
        ...

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
        ...
