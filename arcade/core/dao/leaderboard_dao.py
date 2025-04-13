import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

import pytz
from boto3.dynamodb.conditions import Key

from arcade.config.constants import PP_LEADERBOARD_TABLE
from arcade.core.commons.logger import get_logger
from arcade.core.dao.base_ddb import DynamoDBDao
from arcade.core.interfaces.leaderboard_dao import ILeaderboardDao

logger = logging.getLogger(__name__)


class LeaderboardDao(DynamoDBDao, ILeaderboardDao):
    """
    Data Access Object for leaderboard operations.

    DynamoDB Table Schema:
    - Partition Key: challengeId (String) - Challenge identifier (e.g., "pic-perfect")
    - Sort Key: teamName (String) - Team identifier
    - Attributes:
        - deceptionPoints (Number) - Points earned from votes received (3 per vote)
        - discoveryPoints (Number) - Points earned from correctly identifying hidden image (10 points)
        - totalPoints (Number) - Sum of deception and discovery points
        - imageUrl (String) - URL to the team's submitted image
        - votedForHidden (Boolean) - Whether the team correctly identified the hidden image
    """

    def __init__(self, table_name: str = PP_LEADERBOARD_TABLE):
        """Initialize the DAO with DynamoDB resource."""
        super().__init__(table_name=table_name)

    def update_score(
        self,
        challenge_id: str,
        team_name: str,
        score_updates: Dict[str, Union[int, bool, str]],
    ) -> bool:
        """
        Update a team's score on the leaderboard.

        Args:
            challenge_id: Identifier of the challenge
            team_name: Identifier of the team
            score_updates: Dictionary of score attributes to update
                           Can include deceptionPoints, discoveryPoints, totalPoints,
                           votedForHidden, imageUrl

        Returns:
            Boolean indicating success or failure
        """
        logger.info(
            f"Updating score for team: {team_name} in challenge: {challenge_id}"
        )

        # Check if team already exists in leaderboard
        existing_score = self.get_team_score(challenge_id, team_name)

        if existing_score:
            # Update existing score
            return self.update_item(
                {"challengeId": challenge_id, "teamName": team_name}, score_updates
            )
        else:
            # Create new leaderboard entry
            item = {"challengeId": challenge_id, "teamName": team_name, **score_updates}
            return self.put_item(item)

    def get_leaderboard(self, challenge_id: str) -> List[Dict]:
        """
        Get the current leaderboard with all team scores for a specific challenge.

        Args:
            challenge_id: Identifier of the challenge

        Returns:
            List of team scores sorted by total points in descending order
        """
        logger.info(f"Getting leaderboard for challenge: {challenge_id}")

        # Query for all entries from the leaderboard for this challenge
        response = self.table.query(
            KeyConditionExpression=Key("challengeId").eq(challenge_id)
        )
        leaderboard_entries = response.get("Items", [])

        # Sort by totalPoints in descending order
        sorted_leaderboard = sorted(
            leaderboard_entries, key=lambda x: x.get("totalPoints", 0), reverse=True
        )

        return sorted_leaderboard

    def get_team_score(self, challenge_id: str, team_name: str) -> Optional[Dict]:
        """
        Get a specific team's score from the leaderboard.

        Args:
            challenge_id: Identifier of the challenge
            team_name: Identifier of the team

        Returns:
            Dict containing team's score details if found, None otherwise
        """
        logger.info(f"Getting score for team: {team_name} in challenge: {challenge_id}")
        return self.get_item({"challengeId": challenge_id, "teamName": team_name})

    def reset_leaderboard(self, challenge_id: str) -> bool:
        """Reset the leaderboard for a challenge by deleting all entries.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all items for this challenge
            items = self.query(key_condition={"challengeId": challenge_id})

            # Delete each item
            for item in items:
                self.delete_item(
                    {"challengeId": challenge_id, "teamName": item["teamName"]}
                )

            logger.info(f"Successfully reset leaderboard for challenge {challenge_id}")
            return True
        except Exception as e:
            logger.error(
                f"Error resetting leaderboard for challenge {challenge_id}: {str(e)}"
            )
            return False
