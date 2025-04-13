from typing import Dict, List, Optional, Protocol, Set


class ITeamsDao(Protocol):
    """Interface for team operations in the arcade system."""

    def register_team(self, team_name: str, members: Optional[Set[str]] = None) -> bool:
        """
        Register a new team in the system.

        Args:
            team_name: Unique identifier for the team
            members: Optional set of member identifiers

        Returns:
            Boolean indicating success or failure

        Raises:
            ValueError: If team already exists
        """
        ...

    def get_team(self, team_name: str) -> Optional[Dict]:
        """
        Get team details by team name.

        Args:
            team_name: Identifier of the team

        Returns:
            Dict containing team details if found, None otherwise
        """
        ...

    def update_team(self, team_name: str, updates: Dict) -> bool:
        """
        Update team attributes.

        Args:
            team_name: Identifier of the team
            updates: Dictionary of attributes to update

        Returns:
            Boolean indicating success or failure
        """
        ...

    def delete_team(self, team_name: str) -> bool:
        """
        Delete a team from the system.

        Args:
            team_name: Identifier of the team

        Returns:
            Boolean indicating success or failure
        """
        ...

    def get_all_teams(self) -> List[Dict]:
        """
        Get all registered teams.

        Returns:
            List of team details
        """
        ...

    def get_team_count(self) -> int:
        """
        Get the total number of registered teams.

        Returns:
            Integer count of teams
        """
        ...
