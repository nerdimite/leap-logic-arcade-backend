from abc import ABC, abstractmethod
from typing import Dict, List


class IAgentsDao(ABC):
    """Interface for Agents DAO operations."""

    @abstractmethod
    def get_agent_state(self, team_name: str) -> dict:
        """Get the agent state for a given team.

        Args:
            team_name: The name of the team

        Returns:
            Dict containing the agent state including instructions, temperature, tools, etc.
        """
        pass

    @abstractmethod
    def update_agent_config(
        self, team_name: str, instructions: str, temperature: float
    ) -> None:
        """Update the agent configuration for a team.

        Args:
            team_name: The name of the team
            instructions: New instructions for the agent
            temperature: New temperature value for the agent
        """
        pass

    @abstractmethod
    def get_agent_tools(self, team_name: str) -> List[Dict[str, str]]:
        """Get the list of tools available for an agent.

        Args:
            team_name: The name of the team

        Returns:
            List of tool configurations
        """
        pass

    @abstractmethod
    def add_agent_tool(self, team_name: str, tool: Dict[str, str]) -> None:
        """Add a new tool to the agent's toolset.

        Args:
            team_name: The name of the team
            tool: Tool configuration to add
        """
        pass

    @abstractmethod
    def delete_agent_tool(self, team_name: str, tool_name: str) -> None:
        """Delete a tool from the agent's toolset.

        Args:
            team_name: The name of the team
            tool_name: Name of the tool to delete
        """
        pass

    @abstractmethod
    def update_previous_response_id(self, team_name: str, response_id: str) -> None:
        """Update the previous response ID for an agent.

        Args:
            team_name: The name of the team
            response_id: New response ID to set
        """
        pass
