from typing import Dict, List, Optional, Protocol, Union


class ILeaderboardDao(Protocol):
    """Interface for leaderboard operations."""

    def update_score(
        self,
        challenge_id: str,
        team_name: str,
        score_updates: Dict[str, Union[int, bool, str]],
    ) -> bool:
        """
        Update a team's score on the leaderboard.

        Args:
            challenge_id: Identifier of the challenge
            team_name: Identifier of the team
            score_updates: Dictionary of score attributes to update
                           Can include deceptionPoints, discoveryPoints, totalPoints,
                           votedForHidden, imageUrl

        Returns:
            Boolean indicating success or failure
        """
        ...

    def get_leaderboard(self, challenge_id: str) -> List[Dict]:
        """
        Get the current leaderboard with all team scores for a specific challenge.

        Args:
            challenge_id: Identifier of the challenge

        Returns:
            List of team scores sorted by total points in descending order
        """
        ...

    def get_team_score(self, challenge_id: str, team_name: str) -> Optional[Dict]:
        """
        Get a specific team's score from the leaderboard.

        Args:
            challenge_id: Identifier of the challenge
            team_name: Identifier of the team

        Returns:
            Dict containing team's score details if found, None otherwise
        """
        ...

    def reset_leaderboard(self, challenge_id: str) -> bool:
        """
        Reset the leaderboard for a specific challenge by removing all entries.

        Args:
            challenge_id: Identifier of the challenge

        Returns:
            Boolean indicating success or failure
        """
        ...
