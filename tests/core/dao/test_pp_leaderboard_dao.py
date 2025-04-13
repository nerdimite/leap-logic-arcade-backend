from unittest.mock import MagicMock, patch

import pytest

from arcade.core.dao.leaderboard_dao import LeaderboardDao


@pytest.mark.unit
class TestPPLeaderboardDaoUnit:
    """Unit tests for LeaderboardDao class with Pic Perfect challenge."""

    @pytest.fixture
    def leaderboard_dao(self):
        """Create a LeaderboardDao with mocked DynamoDB."""
        with patch("arcade.core.dao.base_ddb.boto3"):
            dao = LeaderboardDao()
            dao.get_item = MagicMock()
            dao.put_item = MagicMock()
            dao.update_item = MagicMock()
            dao.delete_item = MagicMock()
            dao.scan = MagicMock()
            dao.table = MagicMock()
            dao.table.query = MagicMock()
            return dao

    @pytest.fixture
    def challenge_id(self):
        """Return the Pic Perfect challenge ID."""
        return "pic-perfect"

    @pytest.fixture
    def mock_team_score(self):
        """Create sample team score data for testing."""
        return {
            "challengeId": "pic-perfect",
            "teamName": "test-team",
            "deceptionPoints": 6,
            "discoveryPoints": 10,
            "totalPoints": 16,
            "imageUrl": "https://example.com/image.jpg",
            "votedForHidden": True,
        }

    def test_update_score_existing_team(
        self, leaderboard_dao, challenge_id, mock_team_score
    ):
        """Test updating the score for an existing team."""
        # Set up mocks
        leaderboard_dao.get_team_score = MagicMock(return_value=mock_team_score)
        leaderboard_dao.update_item.return_value = True

        # Update the score
        updates = {"deceptionPoints": 9, "totalPoints": 19}
        result = leaderboard_dao.update_score(challenge_id, "test-team", updates)

        # Check that update_item was called with correct parameters
        leaderboard_dao.update_item.assert_called_once_with(
            {"challengeId": challenge_id, "teamName": "test-team"}, updates
        )
        assert result is True

    def test_update_score_new_team(self, leaderboard_dao, challenge_id):
        """Test updating the score for a new team."""
        # Set up mocks
        leaderboard_dao.get_team_score = MagicMock(return_value=None)
        leaderboard_dao.put_item.return_value = True

        # Create a new score entry
        score_data = {
            "deceptionPoints": 3,
            "discoveryPoints": 10,
            "totalPoints": 13,
            "imageUrl": "https://example.com/new-image.jpg",
            "votedForHidden": True,
        }
        result = leaderboard_dao.update_score(challenge_id, "new-team", score_data)

        # Check that put_item was called with correct parameters
        expected_item = {
            "challengeId": challenge_id,
            "teamName": "new-team",
            **score_data,
        }
        leaderboard_dao.put_item.assert_called_once_with(expected_item)
        assert result is True

    def test_get_leaderboard(self, leaderboard_dao, challenge_id):
        """Test retrieving and sorting the leaderboard."""
        # Set up mocks with unsorted data
        leaderboard_data = [
            {
                "challengeId": challenge_id,
                "teamName": "team-low",
                "totalPoints": 5,
            },
            {
                "challengeId": challenge_id,
                "teamName": "team-high",
                "totalPoints": 20,
            },
            {
                "challengeId": challenge_id,
                "teamName": "team-mid",
                "totalPoints": 10,
            },
        ]

        # Mock the query response
        leaderboard_dao.table.query.return_value = {"Items": leaderboard_data}

        # Get the leaderboard
        result = leaderboard_dao.get_leaderboard(challenge_id)

        # Check that query was called with correct parameters
        leaderboard_dao.table.query.assert_called_once()
        # Extract the KeyConditionExpression from the call
        call_args = leaderboard_dao.table.query.call_args[1]
        assert "KeyConditionExpression" in call_args

        # Verify the result is sorted by totalPoints in descending order
        assert len(result) == 3
        assert result[0]["teamName"] == "team-high"
        assert result[1]["teamName"] == "team-mid"
        assert result[2]["teamName"] == "team-low"

    def test_get_team_score(self, leaderboard_dao, challenge_id, mock_team_score):
        """Test retrieving a team's score."""
        # Set up mocks
        leaderboard_dao.get_item.return_value = mock_team_score

        # Get the team score
        result = leaderboard_dao.get_team_score(challenge_id, "test-team")

        # Check that get_item was called with correct parameters
        leaderboard_dao.get_item.assert_called_once_with(
            {"challengeId": challenge_id, "teamName": "test-team"}
        )
        assert result == mock_team_score

    def test_reset_leaderboard_success(self, leaderboard_dao, challenge_id):
        """Test resetting the leaderboard with successful deletions."""
        # Set up mocks
        leaderboard_entries = [
            {"challengeId": challenge_id, "teamName": "team1"},
            {"challengeId": challenge_id, "teamName": "team2"},
            {"challengeId": challenge_id, "teamName": "team3"},
        ]

        # Mock the query response
        leaderboard_dao.table.query.return_value = {"Items": leaderboard_entries}
        leaderboard_dao.delete_item.return_value = True

        # Reset the leaderboard
        result = leaderboard_dao.reset_leaderboard(challenge_id)

        # Check that query and delete_item were called
        leaderboard_dao.table.query.assert_called_once()
        assert leaderboard_dao.delete_item.call_count == 3
        leaderboard_dao.delete_item.assert_any_call(
            {"challengeId": challenge_id, "teamName": "team1"}
        )
        leaderboard_dao.delete_item.assert_any_call(
            {"challengeId": challenge_id, "teamName": "team2"}
        )
        leaderboard_dao.delete_item.assert_any_call(
            {"challengeId": challenge_id, "teamName": "team3"}
        )
        assert result is True

    def test_reset_leaderboard_partial_failure(self, leaderboard_dao, challenge_id):
        """Test resetting the leaderboard with some failed deletions."""
        # Set up mocks
        leaderboard_entries = [
            {"challengeId": challenge_id, "teamName": "team1"},
            {"challengeId": challenge_id, "teamName": "team2"},
            {"challengeId": challenge_id, "teamName": "team3"},
        ]

        # Mock the query response
        leaderboard_dao.table.query.return_value = {"Items": leaderboard_entries}

        # Make delete_item return True for team1, False for team2, True for team3
        leaderboard_dao.delete_item.side_effect = [True, False, True]

        # Reset the leaderboard
        result = leaderboard_dao.reset_leaderboard(challenge_id)

        # Check that query and delete_item were called
        leaderboard_dao.table.query.assert_called_once()
        assert leaderboard_dao.delete_item.call_count == 3
        leaderboard_dao.delete_item.assert_any_call(
            {"challengeId": challenge_id, "teamName": "team1"}
        )
        leaderboard_dao.delete_item.assert_any_call(
            {"challengeId": challenge_id, "teamName": "team2"}
        )
        leaderboard_dao.delete_item.assert_any_call(
            {"challengeId": challenge_id, "teamName": "team3"}
        )
        assert result is False

    @patch("arcade.core.dao.leaderboard_dao.logger")
    def test_reset_leaderboard_exception(
        self, mock_logger, leaderboard_dao, challenge_id
    ):
        """Test resetting the leaderboard when an exception occurs."""
        # Set up mocks
        leaderboard_dao.table.query.side_effect = Exception("Test exception")

        # Reset the leaderboard
        result = leaderboard_dao.reset_leaderboard(challenge_id)

        # Check that query was called and the exception was logged
        leaderboard_dao.table.query.assert_called_once()
        mock_logger.error.assert_called_once()
        assert result is False
