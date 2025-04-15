from abc import ABC, abstractmethod
from typing import Dict, Optional


class IPubgGameDao(ABC):
    """Interface for PUBG game state operations."""

    @abstractmethod
    def get_team_game_state(self, team_name: str) -> Optional[Dict]:
        """Get the game state for a team.

        Args:
            team_name: The name of the team

        Returns:
            Dict containing the game state or None if not found
        """
        pass

    @abstractmethod
    def update_team_game_state(self, team_name: str, state_updates: Dict) -> bool:
        """Update the game state for a team.

        Args:
            team_name: The name of the team
            state_updates: Dictionary containing state attributes to update

        Returns:
            Boolean indicating success or failure
        """
        pass

    @abstractmethod
    def initialize_team_game(self, team_name: str) -> Dict:
        """Initialize a new game state for a team.

        Args:
            team_name: The name of the team

        Returns:
            Dict containing the initialized game state
        """
        pass

    @abstractmethod
    def set_system_access(self, team_name: str, has_access: bool) -> bool:
        """Set the system access status for a team.

        Args:
            team_name: The name of the team
            has_access: Whether the team has access to the system

        Returns:
            Boolean indicating success or failure
        """
        pass

    @abstractmethod
    def update_power_distribution(
        self, team_name: str, power_distribution: Dict
    ) -> bool:
        """Update the power distribution for a team's ship.

        Args:
            team_name: The name of the team
            power_distribution: Dictionary containing power distribution settings

        Returns:
            Boolean indicating success or failure
        """
        pass

    @abstractmethod
    def set_course_status(self, team_name: str, is_course_set: bool) -> bool:
        """Set the course status for a team's ship.

        Args:
            team_name: The name of the team
            is_course_set: Whether the course is set

        Returns:
            Boolean indicating success or failure
        """
        pass

    @abstractmethod
    def set_thrust_status(self, team_name: str, is_thrust_set: bool) -> bool:
        """Set the thrust status for a team's ship.

        Args:
            team_name: The name of the team
            is_thrust_set: Whether the thrust is set

        Returns:
            Boolean indicating success or failure
        """
        pass

    @abstractmethod
    def complete_mission(self, team_name: str, has_completed: bool) -> bool:
        """Set the mission completion status for a team.

        Args:
            team_name: The name of the team
            has_completed: Whether the team has completed the mission

        Returns:
            Boolean indicating success or failure
        """
        pass
