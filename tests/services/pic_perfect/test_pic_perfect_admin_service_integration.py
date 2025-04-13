import os
from datetime import datetime
from unittest.mock import patch

import pytest

from arcade.config.constants import (ARCADE_STATE_TABLE, MAX_VOTES_PER_TEAM,
                                     PP_IMAGES_TABLE, PP_LEADERBOARD_TABLE,
                                     TEAMS_TABLE)
from arcade.core.dao.images_dao import ImagesDao
from arcade.core.dao.leaderboard_dao import LeaderboardDao
from arcade.core.dao.state_dao import StateDao
from arcade.core.dao.teams_dao import TeamsDao
from arcade.services.pic_perfect.admin import PicPerfectAdminService
from arcade.types import ChallengeState


@pytest.mark.integration
class TestPicPerfectAdminServiceIntegration:
    """Integration tests for PicPerfectAdminService using moto."""

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
        """Create PicPerfectAdminService instance with real DAOs."""
        return PicPerfectAdminService(
            images_dao=images_dao,
            state_dao=state_dao,
            leaderboard_dao=leaderboard_dao,
            teams_dao=teams_dao,
        )

    def test_submit_hidden_image(self, service, state_dao, images_dao):
        """Test submitting a hidden image."""
        # Arrange
        image_url = "http://example.com/hidden.png"
        prompt = "hidden image prompt"

        # Act
        result = service.submit_hidden_image(image_url, prompt)

        # Assert
        assert result["success"] is True
        assert result["image_url"] == image_url

        # Verify hidden image was saved to DynamoDB
        response = images_dao.get_hidden_image()
        assert response is not None
        assert response["imageUrl"] == image_url
        assert response["prompt"] == prompt
        assert response["isHidden"] is True

        # Verify metadata was updated
        challenge_state = state_dao.get_challenge_state("pic-perfect")
        assert challenge_state["metadata"]["hiddenImageSet"] is True
        assert challenge_state["metadata"]["hiddenImageRevealed"] is False

    def test_calculate_scores(self, service, images_dao, leaderboard_dao, state_dao):
        """Test calculating scores."""
        # Arrange
        # Change challenge state to scoring
        state_dao.update_challenge_state(
            "pic-perfect",
            {
                "state": ChallengeState.SCORING.value,
            },
        )

        # Add hidden image
        images_dao.add_hidden_image("http://example.com/hidden.png", "hidden prompt")

        # Setup team submissions and votes
        images_dao.add_image("team1", "http://example.com/image1.png", "prompt1")
        images_dao.add_image("team2", "http://example.com/image2.png", "prompt2")
        images_dao.add_image("team3", "http://example.com/image3.png", "prompt3")

        # Set up votes
        images_dao.vote_on_image("team2", ["team1"])
        images_dao.vote_on_image("team3", ["team1"])
        images_dao.vote_on_image("team1", ["team2", "HIDDEN_IMAGE"])

        # Update leaderboard with votes given
        leaderboard_dao.update_score(
            "pic-perfect", "team1", {"votesGiven": ["team2", "HIDDEN_IMAGE"]}
        )
        leaderboard_dao.update_score("pic-perfect", "team2", {"votesGiven": ["team1"]})
        leaderboard_dao.update_score("pic-perfect", "team3", {"votesGiven": ["team1"]})

        votes_given = images_dao.get_votes_given_by_team("team1")
        print(votes_given)

        # Act
        results = service.calculate_scores()

        # Assert
        assert len(results) == 3

        # Check team scores
        team1_score = next(score for score in results if score["teamName"] == "team1")
        assert team1_score["deceptionPoints"] == 6
        assert team1_score["discoveryPoints"] == 10
        assert team1_score["totalPoints"] == 16
        assert team1_score["votesReceived"] == 2

        team2_score = next(score for score in results if score["teamName"] == "team2")
        assert team2_score["deceptionPoints"] == 3
        assert team2_score["discoveryPoints"] == 0
        assert team2_score["totalPoints"] == 3
        assert team2_score["votesReceived"] == 1

        team3_score = next(score for score in results if score["teamName"] == "team3")
        assert team3_score["deceptionPoints"] == 0
        assert team3_score["discoveryPoints"] == 0
        assert team3_score["totalPoints"] == 0
        assert team3_score["votesReceived"] == 0

        # Verify scores were updated in the database
        updated_team1 = leaderboard_dao.get_team_score("pic-perfect", "team1")
        assert updated_team1["deceptionPoints"] == 6
        assert updated_team1["totalPoints"] == 16

        updated_team2 = leaderboard_dao.get_team_score("pic-perfect", "team2")
        assert updated_team2["deceptionPoints"] == 3
        assert updated_team2["totalPoints"] == 3

    def test_finalize_challenge(self, service, state_dao, leaderboard_dao, images_dao):
        """Test finalizing the challenge."""
        # Arrange
        # Change challenge state to scoring
        state_dao.update_challenge_state(
            "pic-perfect",
            {
                "state": ChallengeState.SCORING.value,
                "metadata": {"hiddenImageSet": True, "hiddenImageRevealed": False},
            },
        )

        # Add hidden image
        images_dao.add_hidden_image("http://example.com/hidden.png", "hidden prompt")

        # Setup team submissions with votes
        images_dao.add_image("team1", "http://example.com/team1.png", "team1 prompt")
        images_dao.add_image("team2", "http://example.com/team2.png", "team2 prompt")
        images_dao.add_image("team3", "http://example.com/team3.png", "team3 prompt")

        # Setup votes (team1 gets 2 votes = 6 points, team2 gets 1 vote = 3 points)
        images_dao.vote_on_image("team2", ["team1"])
        images_dao.vote_on_image("team3", ["team1"])
        images_dao.vote_on_image("team1", ["team2"])

        # Act
        result = service.finalize_challenge()

        # Assert
        assert result["success"] is True

        # Verify challenge state updated
        challenge_state = state_dao.get_challenge_state("pic-perfect")
        assert challenge_state["state"] == ChallengeState.COMPLETE.value
        assert challenge_state["metadata"]["hiddenImageRevealed"] is True
        assert "endTime" in challenge_state

    def test_transition_challenge_state(self, service, state_dao):
        """Test transitioning challenge state."""
        # Arrange
        # Add all team submissions and hidden image to satisfy can_transition_to_voting
        with patch.object(service, "can_transition_to_voting", return_value=True):
            # Act
            result = service.transition_challenge_state(ChallengeState.VOTING)

            # Assert
            assert result["success"] is True
            assert result["previous_state"] == ChallengeState.SUBMISSION.value
            assert result["current_state"] == ChallengeState.VOTING.value

            # Verify state updated in database
            challenge_state = state_dao.get_challenge_state("pic-perfect")
            assert challenge_state["state"] == ChallengeState.VOTING.value

    def test_start_challenge(self, service, state_dao, images_dao):
        """Test starting a challenge."""
        # Arrange
        image_url = "http://example.com/hidden.png"
        prompt = "hidden image prompt"
        config = {"time_limit": 3600}

        # Act
        result = service.start_challenge(image_url, prompt, config)

        # Assert
        assert result["success"] is True
        assert result["challenge_state"] == ChallengeState.SUBMISSION.value

        # Verify hidden image was saved
        hidden_image = images_dao.get_hidden_image()
        assert hidden_image is not None
        assert hidden_image["imageUrl"] == image_url
        assert hidden_image["prompt"] == prompt
        assert hidden_image["isHidden"] is True

        # Verify challenge state is SUBMISSION
        challenge_state = state_dao.get_challenge_state("pic-perfect")
        assert challenge_state["state"] == ChallengeState.SUBMISSION.value
        assert challenge_state["metadata"]["hiddenImageSet"] is True

    def test_full_challenge_lifecycle(
        self, service, state_dao, images_dao, leaderboard_dao
    ):
        """Test the full challenge lifecycle from start to finish."""
        # 1. Start challenge
        service.start_challenge(
            image_url="http://example.com/hidden.png", prompt="hidden image prompt"
        )

        # Verify state
        challenge_state = state_dao.get_challenge_state("pic-perfect")
        assert challenge_state["state"] == ChallengeState.SUBMISSION.value

        # 2. Submit team images
        for team in ["team1", "team2", "team3"]:
            images_dao.add_image(
                team, f"http://example.com/{team}.png", f"{team} prompt"
            )

        # 3. Transition to voting phase (should pass now that all teams have submitted)
        with patch.object(service, "can_transition_to_voting", return_value=True):
            result = service.transition_challenge_state(ChallengeState.VOTING)
            assert result["success"] is True
            assert result["current_state"] == ChallengeState.VOTING.value

        # 4. Simulate voting
        # team1 votes for hidden image
        images_dao.vote_on_image("team1", ["team2", "team3", "HIDDEN_IMAGE"])
        leaderboard_dao.update_score(
            "pic-perfect", "team1", {"discoveryPoints": 10, "votedForHidden": True}
        )

        # team2 votes for team1
        images_dao.vote_on_image("team2", ["team1", "team3"])

        # team3 votes for team1
        images_dao.vote_on_image("team3", ["team1", "team2"])

        # 5. Transition to scoring phase
        with patch.object(service, "can_transition_to_scoring", return_value=True):
            result = service.transition_challenge_state(ChallengeState.SCORING)
            assert result["success"] is True
            assert result["current_state"] == ChallengeState.SCORING.value

        # 6. Calculate scores
        scores = service.calculate_scores()

        # Verify team1 got 6 deception points (2 votes) + 10 discovery points
        team1_score = next(score for score in scores if score["teamName"] == "team1")
        assert team1_score["deceptionPoints"] == 6
        assert team1_score["discoveryPoints"] == 10
        assert team1_score["totalPoints"] == 16

        # 7. Finalize challenge
        result = service.finalize_challenge()
        assert result["success"] is True

        # Verify challenge is complete
        challenge_state = state_dao.get_challenge_state("pic-perfect")
        assert challenge_state["state"] == ChallengeState.COMPLETE.value
        assert challenge_state["metadata"]["hiddenImageRevealed"] is True
        assert "endTime" in challenge_state
