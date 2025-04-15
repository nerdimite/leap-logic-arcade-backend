import logging
from datetime import datetime
from typing import Dict, Optional

import pytz
from dynamodb_json import json_util

from arcade.config.constants import DEFAULT_POWER_DISTRIBUTION, PUBG_GAME_STATE_TABLE
from arcade.core.commons.logger import get_logger
from arcade.core.dao.base_ddb import DynamoDBDao
from arcade.core.interfaces.pubg_game_dao import IPubgGameDao

logger = get_logger(__name__)


class PubgGameDao(DynamoDBDao, IPubgGameDao):
    """
    Data Access Object for PUBG game state operations.

    This class provides operations for managing the state of the PUBG game
    in the arcade system using DynamoDB as the underlying storage.
    """

    def __init__(self, table_name: str = PUBG_GAME_STATE_TABLE):
        """Initialize the PubgGameDao with the pubg-game-state table."""
        super().__init__(table_name=table_name)

    def get_team_game_state(self, team_name: str) -> Optional[Dict]:
        """
        Get the game state for a team.

        Args:
            team_name: The name of the team

        Returns:
            Dict containing the game state or None if not found
        """
        logger.info(f"Getting game state for team: {team_name}")
        key = {"teamName": team_name}
        return self.get_item(key)

    def update_team_game_state(self, team_name: str, state_updates: Dict) -> bool:
        """
        Update the game state for a team.

        Args:
            team_name: The name of the team
            state_updates: Dictionary containing state attributes to update

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Updating game state for team: {team_name}")
        key = {"teamName": team_name}
        return self.update_item(key, state_updates)

    def initialize_team_game(self, team_name: str) -> Dict:
        """
        Initialize a new game state for a team.

        Args:
            team_name: The name of the team

        Returns:
            Dict containing the initialized game state
        """
        logger.info(f"Initializing game state for team: {team_name}")

        # Create initial game state
        game_state = {
            "teamName": team_name,
            "systemAccess": False,
            "powerDistribution": DEFAULT_POWER_DISTRIBUTION,
            "isCourseSet": False,
            "isThrustSet": False,
            "hasCompletedMission": False,
            "completionTime": None,  # ISO 8601 format timestamp in IST
        }

        # Save to DynamoDB
        success = self.put_item(game_state)

        if success:
            return game_state
        else:
            logger.error(f"Failed to initialize game state for team: {team_name}")
            return {}

    def set_system_access(self, team_name: str, has_access: bool) -> bool:
        """
        Set the system access status for a team.

        Args:
            team_name: The name of the team
            has_access: Whether the team has access to the system

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Setting system access for team: {team_name} to {has_access}")
        updates = {"systemAccess": has_access}
        return self.update_team_game_state(team_name, updates)

    def update_power_distribution(
        self, team_name: str, power_distribution: Dict
    ) -> bool:
        """
        Update the power distribution for a team's ship.

        Args:
            team_name: The name of the team
            power_distribution: Dictionary containing power distribution settings

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Updating power distribution for team: {team_name}")
        updates = {"powerDistribution": power_distribution}
        return self.update_team_game_state(team_name, updates)

    def set_course_status(self, team_name: str, is_course_set: bool) -> bool:
        """
        Set the course status for a team's ship.

        Args:
            team_name: The name of the team
            is_course_set: Whether the course is set

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Setting course state for team: {team_name} to {is_course_set}")
        updates = {"isCourseSet": is_course_set}
        return self.update_team_game_state(team_name, updates)

    def set_thrust_status(self, team_name: str, is_thrust_set: bool) -> bool:
        """
        Set the thrust status for a team's ship.

        Args:
            team_name: The name of the team
            is_thrust_set: Whether the thrust is set

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Setting thrust state for team: {team_name} to {is_thrust_set}")
        updates = {"isThrustSet": is_thrust_set}
        return self.update_team_game_state(team_name, updates)

    def complete_mission(self, team_name: str, has_completed: bool) -> bool:
        """
        Set the mission completion status for a team.

        Args:
            team_name: The name of the team
            has_completed: Whether the team has completed the mission

        Returns:
            Boolean indicating success or failure
        """
        logger.info(
            f"Setting mission completion for team: {team_name} to {has_completed}"
        )
        updates = {
            "hasCompletedMission": has_completed,
            "completionTime": datetime.now(pytz.timezone("Asia/Kolkata")).isoformat(),
        }
        return self.update_team_game_state(team_name, updates)
