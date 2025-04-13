import os
from unittest.mock import MagicMock, patch

import pytest

from arcade.config.constants import TEAMS_TABLE
from arcade.core.dao.teams_dao import TeamsDao


@pytest.mark.integration
class TestTeamsDaoIntegration:
    """Integration tests for TeamsDao class with DynamoDB."""

    @pytest.fixture
    def teams_dao(self, dynamodb_resource, setup_test_tables):
        """Create a TeamsDao instance with real DynamoDB mocked by moto."""
        # Initialize the DAO and patch it to use the test table name
        TEST_TEAMS_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + TEAMS_TABLE
        with patch(
            "arcade.config.constants.TEAMS_TABLE",
            TEST_TEAMS_TABLE,
        ):
            dao = TeamsDao()
            dao.table = dynamodb_resource.Table(TEST_TEAMS_TABLE)
            yield dao

    def test_register_team_integration(self, teams_dao):
        """Test team registration with DynamoDB integration."""
        # Arrange
        team_name = "integration_team"
        members = {"member1", "member2"}

        # Act
        result = teams_dao.register_team(team_name, members)

        # Assert
        assert result is True

        # Verify the team was registered by retrieving it
        saved_team = teams_dao.get_team(team_name)
        assert saved_team is not None
        assert saved_team["teamName"] == team_name
        # Convert to sets for comparison since order may vary
        assert set(saved_team["members"]) == members
        assert "createdAt" in saved_team
        assert "lastActive" in saved_team

    def test_get_team_integration(self, teams_dao):
        """Test get_team with DynamoDB integration."""
        # Arrange - First register a team
        team_name = "test_team_get"
        members = {"member1", "member2"}
        teams_dao.register_team(team_name, members)

        # Act
        result = teams_dao.get_team(team_name)

        # Assert
        assert result is not None
        assert result["teamName"] == team_name
        assert set(result["members"]) == members
        assert "createdAt" in result
        assert "lastActive" in result

    def test_update_team_integration(self, teams_dao):
        """Test update_team with DynamoDB integration."""
        # Arrange - First register a team
        team_name = "test_team_update"
        initial_members = {"member1", "member2"}
        teams_dao.register_team(team_name, initial_members)

        # Updated data
        updated_members = {"member1", "member2", "member3"}
        updates = {"members": updated_members}

        # Act
        # Use a fixed timestamp for testing
        current_time = "2023-01-01T12:00:00+05:30"
        with patch("arcade.core.dao.teams_dao.datetime") as mock_datetime:
            # Configure the mock to return our timestamp for the whole chain
            mock_now = MagicMock()
            mock_now.return_value.isoformat.return_value = current_time
            mock_datetime.now = mock_now

            result = teams_dao.update_team(team_name, updates)

        # Assert
        assert result is True

        # Verify the update was applied
        updated_team = teams_dao.get_team(team_name)
        assert set(updated_team["members"]) == updated_members
        assert updated_team["lastActive"] == current_time

    def test_delete_team_integration(self, teams_dao):
        """Test delete_team with DynamoDB integration."""
        # Arrange - First register a team
        team_name = "team_to_delete"
        members = {"member1", "member2"}
        teams_dao.register_team(team_name, members)

        # Verify the team exists
        assert teams_dao.get_team(team_name) is not None

        # Act
        result = teams_dao.delete_team(team_name)

        # Assert
        assert result is True

        # Verify the team was deleted
        assert teams_dao.get_team(team_name) is None

    def test_get_all_teams_integration(self, teams_dao):
        """Test get_all_teams with DynamoDB integration."""
        # Arrange - Register several teams
        team1 = "team1_all"
        team2 = "team2_all"

        teams_dao.register_team(team1, {"member1"})
        teams_dao.register_team(team2, {"member2"})

        # Act
        result = teams_dao.get_all_teams()

        # Assert
        assert len(result) >= 2  # May include teams from other tests
        team_names = [team["teamName"] for team in result]
        assert team1 in team_names
        assert team2 in team_names

    def test_get_team_count_integration(self, teams_dao):
        """Test get_team_count with DynamoDB integration."""
        # Arrange - Register several teams if not already present
        # (since we can't control exact count with shared DB)
        existing_count = teams_dao.get_team_count()

        # Add at least 3 teams
        for i in range(3):
            team_name = f"team_count_{i}"
            if teams_dao.get_team(team_name) is None:
                teams_dao.register_team(team_name, {f"member_{i}"})

        # Act
        result = teams_dao.get_team_count()

        # Assert
        assert result >= existing_count + 3
