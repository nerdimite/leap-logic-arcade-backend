import datetime
import os
from unittest.mock import patch

import pytest

from arcade.config.constants import ARCADE_STATE_TABLE
from arcade.core.dao.state_dao import StateDao
from arcade.types import ChallengeState


@pytest.mark.integration
class TestStateDaoIntegration:
    """Integration tests for StateDao class using moto."""

    @pytest.fixture
    def state_dao(self, dynamodb_resource, setup_test_tables):
        """Create a StateDao with mocked DynamoDB."""
        TEST_ARCADE_STATE_TABLE = (
            os.environ["DYNAMODB_TABLE_PREFIX"] + ARCADE_STATE_TABLE
        )
        with patch(
            "arcade.config.constants.ARCADE_STATE_TABLE",
            TEST_ARCADE_STATE_TABLE,
        ):
            dao = StateDao()
            dao.table = dynamodb_resource.Table(TEST_ARCADE_STATE_TABLE)
            return dao

    def test_initialize_and_get_challenge(self, state_dao):
        """Test initializing a challenge and retrieving it."""
        # Initialize a challenge with no config
        challenge_id = "test-challenge"
        state_dao.initialize_challenge(challenge_id)

        # Get the challenge state
        result = state_dao.get_challenge_state(challenge_id)

        # Verify the result
        assert result is not None
        assert result["challengeId"] == challenge_id
        assert result["state"] == ChallengeState.SUBMISSION.value
        assert "startTime" in result
        assert "metadata" in result

    def test_initialize_with_config_and_get_challenge(self, state_dao):
        """Test initializing a challenge with custom config and retrieving it."""
        # Initialize a challenge with custom config
        challenge_id = "test-challenge-config"
        custom_config = {"timeLimit": 3600, "maxSubmissions": 5}
        state_dao.initialize_challenge(challenge_id, custom_config)

        # Get the challenge state
        result = state_dao.get_challenge_state(challenge_id)

        # Verify the result
        assert result is not None
        assert result["challengeId"] == challenge_id
        assert result["state"] == ChallengeState.SUBMISSION.value
        assert "startTime" in result
        assert "metadata" in result
        assert "config" in result
        assert result["config"] == custom_config

    def test_update_challenge_state(self, state_dao):
        """Test updating a challenge state."""
        # Initialize a challenge
        challenge_id = "update-test-challenge"
        state_dao.initialize_challenge(challenge_id)

        # Update the challenge state to VOTING
        update_result = state_dao.update_challenge_state(
            challenge_id, {"state": ChallengeState.VOTING.value}
        )

        # Verify the update was successful
        assert update_result is True

        # Get the updated challenge state
        result = state_dao.get_challenge_state(challenge_id)

        # Verify the state was updated
        assert result["state"] == ChallengeState.VOTING.value

    def test_finalize_challenge(self, state_dao):
        """Test finalizing a challenge."""
        # Initialize a challenge
        challenge_id = "finalize-test-challenge"
        state_dao.initialize_challenge(challenge_id)

        # Finalize the challenge
        custom_end_time = "2023-01-01T12:00:00"
        finalize_result = state_dao.finalize_challenge(challenge_id, custom_end_time)

        # Verify the finalization was successful
        assert finalize_result is True

        # Get the finalized challenge state
        result = state_dao.get_challenge_state(challenge_id)

        # Verify the state was updated to COMPLETE and endTime was set
        assert result["state"] == ChallengeState.COMPLETE.value
        assert result["endTime"] == custom_end_time

    def test_lock_and_unlock_challenge(self, state_dao):
        """Test locking and unlocking a challenge."""
        # Initialize a challenge
        challenge_id = "lock-unlock-test-challenge"
        state_dao.initialize_challenge(challenge_id)

        # Lock the challenge
        lock_result = state_dao.lock_challenge(challenge_id)

        # Verify the locking was successful
        assert lock_result is True

        # Get the locked challenge state
        locked_result = state_dao.get_challenge_state(challenge_id)

        # Verify the state was updated to LOCKED
        assert locked_result["state"] == ChallengeState.LOCKED.value

        # Unlock the challenge to VOTING state
        unlock_result = state_dao.unlock_challenge(challenge_id, ChallengeState.VOTING)

        # Verify the unlocking was successful
        assert unlock_result is True

        # Get the unlocked challenge state
        unlocked_result = state_dao.get_challenge_state(challenge_id)

        # Verify the state was updated to VOTING
        assert unlocked_result["state"] == ChallengeState.VOTING.value

    def test_is_challenge_active(self, state_dao):
        """Test checking if a challenge is active."""
        # Initialize some challenges with different states
        active_id = "active-test-challenge"
        inactive_id = "inactive-test-challenge"
        nonexistent_id = "nonexistent-test-challenge"

        # Create active challenge in SUBMISSION state
        state_dao.initialize_challenge(active_id)

        # Create inactive challenge in COMPLETE state
        state_dao.initialize_challenge(inactive_id)
        state_dao.finalize_challenge(inactive_id)

        # Check if challenges are active
        assert state_dao.is_challenge_active(active_id) is True
        assert state_dao.is_challenge_active(inactive_id) is False
        assert state_dao.is_challenge_active(nonexistent_id) is False

    def test_is_challenge_locked(self, state_dao):
        """Test checking if a challenge is locked."""
        # Initialize some challenges with different states
        locked_id = "locked-test-challenge"
        unlocked_id = "unlocked-test-challenge"

        # Create locked challenge
        state_dao.initialize_challenge(locked_id)
        state_dao.lock_challenge(locked_id)

        # Create unlocked challenge in SUBMISSION state
        state_dao.initialize_challenge(unlocked_id)

        # Check if challenges are locked
        assert state_dao.is_challenge_locked(locked_id) is True
        assert state_dao.is_challenge_locked(unlocked_id) is False

    def test_is_challenge_complete(self, state_dao):
        """Test checking if a challenge is complete."""
        # Initialize some challenges with different states
        complete_id = "complete-test-challenge"
        incomplete_id = "incomplete-test-challenge"

        # Create complete challenge
        state_dao.initialize_challenge(complete_id)
        state_dao.finalize_challenge(complete_id)

        # Create incomplete challenge in SUBMISSION state
        state_dao.initialize_challenge(incomplete_id)

        # Check if challenges are complete
        assert state_dao.is_challenge_complete(complete_id) is True
        assert state_dao.is_challenge_complete(incomplete_id) is False

    def test_get_all_challenges(self, state_dao):
        """Test retrieving all challenges."""
        # Initialize multiple challenges
        state_dao.initialize_challenge("challenge-1")
        state_dao.initialize_challenge("challenge-2")
        state_dao.initialize_challenge("challenge-3")

        # Get all challenges
        results = state_dao.get_all_challenges()

        # Verify that all challenges were retrieved
        assert len(results) >= 3
        challenge_ids = [item["challengeId"] for item in results]
        assert "challenge-1" in challenge_ids
        assert "challenge-2" in challenge_ids
        assert "challenge-3" in challenge_ids

    def test_full_challenge_lifecycle(self, state_dao):
        """Test a complete challenge lifecycle with state transitions."""
        challenge_id = "lifecycle-test-challenge"

        # 1. Initialize challenge
        init_result = state_dao.initialize_challenge(challenge_id)
        assert init_result["state"] == ChallengeState.SUBMISSION.value

        # 2. Verify challenge is active
        assert state_dao.is_challenge_active(challenge_id) is True

        # 3. Transition to VOTING state
        state_dao.update_challenge_state(
            challenge_id, {"state": ChallengeState.VOTING.value}
        )
        voting_state = state_dao.get_challenge_state(challenge_id)
        assert voting_state["state"] == ChallengeState.VOTING.value

        # 4. Transition to SCORING state
        state_dao.update_challenge_state(
            challenge_id, {"state": ChallengeState.SCORING.value}
        )
        scoring_state = state_dao.get_challenge_state(challenge_id)
        assert scoring_state["state"] == ChallengeState.SCORING.value

        # 5. Finalize the challenge
        state_dao.finalize_challenge(challenge_id)
        complete_state = state_dao.get_challenge_state(challenge_id)
        assert complete_state["state"] == ChallengeState.COMPLETE.value
        assert "endTime" in complete_state

        # 6. Verify challenge is complete
        assert state_dao.is_challenge_complete(challenge_id) is True
        assert state_dao.is_challenge_active(challenge_id) is False
