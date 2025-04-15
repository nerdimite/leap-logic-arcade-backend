from datetime import datetime
from typing import Dict, List, Optional

from arcade.config.constants import (
    DEFAULT_SYSTEM_MESSAGE,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOOLS,
)
from arcade.core.dao import PubgGameDao, StateDao, TeamsDao
from arcade.services.pubg.agent_service import AgentService


class AdminService:
    """Service for admin operations on PUBG."""

    CHALLENGE_ID = "pubg-challenge"

    def __init__(self):
        """Initialize the admin service with required DAOs and services."""
        self.teams_dao = TeamsDao()
        self.agent_service = AgentService()
        self.pubg_game_dao = PubgGameDao()
        self.state_dao = StateDao()

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
            system_message=DEFAULT_SYSTEM_MESSAGE,
            temperature=DEFAULT_TEMPERATURE,
        )

        # Add default tools
        for tool in DEFAULT_TOOLS:
            self.agent_service.add_agent_tool(
                team_name=team_name,
                tool_name=tool["name"],
                description=tool["description"],
            )

    def initialize_challenge(self) -> Dict[str, str]:
        """Initialize agents and game states for all registered teams that don't have them.

        Returns:
            Dict mapping team names to initialization status ("success" or error message)
        """
        results = {}
        teams = [
            team
            for team in self.teams_dao.get_all_teams()
            if team["teamName"] != "HIDDEN_IMAGE"
        ]
        challenge_state = self.state_dao.get_challenge_state(self.CHALLENGE_ID)
        if not challenge_state:
            self.state_dao.initialize_challenge(self.CHALLENGE_ID)

        for team in teams:
            team_name = team["teamName"]
            try:
                agent_initialized = False
                game_state_initialized = False

                # Check if agent already exists
                agent_state = self.agent_service.get_agent_state(team_name)

                # Only initialize agent if it doesn't exist or has no configuration
                if not agent_state or (
                    "instructions" not in agent_state and "tools" not in agent_state
                ):
                    self.initialize_team_agent(team_name)
                    agent_initialized = True

                # Check if game state already exists
                game_state = self.pubg_game_dao.get_team_game_state(team_name)

                # Initialize game state if it doesn't exist
                if not game_state:
                    self.pubg_game_dao.initialize_team_game(team_name)
                    game_state_initialized = True

                # Set appropriate result message
                if agent_initialized and game_state_initialized:
                    results[team_name] = "agent and game state initialized"
                elif agent_initialized:
                    results[team_name] = "agent initialized, game state already exists"
                elif game_state_initialized:
                    results[team_name] = "agent already exists, game state initialized"
                else:
                    results[team_name] = "agent and game state already initialized"

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

    def reset_team_game_state(self, team_name: str) -> None:
        """Reset a team's game state to initial values.

        Args:
            team_name: Name of the team whose game state to reset

        Raises:
            ValueError: If team doesn't exist
        """
        # Verify team exists
        if not self.teams_dao.get_team(team_name):
            raise ValueError(f"Team '{team_name}' does not exist")

        # Check if game state exists and delete it if it does
        game_state = self.pubg_game_dao.get_team_game_state(team_name)
        if game_state:
            self.pubg_game_dao.delete_item({"teamName": team_name})

        # Re-initialize game state
        self.pubg_game_dao.initialize_team_game(team_name)

    def get_uninitialized_teams(self) -> List[str]:
        """Get list of team names that don't have initialized agents or game states.

        Returns:
            List of team names without initialized agents or game states
        """
        uninitialized = []
        teams = [
            team
            for team in self.teams_dao.get_all_teams()
            if team["teamName"] != "HIDDEN_IMAGE"
        ]

        for team in teams:
            team_name = team["teamName"]
            agent_state = self.agent_service.get_agent_state(team_name)
            game_state = self.pubg_game_dao.get_team_game_state(team_name)

            # Check if either agent or game state is missing
            if (
                not agent_state
                or ("instructions" not in agent_state and "tools" not in agent_state)
            ) or not game_state:
                uninitialized.append(team_name)

        return uninitialized

    def clean_all_team_data(self) -> Dict[str, str]:
        """Clean/reset all team data by deleting agent configurations and game states.

        This is a destructive operation that will remove all agent configurations and game states.
        Teams will need to be reinitialized after this operation.

        Returns:
            Dict containing operation status and count of agents/game states cleaned
        """
        teams = [
            team
            for team in self.teams_dao.get_all_teams()
            if team["teamName"] != "HIDDEN_IMAGE"
        ]

        cleaned_agents_count = 0
        cleaned_game_states_count = 0
        errors = []

        self.state_dao.lock_challenge(self.CHALLENGE_ID)

        for team in teams:
            team_name = team["teamName"]
            try:
                # Clean agent data
                agent_state = self.agent_service.get_agent_state(team_name)
                if agent_state:
                    # Delete the agent's entry completely
                    self.agent_service.agents_dao.delete_item({"teamName": team_name})
                    cleaned_agents_count += 1

                # Clean game state data
                game_state = self.pubg_game_dao.get_team_game_state(team_name)
                if game_state:
                    # Delete the game state entry completely
                    self.pubg_game_dao.delete_item({"teamName": team_name})
                    cleaned_game_states_count += 1

            except Exception as e:
                errors.append(f"{team_name}: {str(e)}")

        return {
            "status": "success" if not errors else "partial_success",
            "cleaned_agents_count": cleaned_agents_count,
            "cleaned_game_states_count": cleaned_game_states_count,
            "total_cleaned": cleaned_agents_count + cleaned_game_states_count,
            "errors": errors if errors else None,
        }

    def reset_all_teams(self) -> Dict[str, str]:
        """Reset all teams' agents and game states to initial configuration.

        This operation resets both agent configurations and game states for all teams.

        Returns:
            Dict mapping team names to reset status
        """
        results = {}
        teams = [
            team
            for team in self.teams_dao.get_all_teams()
            if team["teamName"] != "HIDDEN_IMAGE"
        ]

        for team in teams:
            team_name = team["teamName"]
            try:
                # Reset agent
                self.reset_team_agent(team_name)

                # Reset game state
                self.reset_team_game_state(team_name)

                results[team_name] = "agent and game state reset successfully"
            except Exception as e:
                results[team_name] = f"error: {str(e)}"

        return results

    def get_leaderboard(self) -> Dict[str, str]:
        """Get the leaderboard for all teams.

        Returns:
            Dict mapping team names to leaderboard position
        """
        # Get all teams who have completed the mission and sort them by completion time
        teams = [
            team
            for team in self.teams_dao.get_all_teams()
            if team["teamName"] != "HIDDEN_IMAGE"
        ]
        completed_teams = []
        pending_teams = []
        for team in teams:
            team_name = team["teamName"]
            game_state = self.pubg_game_dao.get_team_game_state(team_name)
            if game_state and game_state.get("hasCompletedMission"):
                completed_teams.append(
                    {
                        "team_name": team_name,
                        "completion_time": game_state["completionTime"],
                    }
                )
            else:
                pending_teams.append(team_name)

        sorted_completed_teams = sorted(
            completed_teams, key=lambda x: datetime.fromisoformat(x["completion_time"])
        )

        return {
            "leaderboard": sorted_completed_teams,
            "pending_teams": pending_teams,
        }
