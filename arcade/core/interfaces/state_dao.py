from typing import Any, Dict, List, Optional, Protocol

from arcade.types import ChallengeState


class IStateDao(Protocol):
    """Interface for challenge state operations."""

    def get_challenge_state(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a challenge.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Dict containing challenge state details if found, None otherwise
        """
        ...

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
        ...

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
        ...

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
        ...

    def lock_challenge(self, challenge_id: str) -> bool:
        """
        Lock a challenge to prevent access.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating success or failure
        """
        ...

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
        ...

    def is_challenge_active(self, challenge_id: str) -> bool:
        """
        Check if a challenge is currently active.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating if challenge is active
        """
        ...

    def is_challenge_locked(self, challenge_id: str) -> bool:
        """
        Check if a challenge is currently locked.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating if challenge is locked
        """
        ...

    def is_challenge_complete(self, challenge_id: str) -> bool:
        """
        Check if a challenge is completed.

        Args:
            challenge_id: Identifier for the challenge

        Returns:
            Boolean indicating if challenge is complete
        """
        ...

    def get_all_challenges(self) -> List[Dict[str, Any]]:
        """
        Get information for all challenges.

        Returns:
            List of challenge state details for all challenges
        """
        ...
