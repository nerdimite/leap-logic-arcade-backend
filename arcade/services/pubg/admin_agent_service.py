from typing import Dict, List, Optional

from arcade.core.dao.teams_dao import TeamsDao
from arcade.services.pubg.agent_service import AgentService


class AdminAgentService:
    """Service for admin operations on agents."""

    # Default configuration for new agents
    DEFAULT_SYSTEM_MESSAGE = """You are a dumb AI assistant."""

    DEFAULT_TEMPERATURE = 0.8

    DEFAULT_TOOLS = []

    def __init__(self):
        """Initialize the admin service with required DAOs and services."""
        self.teams_dao = TeamsDao()
        self.agent_service = AgentService()

    def initialize_team_agent(self, team_name: str) -> None:
        """Initialize an agent for a newly registered team with default configuration.

        Args:
            team_name: Name of the team to initialize agent for

        Raises:
            ValueError: If team doesn't exist
        """
        # Verify team exists
        team = self.teams_dao.get_team(team_name)
        if not team:
            raise ValueError(f"Team '{team_name}' does not exist")

        # Set default configuration
        self.agent_service.update_agent_config(
            team_name=team_name,
            system_message=self.DEFAULT_SYSTEM_MESSAGE,
            temperature=self.DEFAULT_TEMPERATURE,
        )

        # Add default tools
        for tool in self.DEFAULT_TOOLS:
            self.agent_service.add_agent_tool(
                team_name=team_name,
                tool_name=tool["name"],
                description=tool["description"],
            )

    def initialize_all_teams(self) -> Dict[str, str]:
        """Initialize agents for all registered teams that don't have agents yet.

        Returns:
            Dict mapping team names to initialization status ("success" or error message)
        """
        results = {}
        teams = self.teams_dao.get_all_teams()

        for team in teams:
            team_name = team["teamName"]
            try:
                # Check if agent already exists
                agent_state = self.agent_service.get_agent_state(team_name)

                # Only initialize if agent doesn't exist or has no configuration
                if not agent_state or (
                    "instructions" not in agent_state and "tools" not in agent_state
                ):
                    self.initialize_team_agent(team_name)
                    results[team_name] = "success"
                else:
                    results[team_name] = "agent already initialized"

            except Exception as e:
                results[team_name] = f"error: {str(e)}"

        return results

    def reset_team_agent(self, team_name: str) -> None:
        """Reset an agent to default configuration.

        Args:
            team_name: Name of the team whose agent to reset

        Raises:
            ValueError: If team doesn't exist
        """
        # Verify team exists
        if not self.teams_dao.get_team(team_name):
            raise ValueError(f"Team '{team_name}' does not exist")

        # Get current tools to remove them
        current_tools = self.agent_service.get_agent_tools(team_name)
        for tool in current_tools:
            self.agent_service.delete_agent_tool(
                team_name=team_name, tool_name=tool["name"]
            )

        # Set back to defaults
        self.initialize_team_agent(team_name)

    def get_uninitialized_teams(self) -> List[str]:
        """Get list of team names that don't have initialized agents.

        Returns:
            List of team names without initialized agents
        """
        uninitialized = []
        teams = self.teams_dao.get_all_teams()

        for team in teams:
            team_name = team["teamName"]
            agent_state = self.agent_service.get_agent_state(team_name)

            if not agent_state or (
                "instructions" not in agent_state and "tools" not in agent_state
            ):
                uninitialized.append(team_name)

        return uninitialized

    def clean_all_agents(self) -> Dict[str, str]:
        """Clean/reset all agents by deleting their configurations.

        This is a destructive operation that will remove all agent configurations.
        Teams will need to be reinitialized after this operation.

        Returns:
            Dict containing operation status and count of agents cleaned
        """
        teams = self.teams_dao.get_all_teams()
        cleaned_count = 0
        errors = []

        for team in teams:
            team_name = team["teamName"]
            try:
                # Get current state to check if agent exists
                agent_state = self.agent_service.get_agent_state(team_name)
                if agent_state:
                    # Delete the agent's entry completely
                    self.agent_service.agents_dao.delete_item({"teamName": team_name})
                    cleaned_count += 1
            except Exception as e:
                errors.append(f"{team_name}: {str(e)}")

        return {
            "status": "success" if not errors else "partial_success",
            "cleaned_count": cleaned_count,
            "errors": errors if errors else None,
        }
