from datetime import datetime
from typing import Dict, List, Optional, Set

import pytz

from arcade.config.constants import TEAMS_TABLE
from arcade.core.dao.base_ddb import DynamoDBDao
from arcade.core.interfaces.teams_dao import ITeamsDao


class TeamsDao(DynamoDBDao, ITeamsDao):
    """
    Data Access Object for handling team operations.

    DynamoDB Table Schema:
    - Primary Key: teamName (String) - Team identifier
    - Attributes:
        - createdAt (String) - ISO format timestamp of team creation
        - lastActive (String) - ISO format timestamp of last activity
        - members (StringSet) - Set of member identifiers
    """

    def __init__(self):
        """Initialize the DAO with the teams table name from constants."""
        super().__init__(table_name=TEAMS_TABLE)

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
        # Check if team already exists
        existing_team = self.get_team(team_name)
        if existing_team:
            raise ValueError(f"Team '{team_name}' already exists")

        # Create timestamp
        current_time = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

        # Create item
        item = {
            "teamName": team_name,
            "createdAt": current_time,
            "lastActive": current_time,
            "members": members
            or set(["PLACEHOLDER"]),  # Use placeholder for empty sets
        }

        # Store item
        return self.put_item(item)

    def get_team(self, team_name: str) -> Optional[Dict]:
        """
        Get team details by team name.

        Args:
            team_name: Identifier of the team

        Returns:
            Dict containing team details if found, None otherwise
        """
        return self.get_item({"teamName": team_name})

    def update_team(self, team_name: str, updates: Dict) -> bool:
        """
        Update team attributes.

        Args:
            team_name: Identifier of the team
            updates: Dictionary of attributes to update

        Returns:
            Boolean indicating success or failure
        """
        # Update lastActive timestamp
        updates["lastActive"] = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

        return self.update_item(key={"teamName": team_name}, updates=updates)

    def delete_team(self, team_name: str) -> bool:
        """
        Delete a team from the system.

        Args:
            team_name: Identifier of the team

        Returns:
            Boolean indicating success or failure
        """
        return self.delete_item({"teamName": team_name})

    def get_all_teams(self) -> List[Dict]:
        """
        Get all registered teams.

        Returns:
            List of team details
        """
        return self.scan(limit=100)  # Assuming we won't have more than 100 teams

    def get_team_count(self) -> int:
        """
        Get the total number of registered teams.

        Returns:
            Integer count of teams
        """
        teams = self.get_all_teams()
        return len(teams)
