import datetime
from unittest.mock import MagicMock, patch

import pytest

from arcade.core.dao.state_dao import StateDao
from arcade.types import ChallengeState


@pytest.mark.unit
class TestStateDaoUnit:
    """Unit tests for StateDao class."""

    @pytest.fixture
    def state_dao(self):
        """Create a StateDao with mocked DynamoDB."""
        with patch("arcade.core.dao.base_ddb.boto3"):
            dao = StateDao()
            dao.get_item = MagicMock()
            dao.put_item = MagicMock()
            dao.update_item = MagicMock()
            dao.scan = MagicMock()
            return dao

    @pytest.fixture
    def mock_challenge_data(self):
        """Create sample challenge data for testing."""
        return {
            "challengeId": "test-challenge",
            "state": ChallengeState.SUBMISSION.value,
            "startTime": "2023-01-01T12:00:00",
            "metadata": {},
        }

    def test_get_challenge_state(self, state_dao, mock_challenge_data):
        """Test retrieving challenge state."""
        state_dao.get_item.return_value = mock_challenge_data

        result = state_dao.get_challenge_state("test-challenge")

        state_dao.get_item.assert_called_once_with({"challengeId": "test-challenge"})
        assert result == mock_challenge_data

    def test_update_challenge_state(self, state_dao):
        """Test updating challenge state."""
        state_dao.update_item.return_value = True
        updates = {"state": ChallengeState.VOTING.value}

        result = state_dao.update_challenge_state("test-challenge", updates)

        state_dao.update_item.assert_called_once_with(
            {"challengeId": "test-challenge"}, updates
        )
        assert result is True

    @patch("arcade.core.dao.state_dao.datetime")
    def test_initialize_challenge(self, mock_datetime, state_dao):
        """Test initializing a challenge."""
        # Mock the datetime to return a fixed timestamp
        mock_timestamp = "2023-01-01T12:00:00"
        mock_datetime.now.return_value.isoformat.return_value = mock_timestamp

        # Mock the put_item method to return True
        state_dao.put_item.return_value = True

        # Initialize a challenge with no config
        result = state_dao.initialize_challenge("test-challenge")

        # Check that put_item was called with the correct arguments
        expected_item = {
            "challengeId": "test-challenge",
            "state": ChallengeState.SUBMISSION.value,
            "startTime": mock_timestamp,
            "metadata": {},
        }
        state_dao.put_item.assert_called_once_with(expected_item)

        # Check that the method returns the expected challenge state
        assert result == expected_item

    @patch("arcade.core.dao.state_dao.datetime")
    def test_initialize_challenge_with_config(self, mock_datetime, state_dao):
        """Test initializing a challenge with custom config."""
        # Mock the datetime to return a fixed timestamp
        mock_timestamp = "2023-01-01T12:00:00"
        mock_datetime.now.return_value.isoformat.return_value = mock_timestamp

        # Mock the put_item method to return True
        state_dao.put_item.return_value = True

        # Initialize a challenge with custom config
        config = {"timeLimit": 3600, "maxSubmissions": 5}
        result = state_dao.initialize_challenge("test-challenge", config)

        # Check that put_item was called with the correct arguments
        expected_item = {
            "challengeId": "test-challenge",
            "state": ChallengeState.SUBMISSION.value,
            "startTime": mock_timestamp,
            "metadata": {},
            "config": config,
        }
        state_dao.put_item.assert_called_once_with(expected_item)

        # Check that the method returns the expected challenge state
        assert result == expected_item

    def test_initialize_challenge_failure(self, state_dao):
        """Test initializing a challenge when put_item fails."""
        # Mock the put_item method to return False
        state_dao.put_item.return_value = False

        # Initialize a challenge
        result = state_dao.initialize_challenge("test-challenge")

        # Check that the method returns an empty dict on failure
        assert result == {}

    @patch("arcade.core.dao.state_dao.datetime")
    def test_finalize_challenge(self, mock_datetime, state_dao):
        """Test finalizing a challenge."""
        # Mock the datetime to return a fixed timestamp
        mock_timestamp = "2023-01-01T18:00:00"
        mock_datetime.now.return_value.isoformat.return_value = mock_timestamp

        # Mock the update_challenge_state method to return True
        state_dao.update_challenge_state = MagicMock(return_value=True)

        # Finalize a challenge with no end_time provided
        result = state_dao.finalize_challenge("test-challenge")

        # Check that update_challenge_state was called with the correct arguments
        expected_updates = {
            "state": ChallengeState.COMPLETE.value,
            "endTime": mock_timestamp,
        }
        state_dao.update_challenge_state.assert_called_once_with(
            "test-challenge", expected_updates
        )

        # Check that the method returns True
        assert result is True

    def test_finalize_challenge_with_end_time(self, state_dao):
        """Test finalizing a challenge with a specific end time."""
        # Mock the update_challenge_state method to return True
        state_dao.update_challenge_state = MagicMock(return_value=True)

        # Finalize a challenge with a specific end_time
        custom_end_time = "2023-01-02T12:00:00"
        result = state_dao.finalize_challenge("test-challenge", custom_end_time)

        # Check that update_challenge_state was called with the correct arguments
        expected_updates = {
            "state": ChallengeState.COMPLETE.value,
            "endTime": custom_end_time,
        }
        state_dao.update_challenge_state.assert_called_once_with(
            "test-challenge", expected_updates
        )

        # Check that the method returns True
        assert result is True

    def test_lock_challenge(self, state_dao):
        """Test locking a challenge."""
        # Mock the update_challenge_state method to return True
        state_dao.update_challenge_state = MagicMock(return_value=True)

        # Lock a challenge
        result = state_dao.lock_challenge("test-challenge")

        # Check that update_challenge_state was called with the correct arguments
        expected_updates = {"state": ChallengeState.LOCKED.value}
        state_dao.update_challenge_state.assert_called_once_with(
            "test-challenge", expected_updates
        )

        # Check that the method returns True
        assert result is True

    def test_unlock_challenge(self, state_dao):
        """Test unlocking a challenge to default state."""
        # Mock the update_challenge_state method to return True
        state_dao.update_challenge_state = MagicMock(return_value=True)

        # Unlock a challenge
        result = state_dao.unlock_challenge("test-challenge")

        # Check that update_challenge_state was called with the correct arguments
        expected_updates = {"state": ChallengeState.SUBMISSION.value}
        state_dao.update_challenge_state.assert_called_once_with(
            "test-challenge", expected_updates
        )

        # Check that the method returns True
        assert result is True

    def test_unlock_challenge_custom_state(self, state_dao):
        """Test unlocking a challenge to a custom state."""
        # Mock the update_challenge_state method to return True
        state_dao.update_challenge_state = MagicMock(return_value=True)

        # Unlock a challenge to VOTING state
        result = state_dao.unlock_challenge("test-challenge", ChallengeState.VOTING)

        # Check that update_challenge_state was called with the correct arguments
        expected_updates = {"state": ChallengeState.VOTING.value}
        state_dao.update_challenge_state.assert_called_once_with(
            "test-challenge", expected_updates
        )

        # Check that the method returns True
        assert result is True

    def test_unlock_challenge_to_locked_state(self, state_dao):
        """Test unlocking a challenge to LOCKED state fails."""
        # Set up the mock for update_challenge_state
        update_mock = MagicMock(return_value=True)
        state_dao.update_challenge_state = update_mock

        # Attempt to unlock a challenge to LOCKED state
        result = state_dao.unlock_challenge("test-challenge", ChallengeState.LOCKED)

        # Check that update_challenge_state was not called
        update_mock.assert_not_called()

        # Check that the method returns False
        assert result is False

    def test_is_challenge_active_active(self, state_dao):
        """Test checking if a challenge is active when it is active."""
        # Mock get_challenge_state to return an active challenge
        state_dao.get_challenge_state = MagicMock(
            return_value={"state": ChallengeState.SUBMISSION.value}
        )

        # Check if the challenge is active
        result = state_dao.is_challenge_active("test-challenge")

        # Check that get_challenge_state was called
        state_dao.get_challenge_state.assert_called_once_with("test-challenge")

        # Check that the method returns True
        assert result is True

    def test_is_challenge_active_inactive(self, state_dao):
        """Test checking if a challenge is active when it is not active."""
        # Mock get_challenge_state to return an inactive challenge
        state_dao.get_challenge_state = MagicMock(
            return_value={"state": ChallengeState.COMPLETE.value}
        )

        # Check if the challenge is active
        result = state_dao.is_challenge_active("test-challenge")

        # Check that get_challenge_state was called
        state_dao.get_challenge_state.assert_called_once_with("test-challenge")

        # Check that the method returns False
        assert result is False

    def test_is_challenge_active_not_found(self, state_dao):
        """Test checking if a challenge is active when it does not exist."""
        # Mock get_challenge_state to return None
        state_dao.get_challenge_state = MagicMock(return_value=None)

        # Check if the challenge is active
        result = state_dao.is_challenge_active("test-challenge")

        # Check that get_challenge_state was called
        state_dao.get_challenge_state.assert_called_once_with("test-challenge")

        # Check that the method returns False
        assert result is False

    def test_is_challenge_locked_locked(self, state_dao):
        """Test checking if a challenge is locked when it is locked."""
        # Mock get_challenge_state to return a locked challenge
        state_dao.get_challenge_state = MagicMock(
            return_value={"state": ChallengeState.LOCKED.value}
        )

        # Check if the challenge is locked
        result = state_dao.is_challenge_locked("test-challenge")

        # Check that get_challenge_state was called
        state_dao.get_challenge_state.assert_called_once_with("test-challenge")

        # Check that the method returns True
        assert result is True

    def test_is_challenge_locked_unlocked(self, state_dao):
        """Test checking if a challenge is locked when it is not locked."""
        # Mock get_challenge_state to return an unlocked challenge
        state_dao.get_challenge_state = MagicMock(
            return_value={"state": ChallengeState.SUBMISSION.value}
        )

        # Check if the challenge is locked
        result = state_dao.is_challenge_locked("test-challenge")

        # Check that get_challenge_state was called
        state_dao.get_challenge_state.assert_called_once_with("test-challenge")

        # Check that the method returns False
        assert result is False

    def test_is_challenge_complete_complete(self, state_dao):
        """Test checking if a challenge is complete when it is complete."""
        # Mock get_challenge_state to return a complete challenge
        state_dao.get_challenge_state = MagicMock(
            return_value={"state": ChallengeState.COMPLETE.value}
        )

        # Check if the challenge is complete
        result = state_dao.is_challenge_complete("test-challenge")

        # Check that get_challenge_state was called
        state_dao.get_challenge_state.assert_called_once_with("test-challenge")

        # Check that the method returns True
        assert result is True

    def test_is_challenge_complete_incomplete(self, state_dao):
        """Test checking if a challenge is complete when it is not complete."""
        # Mock get_challenge_state to return an incomplete challenge
        state_dao.get_challenge_state = MagicMock(
            return_value={"state": ChallengeState.SUBMISSION.value}
        )

        # Check if the challenge is complete
        result = state_dao.is_challenge_complete("test-challenge")

        # Check that get_challenge_state was called
        state_dao.get_challenge_state.assert_called_once_with("test-challenge")

        # Check that the method returns False
        assert result is False

    def test_get_all_challenges(self, state_dao):
        """Test retrieving all challenges."""
        # Mock the scan method to return a list of challenges
        challenges = [
            {
                "challengeId": "challenge-1",
                "state": ChallengeState.SUBMISSION.value,
            },
            {
                "challengeId": "challenge-2",
                "state": ChallengeState.VOTING.value,
            },
        ]
        state_dao.scan.return_value = challenges

        # Get all challenges
        result = state_dao.get_all_challenges()

        # Check that scan was called
        state_dao.scan.assert_called_once()

        # Check that the method returns the list of challenges
        assert result == challenges
