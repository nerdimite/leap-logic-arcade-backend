from typing import Any, Dict, List, Optional

from arcade.types import ChallengeState


class PicPerfectService:
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
