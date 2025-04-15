from typing import Dict, List, Optional

from arcade.core.dao.agents_dao import AgentsDao
from arcade.services.pubg.tools import TOOLS


class AgentService:
    def __init__(self):
        self.agents_dao = AgentsDao()

    def update_agent_config(
        self,
        team_name: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        last_response_id: Optional[str] = None,
    ) -> None:
        """Update the agent configuration for a team.

        Args:
            team_name: Name of the team
            system_message: New system message/instructions for the agent
            temperature: New temperature value for the agent
            last_response_id: ID of the last response from the agent
        """
        if system_message is not None or temperature is not None:
            self.agents_dao.update_agent_config(
                team_name=team_name,
                instructions=system_message,
                temperature=temperature,
            )

        if last_response_id is not None:
            self.agents_dao.update_previous_response_id(
                team_name=team_name, response_id=last_response_id
            )

    def add_agent_tool(self, team_name: str, tool_name: str, description: str) -> None:
        """Add a new tool to the agent's toolset.

        Args:
            team_name: Name of the team
            tool_name: Name of the tool to add
            description: Description of the tool
        """
        # search for the tool in TOOLS
        tool = next((_tool for _tool in TOOLS if _tool["name"] == tool_name), None)
        if tool is None:
            raise ValueError(f"Tool {tool_name} not found in TOOLS")

        tool["description"] = description
        tool["parameters"]["description"] = description

        self.agents_dao.add_agent_tool(team_name=team_name, tool=tool)

    def delete_agent_tool(self, team_name: str, tool_name: str) -> None:
        """Delete a tool from the agent's toolset.

        Args:
            team_name: Name of the team
            tool_name: Name of the tool to delete
        """
        self.agents_dao.delete_agent_tool(team_name=team_name, tool_name=tool_name)

    def get_agent_state(self, team_name: str) -> Dict:
        """Get the current state of an agent.

        Args:
            team_name: Name of the team

        Returns:
            Dict containing the agent's current state
        """
        return self.agents_dao.get_agent_state(team_name=team_name)

    def get_agent_tools(self, team_name: str) -> List[Dict[str, str]]:
        """Get the list of tools available for an agent.

        Args:
            team_name: Name of the team

        Returns:
            List of tool configurations
        """
        return self.agents_dao.get_agent_tools(team_name=team_name)

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get the list of available tools.

        Returns:
            List of tool configurations
        """
        return TOOLS
