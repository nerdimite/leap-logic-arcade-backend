import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Union

import boto3
import pytz
from botocore.exceptions import ClientError

from arcade.config.constants import PUBG_AGENTS_TABLE
from arcade.core.dao.base_ddb import DynamoDBDao
from arcade.core.interfaces.agents_dao import IAgentsDao

logger = logging.getLogger(__name__)


class AgentsDao(DynamoDBDao, IAgentsDao):
    """DAO for managing agent configurations in DynamoDB."""

    def __init__(self):
        """Initialize the DAO with the agents table."""
        super().__init__(PUBG_AGENTS_TABLE)

    def get_agent_state(self, team_name: str) -> dict:
        """Get the agent state for a given team."""
        try:
            response = self.get_item({"teamName": team_name})
            return response if response else {}
        except ClientError as e:
            logger.error(f"Error getting agent state for team {team_name}: {str(e)}")
            raise

    def update_agent_config(
        self,
        team_name: str,
        instructions: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        """Update the agent configuration for a team."""
        try:
            if instructions is None and temperature is None:
                raise ValueError(
                    "At least one of instructions or temperature must be provided"
                )

            updates = {}
            if instructions is not None:
                updates["instructions"] = instructions
            if temperature is not None:
                updates["temperature"] = temperature

            self.update_item(key={"teamName": team_name}, updates=updates)
        except ClientError as e:
            logger.error(f"Error updating agent config for team {team_name}: {str(e)}")
            raise

    def get_agent_tools(self, team_name: str) -> List[Dict[str, str]]:
        """Get the list of tools available for an agent."""
        try:
            response = self.get_item({"teamName": team_name})
            return response.get("tools", []) if response else []
        except ClientError as e:
            logger.error(f"Error getting agent tools for team {team_name}: {str(e)}")
            raise

    def add_agent_tool(self, team_name: str, tool: Dict[str, str]) -> None:
        """Add/update a tool to the agent's toolset."""
        try:
            # Get current tools
            current_tools = self.get_agent_tools(team_name)

            # Add new tool if it doesn't exist
            tool_exists = any(t.get("name") == tool.get("name") for t in current_tools)
            if not tool_exists:
                current_tools.append(tool)
                self.update_item(
                    key={"teamName": team_name}, updates={"tools": current_tools}
                )
            if tool_exists:
                # Update the tool
                existing_tool_index = next(
                    (
                        i
                        for i, t in enumerate(current_tools)
                        if t.get("name") == tool.get("name")
                    ),
                )
                current_tools[existing_tool_index] = tool
                self.update_item(
                    key={"teamName": team_name}, updates={"tools": current_tools}
                )
        except ClientError as e:
            logger.error(f"Error adding agent tool for team {team_name}: {str(e)}")
            raise

    def delete_agent_tool(self, team_name: str, tool_name: str) -> None:
        """Delete a tool from the agent's toolset."""
        try:
            current_tools = self.get_agent_tools(team_name)
            updated_tools = [t for t in current_tools if t.get("name") != tool_name]

            self.update_item(
                key={"teamName": team_name}, updates={"tools": updated_tools}
            )
        except ClientError as e:
            logger.error(f"Error deleting agent tool for team {team_name}: {str(e)}")
            raise

    def update_previous_response_id(self, team_name: str, response_id: str) -> None:
        """Update the previous response ID for an agent."""
        try:
            self.update_item(
                key={"teamName": team_name}, updates={"previousResponseId": response_id}
            )
        except ClientError as e:
            logger.error(
                f"Error updating previous response ID for team {team_name}: {str(e)}"
            )
            raise
