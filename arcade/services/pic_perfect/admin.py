from typing import Any, Dict, List, Optional

from arcade.types import ChallengeState


class PicPerfectAdminService:
    """Interface for Pic Perfect challenge business logic."""

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
