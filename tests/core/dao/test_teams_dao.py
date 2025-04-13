import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz

from arcade.core.dao.teams_dao import TeamsDao


@pytest.mark.unit
class TestTeamsDaoUnit:
    """Unit tests for TeamsDao class."""

    @pytest.fixture
    def mock_dynamodb_dao(self):
        """Create a mock TeamsDao with mocked DynamoDB methods."""
        with patch("arcade.core.dao.teams_dao.DynamoDBDao") as mock_ddb:
            teams_dao = TeamsDao()
            # Mock the methods inherited from DynamoDBDao
            teams_dao.get_item = MagicMock()
            teams_dao.put_item = MagicMock(return_value=True)
            teams_dao.update_item = MagicMock(return_value=True)
            teams_dao.delete_item = MagicMock(return_value=True)
            teams_dao.scan = MagicMock()
            yield teams_dao

    def test_register_team_success(self, mock_dynamodb_dao):
        """Test successful team registration."""
        # Arrange
        mock_dynamodb_dao.get_item.return_value = None  # Team doesn't exist yet
        team_name = "test_team"
        members = {"member1", "member2"}

        # Act
        result = mock_dynamodb_dao.register_team(team_name, members)

        # Assert
        assert result is True
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": team_name})
        mock_dynamodb_dao.put_item.assert_called_once()
        # Verify the item structure
        call_args = mock_dynamodb_dao.put_item.call_args[0][0]
        assert call_args["teamName"] == team_name
        assert call_args["members"] == members
        assert "createdAt" in call_args
        assert "lastActive" in call_args

    def test_register_team_with_default_members(self, mock_dynamodb_dao):
        """Test team registration with default members."""
        # Arrange
        mock_dynamodb_dao.get_item.return_value = None  # Team doesn't exist yet
        team_name = "test_team"

        # Act
        result = mock_dynamodb_dao.register_team(team_name)

        # Assert
        assert result is True
        call_args = mock_dynamodb_dao.put_item.call_args[0][0]
        assert call_args["members"] == {"PLACEHOLDER"}

    def test_register_team_already_exists(self, mock_dynamodb_dao):
        """Test registration when team already exists."""
        # Arrange
        mock_dynamodb_dao.get_item.return_value = {"teamName": "existing_team"}
        team_name = "existing_team"

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            mock_dynamodb_dao.register_team(team_name)
        assert f"Team '{team_name}' already exists" in str(excinfo.value)
        mock_dynamodb_dao.put_item.assert_not_called()

    def test_get_team_exists(self, mock_dynamodb_dao):
        """Test getting an existing team."""
        # Arrange
        expected_team = {"teamName": "test_team", "members": {"member1"}}
        mock_dynamodb_dao.get_item.return_value = expected_team
        team_name = "test_team"

        # Act
        result = mock_dynamodb_dao.get_team(team_name)

        # Assert
        assert result == expected_team
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": team_name})

    def test_get_team_not_exists(self, mock_dynamodb_dao):
        """Test getting a non-existent team."""
        # Arrange
        mock_dynamodb_dao.get_item.return_value = None
        team_name = "nonexistent_team"

        # Act
        result = mock_dynamodb_dao.get_team(team_name)

        # Assert
        assert result is None
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": team_name})

    def test_update_team(self, mock_dynamodb_dao):
        """Test updating a team."""
        # Arrange
        team_name = "test_team"
        updates = {"members": {"member1", "member2", "member3"}}

        # Use a fixed timestamp for testing
        current_time = "2023-01-01T12:00:00+05:30"

        # Mock the datetime.now().isoformat() chain in one go
        with patch("arcade.core.dao.teams_dao.datetime") as mock_datetime:
            # Configure the mock to return our timestamp for the whole chain
            mock_now = MagicMock()
            mock_now.return_value.isoformat.return_value = current_time
            mock_datetime.now = mock_now

            # Act
            result = mock_dynamodb_dao.update_team(team_name, updates)

        # Assert
        assert result is True
        # Check that lastActive was added to updates
        expected_updates = updates.copy()
        expected_updates["lastActive"] = current_time
        mock_dynamodb_dao.update_item.assert_called_once_with(
            key={"teamName": team_name}, updates=expected_updates
        )

    def test_delete_team(self, mock_dynamodb_dao):
        """Test deleting a team."""
        # Arrange
        team_name = "test_team"

        # Act
        result = mock_dynamodb_dao.delete_team(team_name)

        # Assert
        assert result is True
        mock_dynamodb_dao.delete_item.assert_called_once_with({"teamName": team_name})

    def test_get_all_teams(self, mock_dynamodb_dao):
        """Test getting all teams."""
        # Arrange
        expected_teams = [
            {"teamName": "team1", "members": {"member1"}},
            {"teamName": "team2", "members": {"member2"}},
        ]
        mock_dynamodb_dao.scan.return_value = expected_teams

        # Act
        result = mock_dynamodb_dao.get_all_teams()

        # Assert
        assert result == expected_teams
        mock_dynamodb_dao.scan.assert_called_once_with(limit=100)

    def test_get_team_count(self, mock_dynamodb_dao):
        """Test getting team count."""
        # Arrange
        teams = [
            {"teamName": "team1", "members": {"member1"}},
            {"teamName": "team2", "members": {"member2"}},
            {"teamName": "team3", "members": {"member3"}},
        ]
        mock_dynamodb_dao.scan.return_value = teams

        # Act
        result = mock_dynamodb_dao.get_team_count()

        # Assert
        assert result == 3
        mock_dynamodb_dao.scan.assert_called_once_with(limit=100)
