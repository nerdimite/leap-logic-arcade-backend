import os
from datetime import datetime
from unittest.mock import patch

import pytest

from arcade.config.constants import (
    ARCADE_STATE_TABLE,
    MAX_VOTES_PER_TEAM,
    PP_IMAGES_TABLE,
    PP_LEADERBOARD_TABLE,
    TEAMS_TABLE,
)
from arcade.core.dao.images_dao import ImagesDao
from arcade.core.dao.leaderboard_dao import LeaderboardDao
from arcade.core.dao.state_dao import StateDao
from arcade.core.dao.teams_dao import TeamsDao
from arcade.services.pic_perfect.main import PicPerfectService
from arcade.types import ChallengeState


@pytest.mark.integration
class TestPicPerfectServiceIntegration:
    """Integration tests for PicPerfectService using moto."""

    @pytest.fixture(scope="function")
    def images_dao(self, dynamodb_resource, setup_test_tables):
        """Create ImagesDao instance."""
        # Initialize the DAO and patch it to use the test table name
        TEST_IMAGES_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + PP_IMAGES_TABLE
        with patch(
            "arcade.config.constants.PP_IMAGES_TABLE",
            TEST_IMAGES_TABLE,
        ):
            dao = ImagesDao()
            dao.table = dynamodb_resource.Table(TEST_IMAGES_TABLE)
            return dao

    @pytest.fixture(scope="function")
    def state_dao(self, dynamodb_resource, setup_test_tables):
        """Create StateDao instance."""
        # Initialize the DAO and patch it to use the test table name
        TEST_STATE_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + ARCADE_STATE_TABLE
        with patch(
            "arcade.config.constants.ARCADE_STATE_TABLE",
            TEST_STATE_TABLE,
        ):
            dao = StateDao()
            dao.table = dynamodb_resource.Table(TEST_STATE_TABLE)
            return dao

    @pytest.fixture(scope="function")
    def leaderboard_dao(self, dynamodb_resource, setup_test_tables):
        """Create LeaderboardDao instance."""
        # Initialize the DAO and patch it to use the test table name
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

    @pytest.fixture(scope="function")
    def teams_dao(self, dynamodb_resource, setup_test_tables):
        """Create TeamsDao instance."""
        # Initialize the DAO and patch it to use the test table name
        TEST_TEAMS_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + TEAMS_TABLE
        with patch(
            "arcade.config.constants.TEAMS_TABLE",
            TEST_TEAMS_TABLE,
        ):
            dao = TeamsDao()
            dao.table = dynamodb_resource.Table(TEST_TEAMS_TABLE)
            return dao

    @pytest.fixture(scope="function")
    def setup_initial_data(self, images_dao, state_dao, leaderboard_dao, teams_dao):
        """Setup all required tables with initial data."""
        # Initialize challenge state
        state_dao.initialize_challenge("pic-perfect", {})
        state_dao.update_challenge_state(
            "pic-perfect",
            {
                "state": ChallengeState.SUBMISSION.value,
                "metadata": {"hiddenImageSet": False, "hiddenImageRevealed": False},
            },
        )

        # Register teams
        teams = ["team1", "team2", "team3"]
        for team in teams:
            teams_dao.register_team(team, [])

        # Initialize empty leaderboard
        for team in teams:
            leaderboard_dao.update_score(
                "pic-perfect",
                team,
                {
                    "deceptionPoints": 0,
                    "discoveryPoints": 0,
                    "totalPoints": 0,
                    "votedForHidden": False,
                },
            )

    @pytest.fixture(scope="function")
    def service(
        self, images_dao, state_dao, leaderboard_dao, teams_dao, setup_initial_data
    ):
        """Create PicPerfectService instance with real DAOs."""
        return PicPerfectService(
            images_dao=images_dao,
            state_dao=state_dao,
            leaderboard_dao=leaderboard_dao,
            teams_dao=teams_dao,
        )

    def test_submit_team_image(self, service, images_dao, leaderboard_dao):
        """Test submitting a team image."""
        # Arrange
        team_name = "team1"
        image_url = "http://example.com/image1.png"
        prompt = "test prompt"

        # Act
        result = service.submit_team_image(team_name, image_url, prompt)

        # Assert
        assert result["success"] is True
        assert result["team_name"] == team_name
        assert result["image_url"] == image_url

        # Verify image was saved to database
        team_image = images_dao.get_team_image(team_name)
        assert team_image is not None
        assert team_image["imageUrl"] == image_url
        assert team_image["prompt"] == prompt

        # Verify leaderboard was updated
        team_score = leaderboard_dao.get_team_score("pic-perfect", team_name)
        assert team_score["imageUrl"] == image_url

    def test_submit_image_wrong_state(self, service, state_dao):
        """Test submitting a team image when challenge is not in submission state."""
        # Arrange
        team_name = "team1"
        image_url = "http://example.com/image1.png"
        prompt = "test prompt"

        # Change challenge state to voting
        state_dao.update_challenge_state(
            "pic-perfect", {"state": ChallengeState.VOTING.value}
        )

        # Act & Assert
        with pytest.raises(ValueError, match=f"Challenge is not in submission state"):
            service.submit_team_image(team_name, image_url, prompt)

    def test_get_team_status(self, service, images_dao):
        """Test getting team status."""
        # Arrange
        team_name = "team1"
        image_url = "http://example.com/image1.png"
        prompt = "test prompt"

        # Submit an image
        images_dao.add_image(team_name, image_url, prompt)

        # Act
        result = service.get_team_status(team_name)

        # Assert
        assert result["has_submitted"] is True
        assert result["image_details"]["teamName"] == team_name
        assert result["image_details"]["imageUrl"] == image_url
        assert result["votes_given"] == []
        assert result["votes_remaining"] == MAX_VOTES_PER_TEAM

    

    def test_voting_workflow(self, service, images_dao, leaderboard_dao, state_dao):
        """Test the complete voting workflow."""
        # Arrange
        # Set up hidden image
        images_dao.add_hidden_image("http://example.com/hidden.png", "hidden prompt")

        # Submit images for all teams
        for i, team in enumerate(["team1", "team2", "team3"]):
            images_dao.add_image(
                team, f"http://example.com/image{i+1}.png", f"prompt{i+1}"
            )

        # Change challenge state to voting
        state_dao.update_challenge_state(
            "pic-perfect", {"state": ChallengeState.VOTING.value}
        )

        # Act - Get voting pool for team1
        voting_pool = service.get_voting_pool("team1")

        # Assert
        assert len(voting_pool) == 3  # team2, team3, and HIDDEN_IMAGE
        assert any(img["teamName"] == "HIDDEN_IMAGE" for img in voting_pool)
        assert not any(img["teamName"] == "team1" for img in voting_pool)

        # Act - Cast votes from team1 to team2 and HIDDEN_IMAGE
        result = service.cast_votes("team1", ["team2", "HIDDEN_IMAGE"])

        # Assert
        assert result["success"] is True
        assert len(result["voted_teams"]) == 2
        assert result["remaining_votes"] == MAX_VOTES_PER_TEAM - 2

        # Verify votes were recorded
        team2_image = images_dao.get_team_image("team2")
        assert "team1" in team2_image["votes"]

        hidden_image = images_dao.get_hidden_image()
        assert "team1" in hidden_image["votes"]

        team1_image = images_dao.get_team_image("team1")
        assert "team2" in team1_image["votesGiven"]
        assert "HIDDEN_IMAGE" in team1_image["votesGiven"]

        # Check if discovery points were awarded for voting for hidden image
        team1_score = leaderboard_dao.get_team_score("pic-perfect", "team1")
        assert team1_score["discoveryPoints"] == 10
        assert team1_score["votedForHidden"] is True

    def test_get_leaderboard(self, service, leaderboard_dao, state_dao, images_dao):
        """Test getting the leaderboard."""
        # Arrange
        # Update leaderboard with some scores
        leaderboard_dao.update_score(
            "pic-perfect",
            "team1",
            {
                "deceptionPoints": 6,
                "discoveryPoints": 10,
                "totalPoints": 16,
                "imageUrl": "http://example.com/image1.png",
            },
        )

        leaderboard_dao.update_score(
            "pic-perfect",
            "team2",
            {
                "deceptionPoints": 3,
                "discoveryPoints": 0,
                "totalPoints": 3,
                "imageUrl": "http://example.com/image2.png",
            },
        )

        # Add hidden image
        images_dao.add_hidden_image("http://example.com/hidden.png", "hidden prompt")

        # Set challenge state to COMPLETE
        state_dao.update_challenge_state(
            "pic-perfect", {"state": ChallengeState.COMPLETE.value}
        )

        # Act
        result = service.get_leaderboard()

        # Assert
        assert len(result["leaderboard"]) == 3  # team1, team2, team3
        assert result["hidden_image"]["teamName"] == "HIDDEN_IMAGE"
        assert result["hidden_image"]["imageUrl"] == "http://example.com/hidden.png"
        assert result["challenge_state"] == ChallengeState.COMPLETE.value

        # Check scores and order (should be sorted by total points)
        assert result["leaderboard"][0]["teamName"] == "team1"
        assert result["leaderboard"][0]["totalPoints"] == 16
        assert result["leaderboard"][1]["teamName"] == "team2"
        assert result["leaderboard"][1]["totalPoints"] == 3
