import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from arcade.config.constants import ARCADE_STATE_TABLE
from arcade.core.commons.logger import get_logger
from arcade.core.dao.base_ddb import DynamoDBDao
from arcade.core.interfaces.state_dao import IStateDao
from arcade.types import ChallengeState

logger = logging.getLogger(__name__)


class StateDao(DynamoDBDao, IStateDao):
    """
    Data Access Object for challenge state operations.

    This class provides operations for managing the state of various challenges
    in the arcade system using DynamoDB as the underlying storage.
    """

    def __init__(self, table_name: str = ARCADE_STATE_TABLE):
        """Initialize the StateDao with the arcade-challenge-state table."""
        super().__init__(table_name=table_name)

    def get_challenge_state(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a challenge.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Dict containing challenge state details if found, None otherwise
        """
        logger.info(f"Getting state for challenge: {challenge_id}")
        key = {"challengeId": challenge_id}
        return self.get_item(key)

    def update_challenge_state(
        self, challenge_id: str, state_updates: Dict[str, Any]
    ) -> bool:
        """
        Update a challenge's state attributes.

        Args:
            challenge_id: Identifier for the challenge
            state_updates: Dictionary of state attributes to update

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Updating state for challenge: {challenge_id}")
        key = {"challengeId": challenge_id}
        return self.update_item(key, state_updates)

    def initialize_challenge(
        self, challenge_id: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a challenge with default or custom configuration.

        Args:
            challenge_id: Identifier for the challenge
            config: Optional custom configuration parameters

        Returns:
            Dict containing the initialized challenge state
        """
        logger.info(f"Initializing challenge: {challenge_id}")

        # Get the current timestamp in ISO format
        current_time = datetime.now().isoformat()

        # Create challenge state item
        challenge_state = {
            "challengeId": challenge_id,
            "state": ChallengeState.SUBMISSION.value,
            "startTime": current_time,
            "metadata": {},
        }

        # Add optional configuration if provided
        if config:
            challenge_state["config"] = config

        # Save to DynamoDB
        success = self.put_item(challenge_state)

        if success:
            return challenge_state
        else:
            logger.error(f"Failed to initialize challenge: {challenge_id}")
            return {}

    def finalize_challenge(
        self, challenge_id: str, end_time: Optional[str] = None
    ) -> bool:
        """
        Finalize a challenge and record completion time.

        Args:
            challenge_id: Identifier for the challenge
            end_time: Optional ISO format timestamp for challenge completion

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Finalizing challenge: {challenge_id}")

        # Get the current timestamp if not provided
        if end_time is None:
            end_time = datetime.now().isoformat()

        # Update challenge state
        updates = {"state": ChallengeState.COMPLETE.value, "endTime": end_time}

        return self.update_challenge_state(challenge_id, updates)

    def lock_challenge(self, challenge_id: str) -> bool:
        """
        Lock a challenge to prevent access.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Locking challenge: {challenge_id}")
        updates = {"state": ChallengeState.LOCKED.value}
        return self.update_challenge_state(challenge_id, updates)

    def unlock_challenge(
        self,
        challenge_id: str,
        target_state: ChallengeState = ChallengeState.SUBMISSION,
    ) -> bool:
        """
        Unlock a challenge and set it to a target state.

        Args:
            challenge_id: Identifier for the challenge
            target_state: State to transition to when unlocking

        Returns:
            Boolean indicating success or failure
        """
        logger.info(
            f"Unlocking challenge: {challenge_id} to state: {target_state.value}"
        )

        # Ensure the target state is not LOCKED
        if target_state == ChallengeState.LOCKED:
            logger.error("Cannot unlock to LOCKED state")
            return False

        updates = {"state": target_state.value}
        return self.update_challenge_state(challenge_id, updates)

    def is_challenge_active(self, challenge_id: str) -> bool:
        """
        Check if a challenge is currently active.

        A challenge is considered active if it's in SUBMISSION, VOTING, or SCORING state.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating if challenge is active
        """
        logger.info(f"Checking if challenge is active: {challenge_id}")

        challenge_data = self.get_challenge_state(challenge_id)
        if not challenge_data:
            return False

        active_states = [
            ChallengeState.SUBMISSION.value,
            ChallengeState.VOTING.value,
            ChallengeState.SCORING.value,
        ]

        return challenge_data.get("state") in active_states

    def is_challenge_locked(self, challenge_id: str) -> bool:
        """
        Check if a challenge is currently locked.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating if challenge is locked
        """
        logger.info(f"Checking if challenge is locked: {challenge_id}")

        challenge_data = self.get_challenge_state(challenge_id)
        if not challenge_data:
            return False

        return challenge_data.get("state") == ChallengeState.LOCKED.value

    def is_challenge_complete(self, challenge_id: str) -> bool:
        """
        Check if a challenge is completed.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating if challenge is complete
        """
        logger.info(f"Checking if challenge is complete: {challenge_id}")

        challenge_data = self.get_challenge_state(challenge_id)
        if not challenge_data:
            return False

        return challenge_data.get("state") == ChallengeState.COMPLETE.value

    def get_all_challenges(self) -> List[Dict[str, Any]]:
        """
        Get information for all challenges.

        Returns:
            List of challenge state details for all challenges
        """
        logger.info("Getting all challenges")
        return self.scan()

    def delete_challenge_state(self, challenge_id: str) -> bool:
        """Delete the state for a specific challenge.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.delete_item({"challengeId": challenge_id})
            logger.info(f"Successfully deleted state for challenge {challenge_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting challenge state for {challenge_id}: {str(e)}")
            return False
