import os
from unittest.mock import patch

import pytest

from arcade.config.constants import PP_LEADERBOARD_TABLE
from arcade.core.dao.leaderboard_dao import LeaderboardDao


@pytest.mark.integration
class TestPPLeaderboardDaoIntegration:
    """Integration tests for LeaderboardDao class with Pic Perfect challenge using moto."""

    @pytest.fixture
    def challenge_id(self):
        """Return the Pic Perfect challenge ID."""
        return "pic-perfect"

    @pytest.fixture
    def leaderboard_dao(self, dynamodb_resource, setup_test_tables):
        """Create a LeaderboardDao with mocked DynamoDB."""
        TEST_LEADERBOARD_TABLE = (
            os.environ["DYNAMODB_TABLE_PREFIX"] + PP_LEADERBOARD_TABLE
        )
        with patch(
            "arcade.config.constants.PP_LEADERBOARD_TABLE",
            TEST_LEADERBOARD_TABLE,
        ):
            dao = LeaderboardDao()
            dao.table = dynamodb_resource.Table(TEST_LEADERBOARD_TABLE)
            return dao

    def test_update_and_get_team_score(self, leaderboard_dao, challenge_id):
        """Test updating a team's score and retrieving it."""
        # Create initial score data
        team_name = "test-team"
        initial_score = {
            "deceptionPoints": 3,
            "discoveryPoints": 0,
            "totalPoints": 3,
            "imageUrl": "https://example.com/image.jpg",
            "votedForHidden": False,
        }

        # Update score for a new team
        result = leaderboard_dao.update_score(challenge_id, team_name, initial_score)
        assert result is True

        # Retrieve the team's score
        score = leaderboard_dao.get_team_score(challenge_id, team_name)
        assert score is not None
        assert score["challengeId"] == challenge_id
        assert score["teamName"] == team_name
        assert score["deceptionPoints"] == 3
        assert score["discoveryPoints"] == 0
        assert score["totalPoints"] == 3
        assert score["imageUrl"] == "https://example.com/image.jpg"
        assert score["votedForHidden"] is False

        # Update the existing score
        updated_score = {
            "deceptionPoints": 6,
            "discoveryPoints": 10,
            "totalPoints": 16,
            "votedForHidden": True,
        }
        result = leaderboard_dao.update_score(challenge_id, team_name, updated_score)
        assert result is True

        # Retrieve the updated score
        score = leaderboard_dao.get_team_score(challenge_id, team_name)
        assert score is not None
        assert score["deceptionPoints"] == 6
        assert score["discoveryPoints"] == 10
        assert score["totalPoints"] == 16
        assert score["votedForHidden"] is True
        # Original fields should still be present
        assert score["imageUrl"] == "https://example.com/image.jpg"

    def test_get_leaderboard_sorting(self, leaderboard_dao, challenge_id):
        """Test retrieving the leaderboard with proper sorting."""
        # Create multiple team scores with different point totals
        teams_data = [
            {
                "teamName": "team-low",
                "deceptionPoints": 0,
                "discoveryPoints": 0,
                "totalPoints": 0,
                "votedForHidden": False,
            },
            {
                "teamName": "team-mid",
                "deceptionPoints": 6,
                "discoveryPoints": 0,
                "totalPoints": 6,
                "votedForHidden": False,
            },
            {
                "teamName": "team-high",
                "deceptionPoints": 6,
                "discoveryPoints": 10,
                "totalPoints": 16,
                "votedForHidden": True,
            },
        ]

        # Add teams to the leaderboard
        for team_data in teams_data:
            team_name = team_data.pop("teamName")
            leaderboard_dao.update_score(challenge_id, team_name, team_data)

        # Get the leaderboard
        leaderboard = leaderboard_dao.get_leaderboard(challenge_id)

        # Verify the leaderboard is sorted by totalPoints in descending order
        assert len(leaderboard) == 3
        assert leaderboard[0]["teamName"] == "team-high"
        assert leaderboard[0]["totalPoints"] == 16
        assert leaderboard[1]["teamName"] == "team-mid"
        assert leaderboard[1]["totalPoints"] == 6
        assert leaderboard[2]["teamName"] == "team-low"
        assert leaderboard[2]["totalPoints"] == 0

    def test_reset_leaderboard(self, leaderboard_dao, challenge_id):
        """Test resetting the leaderboard."""
        # Add some teams to the leaderboard
        teams = ["team1", "team2", "team3"]
        for team in teams:
            leaderboard_dao.update_score(
                challenge_id,
                team,
                {
                    "deceptionPoints": 3,
                    "discoveryPoints": 0,
                    "totalPoints": 3,
                    "votedForHidden": False,
                },
            )

        # Verify teams are in the leaderboard
        leaderboard = leaderboard_dao.get_leaderboard(challenge_id)
        assert len(leaderboard) == 3

        # Reset the leaderboard
        result = leaderboard_dao.reset_leaderboard(challenge_id)
        assert result is True

        # Verify the leaderboard is empty
        empty_leaderboard = leaderboard_dao.get_leaderboard(challenge_id)
        assert len(empty_leaderboard) == 0

    def test_multiple_challenges(self, leaderboard_dao, challenge_id):
        """Test that leaderboards for different challenges are isolated."""
        # Add team to Pic Perfect challenge
        pp_team_data = {
            "deceptionPoints": 6,
            "discoveryPoints": 10,
            "totalPoints": 16,
            "votedForHidden": True,
        }
        leaderboard_dao.update_score(challenge_id, "shared-team", pp_team_data)

        # Add same team to a different challenge
        other_challenge = "treasure-hunt"
        other_team_data = {
            "points": 20,
            "totalPoints": 20,
            "foundTreasures": 2,
        }
        leaderboard_dao.update_score(other_challenge, "shared-team", other_team_data)

        # Get team scores from both challenges
        pp_score = leaderboard_dao.get_team_score(challenge_id, "shared-team")
        other_score = leaderboard_dao.get_team_score(other_challenge, "shared-team")

        # Verify each challenge has the correct data
        assert pp_score["totalPoints"] == 16
        assert pp_score["votedForHidden"] is True
        assert pp_score["deceptionPoints"] == 6

        assert other_score["totalPoints"] == 20
        assert "foundTreasures" in other_score
        assert "votedForHidden" not in other_score

        # Get leaderboards for both challenges
        pp_leaderboard = leaderboard_dao.get_leaderboard(challenge_id)
        other_leaderboard = leaderboard_dao.get_leaderboard(other_challenge)

        # Verify each leaderboard has only the relevant entries
        assert len(pp_leaderboard) == 1
        assert len(other_leaderboard) == 1

        # Reset one challenge and verify the other is unaffected
        leaderboard_dao.reset_leaderboard(challenge_id)

        assert len(leaderboard_dao.get_leaderboard(challenge_id)) == 0
        assert len(leaderboard_dao.get_leaderboard(other_challenge)) == 1

    def test_complete_leaderboard_workflow(self, leaderboard_dao, challenge_id):
        """Test a complete workflow for the leaderboard."""
        # 1. Create initial scores for multiple teams
        team1_data = {
            "deceptionPoints": 0,
            "discoveryPoints": 0,
            "totalPoints": 0,
            "imageUrl": "https://example.com/team1.jpg",
            "votedForHidden": False,
        }
        team2_data = {
            "deceptionPoints": 0,
            "discoveryPoints": 0,
            "totalPoints": 0,
            "imageUrl": "https://example.com/team2.jpg",
            "votedForHidden": False,
        }

        leaderboard_dao.update_score(challenge_id, "team1", team1_data)
        leaderboard_dao.update_score(challenge_id, "team2", team2_data)

        # 2. Verify initial leaderboard state
        initial_leaderboard = leaderboard_dao.get_leaderboard(challenge_id)
        assert len(initial_leaderboard) == 2
        # Initial ordering is undefined since both have 0 points

        # 3. Update team1 score to reflect votes
        team1_update = {
            "deceptionPoints": 6,  # 2 votes received
            "totalPoints": 6,
        }
        leaderboard_dao.update_score(challenge_id, "team1", team1_update)

        # 4. Update team2 score to reflect hidden image discovery
        team2_update = {
            "deceptionPoints": 3,  # 1 vote received
            "discoveryPoints": 10,  # Hidden image found
            "totalPoints": 13,
            "votedForHidden": True,
        }
        leaderboard_dao.update_score(challenge_id, "team2", team2_update)

        # 5. Verify final leaderboard state and ordering
        final_leaderboard = leaderboard_dao.get_leaderboard(challenge_id)
        assert len(final_leaderboard) == 2

        # Team2 should be first with 13 points
        assert final_leaderboard[0]["teamName"] == "team2"
        assert final_leaderboard[0]["deceptionPoints"] == 3
        assert final_leaderboard[0]["discoveryPoints"] == 10
        assert final_leaderboard[0]["totalPoints"] == 13
        assert final_leaderboard[0]["votedForHidden"] is True

        # Team1 should be second with 6 points
        assert final_leaderboard[1]["teamName"] == "team1"
        assert final_leaderboard[1]["deceptionPoints"] == 6
        assert final_leaderboard[1]["discoveryPoints"] == 0
        assert final_leaderboard[1]["totalPoints"] == 6
        assert final_leaderboard[1]["votedForHidden"] is False
