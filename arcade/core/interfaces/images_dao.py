from typing import Dict, List, Optional, Protocol, Union


class IImagesDao(Protocol):
    """Interface for image submission and voting operations."""

    def add_image(self, team_name: str, image_url: str, prompt: str) -> Dict:
        """
        Add a team's image submission to the database.

        Args:
            team_name: Identifier of the submitting team
            image_url: URL to the generated image
            prompt: Text prompt used to generate the image

        Returns:
            Dict containing submission details
        """
        ...

    def add_hidden_image(self, image_url: str, prompt: str) -> Dict:
        """
        Add the hidden original image to the database.

        Args:
            image_url: URL to the original image
            prompt: Text prompt describing the image

        Returns:
            Dict containing submission details
        """
        ...

    def vote_on_image(
        self, voting_team: str, target_team: Union[str, List[str]]
    ) -> Dict:
        """
        Record votes cast by a team for another team's image.

        Args:
            voting_team: Identifier of the team casting votes
            target_team: Team or list of teams receiving votes

        Returns:
            Dict containing voting results
        """
        ...

    def get_all_images(
        self, exclude_teams: Optional[Union[List[str], str]] = None
    ) -> List[Dict]:
        """
        Get all submitted images, optionally excluding specific teams.

        Args:
            exclude_teams: Team(s) to exclude from results

        Returns:
            List of image details for all teams except excluded ones
        """
        ...

    def get_hidden_image(self) -> Optional[Dict]:
        """
        Get the hidden original image.

        Returns:
            Dict containing hidden image details if found, None otherwise
        """
        ...

    def get_team_image(self, team_name: str) -> Optional[Dict]:
        """
        Get a specific team's submitted image.

        Args:
            team_name: Identifier of the team

        Returns:
            Dict containing team's image details if found, None otherwise
        """
        ...

    def get_votes_given_by_team(self, team_name: str) -> List[str]:
        """
        Get list of teams that received votes from a specific team.

        Args:
            team_name: Identifier of the voting team

        Returns:
            List of team identifiers that received votes
        """
        ...

    def get_votes_remaining(self, team_name: str) -> int:
        """
        Calculate remaining votes available to a team.

        Args:
            team_name: Identifier of the team

        Returns:
            Number of remaining votes (0-3)
        """
        ...
