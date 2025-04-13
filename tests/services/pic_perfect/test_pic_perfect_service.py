from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from arcade.services.pic_perfect.main import PicPerfectService
from arcade.types import ChallengeState


@pytest.mark.unit
class TestPicPerfectServiceUnit:
    """Unit tests for PicPerfectService class."""

    @pytest.fixture
    def mock_images_dao(self):
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_state_dao(self):
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_leaderboard_dao(self):
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_teams_dao(self):
        mock = MagicMock()
        return mock

    @pytest.fixture
    def service(
        self, mock_images_dao, mock_state_dao, mock_leaderboard_dao, mock_teams_dao
    ):
        return PicPerfectService(
            images_dao=mock_images_dao,
            state_dao=mock_state_dao,
            leaderboard_dao=mock_leaderboard_dao,
            teams_dao=mock_teams_dao,
        )

    def test_submit_team_image_success(
        self, service, mock_images_dao, mock_state_dao, mock_leaderboard_dao
    ):
        # Arrange
        team_name = "team1"
        image_url = "http://example.com/image.png"
        prompt = "test prompt"

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.SUBMISSION.value
        }
        mock_images_dao.add_image.return_value = {"timestamp": "2023-01-01T12:00:00"}

        # Act
        result = service.submit_team_image(team_name, image_url, prompt)

        # Assert
        assert result["success"] is True
        assert result["timestamp"] == "2023-01-01T12:00:00"
        assert result["team_name"] == team_name
        assert result["image_url"] == image_url

        mock_state_dao.get_challenge_state.assert_called_once_with("pic-perfect")
        mock_images_dao.add_image.assert_called_once_with(team_name, image_url, prompt)
        mock_leaderboard_dao.update_score.assert_called_once()

    def test_submit_team_image_challenge_not_initialized(self, service, mock_state_dao):
        # Arrange
        team_name = "team1"
        image_url = "http://example.com/image.png"
        prompt = "test prompt"

        mock_state_dao.get_challenge_state.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"Challenge pic-perfect not initialized"):
            service.submit_team_image(team_name, image_url, prompt)

    def test_submit_team_image_wrong_state(self, service, mock_state_dao):
        # Arrange
        team_name = "team1"
        image_url = "http://example.com/image.png"
        prompt = "test prompt"

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.VOTING.value
        }

        # Act & Assert
        with pytest.raises(ValueError, match=f"Challenge is not in submission state"):
            service.submit_team_image(team_name, image_url, prompt)

    def test_cast_votes_success(
        self, service, mock_images_dao, mock_state_dao, mock_leaderboard_dao
    ):
        # Arrange
        team_name = "team1"
        voted_teams = ["team2", "team3"]

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.VOTING.value
        }
        mock_images_dao.get_team_image.return_value = {
            "teamName": team_name,
            "imageUrl": "http://example.com/image.png",
        }
        mock_images_dao.vote_on_image.return_value = {"voted_teams": voted_teams}
        mock_images_dao.get_votes_remaining.return_value = 1
        mock_images_dao.get_hidden_image.return_value = None

        # Act
        result = service.cast_votes(team_name, voted_teams)

        # Assert
        assert result["success"] is True
        assert result["voted_teams"] == voted_teams
        assert result["remaining_votes"] == 1

        mock_state_dao.get_challenge_state.assert_called_once_with("pic-perfect")
        mock_images_dao.get_team_image.assert_called_once_with(team_name)
        mock_images_dao.vote_on_image.assert_called_once_with(team_name, voted_teams)
        mock_images_dao.get_votes_remaining.assert_called_once_with(team_name)
        mock_images_dao.get_hidden_image.assert_called_once()

    def test_cast_votes_for_hidden_image(
        self, service, mock_images_dao, mock_state_dao, mock_leaderboard_dao
    ):
        # Arrange
        team_name = "team1"
        voted_teams = ["team2", "HIDDEN_IMAGE"]

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.VOTING.value
        }
        mock_images_dao.get_team_image.return_value = {
            "teamName": team_name,
            "imageUrl": "http://example.com/image.png",
        }
        mock_images_dao.vote_on_image.return_value = {"voted_teams": voted_teams}
        mock_images_dao.get_votes_remaining.return_value = 1
        mock_images_dao.get_hidden_image.return_value = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "http://example.com/hidden.png",
        }

        # Act
        result = service.cast_votes(team_name, voted_teams)

        # Assert
        assert result["success"] is True

        # Check discovery points awarded for voting for hidden image
        mock_leaderboard_dao.update_score.assert_called_once_with(
            "pic-perfect", team_name, {"discoveryPoints": 10, "votedForHidden": True}
        )

    def test_cast_votes_challenge_not_in_voting_state(self, service, mock_state_dao):
        # Arrange
        team_name = "team1"
        voted_teams = ["team2", "team3"]

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.SUBMISSION.value
        }

        # Act & Assert
        with pytest.raises(ValueError, match=f"Challenge is not in voting state"):
            service.cast_votes(team_name, voted_teams)

    def test_cast_votes_team_no_submission(
        self, service, mock_state_dao, mock_images_dao
    ):
        # Arrange
        team_name = "team1"
        voted_teams = ["team2", "team3"]

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.VOTING.value
        }
        mock_images_dao.get_team_image.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError,
            match=f"Team {team_name} has not submitted an image and cannot vote",
        ):
            service.cast_votes(team_name, voted_teams)

    def test_get_voting_pool(self, service, mock_state_dao, mock_images_dao):
        # Arrange
        requesting_team = "team1"
        images = [
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
            {"teamName": "team3", "imageUrl": "http://example.com/image3.png"},
        ]
        hidden_image = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "http://example.com/hidden.png",
        }

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.VOTING.value
        }
        mock_images_dao.get_all_images.return_value = images
        mock_images_dao.get_hidden_image.return_value = hidden_image

        # Act
        result = service.get_voting_pool(requesting_team)

        # Assert
        assert len(result) == 3
        assert hidden_image in result
        mock_images_dao.get_all_images.assert_called_once_with(
            exclude_teams=requesting_team
        )
        mock_images_dao.get_hidden_image.assert_called_once()

    def test_get_team_status(self, service, mock_images_dao, mock_leaderboard_dao):
        # Arrange
        team_name = "team1"
        team_image = {"teamName": team_name, "imageUrl": "http://example.com/image.png"}
        votes_given = ["team2", "team3"]
        votes_remaining = 1
        team_score = {"totalPoints": 10, "deceptionPoints": 0, "discoveryPoints": 10}

        mock_images_dao.get_team_image.return_value = team_image
        mock_images_dao.get_votes_given_by_team.return_value = votes_given
        mock_images_dao.get_votes_remaining.return_value = votes_remaining
        mock_leaderboard_dao.get_team_score.return_value = team_score

        # Act
        result = service.get_team_status(team_name)

        # Assert
        assert result["has_submitted"] is True
        assert result["image_details"] == team_image
        assert result["votes_given"] == votes_given
        assert result["votes_remaining"] == votes_remaining
        assert result["score"] == team_score

    def test_get_leaderboard(
        self, service, mock_leaderboard_dao, mock_state_dao, mock_images_dao
    ):
        # Arrange
        leaderboard = [
            {
                "teamName": "team1",
                "totalPoints": 13,
                "deceptionPoints": 3,
                "discoveryPoints": 10,
            },
            {
                "teamName": "team2",
                "totalPoints": 6,
                "deceptionPoints": 6,
                "discoveryPoints": 0,
            },
        ]
        challenge_state = {"state": ChallengeState.COMPLETE.value}
        hidden_image = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "http://example.com/hidden.png",
        }

        mock_leaderboard_dao.get_leaderboard.return_value = leaderboard
        mock_state_dao.get_challenge_state.return_value = challenge_state
        mock_images_dao.get_hidden_image.return_value = hidden_image

        # Act
        result = service.get_leaderboard()

        # Assert
        assert result["leaderboard"] == leaderboard
        assert result["hidden_image"] == hidden_image
        assert result["challenge_state"] == ChallengeState.COMPLETE.value

    def test_get_leaderboard_challenge_not_complete(
        self, service, mock_leaderboard_dao, mock_state_dao
    ):
        # Arrange
        leaderboard = [
            {
                "teamName": "team1",
                "totalPoints": 13,
                "deceptionPoints": 3,
                "discoveryPoints": 10,
            },
            {
                "teamName": "team2",
                "totalPoints": 6,
                "deceptionPoints": 6,
                "discoveryPoints": 0,
            },
        ]
        challenge_state = {"state": ChallengeState.VOTING.value}

        mock_leaderboard_dao.get_leaderboard.return_value = leaderboard
        mock_state_dao.get_challenge_state.return_value = challenge_state

        # Act
        result = service.get_leaderboard()

        # Assert
        assert result["leaderboard"] == leaderboard
        assert (
            result["hidden_image"] is None
        )  # Hidden image not revealed until complete
        assert result["challenge_state"] == ChallengeState.VOTING.value

    def test_get_submission_status(self, service, mock_teams_dao, mock_images_dao):
        # Arrange
        all_teams = [
            {"teamName": "team1"},
            {"teamName": "team2"},
            {"teamName": "team3"},
        ]
        submitted_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]

        mock_teams_dao.get_all_teams.return_value = all_teams
        mock_images_dao.get_all_images.return_value = submitted_images

        # Act
        result = service.get_submission_status()

        # Assert
        assert result["teams_submitted"] == 2
        assert result["total_teams"] == 3
        assert result["pending_teams"] == ["team3"]
        assert result["can_transition_to_voting"] is False

    def test_get_submission_status_all_submitted(
        self, service, mock_teams_dao, mock_images_dao
    ):
        # Arrange
        all_teams = [
            {"teamName": "team1"},
            {"teamName": "team2"},
        ]
        submitted_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]

        mock_teams_dao.get_all_teams.return_value = all_teams
        mock_images_dao.get_all_images.return_value = submitted_images

        # Act
        result = service.get_submission_status()

        # Assert
        assert result["teams_submitted"] == 2
        assert result["total_teams"] == 2
        assert result["pending_teams"] == []
        assert result["can_transition_to_voting"] is True

    def test_get_voting_status(self, service, mock_images_dao):
        # Arrange
        team_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
            {"teamName": "team3", "imageUrl": "http://example.com/image3.png"},
        ]

        # Only team1 has used all their votes
        mock_images_dao.get_all_images.return_value = team_images
        mock_images_dao.get_votes_remaining.side_effect = [
            0,
            2,
            1,
        ]  # team1, team2, team3

        # Act
        result = service.get_voting_status()

        # Assert
        assert result["teams_completed_voting"] == 1
        assert result["total_teams"] == 3
        assert "team2" in result["pending_teams"]
        assert "team3" in result["pending_teams"]
        assert result["can_transition_to_scoring"] is False

    def test_get_voting_status_all_voted(self, service, mock_images_dao):
        # Arrange
        team_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]

        # All teams have used all their votes
        mock_images_dao.get_all_images.return_value = team_images
        mock_images_dao.get_votes_remaining.side_effect = [0, 0]  # team1, team2

        # Act
        result = service.get_voting_status()

        # Assert
        assert result["teams_completed_voting"] == 2
        assert result["total_teams"] == 2
        assert result["pending_teams"] == []
        assert result["can_transition_to_scoring"] is True

    def test_can_transition_to_voting(self, service):
        # Arrange
        with patch.object(
            service, "get_submission_status"
        ) as mock_get_submission_status:
            mock_get_submission_status.return_value = {"can_transition_to_voting": True}

            # Act
            result = service.can_transition_to_voting()

            # Assert
            assert result is True
            mock_get_submission_status.assert_called_once()

    def test_can_transition_to_scoring(self, service):
        # Arrange
        with patch.object(service, "get_voting_status") as mock_get_voting_status:
            mock_get_voting_status.return_value = {"can_transition_to_scoring": True}

            # Act
            result = service.can_transition_to_scoring()

            # Assert
            assert result is True
            mock_get_voting_status.assert_called_once()
