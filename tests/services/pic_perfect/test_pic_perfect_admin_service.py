from datetime import datetime
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest

from arcade.services.pic_perfect.admin import PicPerfectAdminService
from arcade.types import ChallengeState


@pytest.mark.unit
class TestPicPerfectAdminServiceUnit:
    """Unit tests for PicPerfectAdminService class."""

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
        return PicPerfectAdminService(
            images_dao=mock_images_dao,
            state_dao=mock_state_dao,
            leaderboard_dao=mock_leaderboard_dao,
            teams_dao=mock_teams_dao,
        )

    def test_submit_hidden_image_success(
        self, service, mock_images_dao, mock_state_dao
    ):
        # Arrange
        image_url = "http://example.com/hidden.png"
        prompt = "hidden image prompt"

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.SUBMISSION.value,
            "metadata": {},
        }
        mock_images_dao.get_hidden_image.return_value = None
        mock_images_dao.add_hidden_image.return_value = {
            "timestamp": "2023-01-01T12:00:00"
        }

        # Act
        result = service.submit_hidden_image(image_url, prompt)

        # Assert
        assert result["success"] is True
        assert result["timestamp"] == "2023-01-01T12:00:00"
        assert result["image_url"] == image_url

        mock_state_dao.get_challenge_state.assert_called_once_with("pic-perfect")
        mock_images_dao.get_hidden_image.assert_called_once()
        mock_images_dao.add_hidden_image.assert_called_once_with(image_url, prompt)
        mock_state_dao.update_challenge_state.assert_called_once()

        # Check metadata updated
        metadata_arg = mock_state_dao.update_challenge_state.call_args[0][1]["metadata"]
        assert metadata_arg["hiddenImageSet"] is True
        assert metadata_arg["hiddenImageRevealed"] is False

    def test_submit_hidden_image_challenge_not_initialized(
        self, service, mock_state_dao
    ):
        # Arrange
        image_url = "http://example.com/hidden.png"
        prompt = "hidden image prompt"

        mock_state_dao.get_challenge_state.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"Challenge pic-perfect not initialized"):
            service.submit_hidden_image(image_url, prompt)

    def test_submit_hidden_image_already_exists(
        self, service, mock_state_dao, mock_images_dao
    ):
        # Arrange
        image_url = "http://example.com/hidden.png"
        prompt = "hidden image prompt"

        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.SUBMISSION.value
        }
        mock_images_dao.get_hidden_image.return_value = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "existing-url",
        }

        # Act & Assert
        with pytest.raises(
            ValueError, match="Hidden image already exists and cannot be replaced"
        ):
            service.submit_hidden_image(image_url, prompt)

    def test_calculate_scores_success(
        self, service, mock_images_dao, mock_state_dao, mock_leaderboard_dao
    ):
        # Arrange
        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.SCORING.value
        }

        team_images = [
            {
                "teamName": "team1",
                "imageUrl": "http://example.com/image1.png",
                "votes": {"team2", "team3"},  # 2 votes = 6 points
            },
            {
                "teamName": "team2",
                "imageUrl": "http://example.com/image2.png",
                "votes": {"team1"},  # 1 vote = 3 points
            },
        ]

        # team1 has 10 discovery points for identifying hidden image
        mock_leaderboard_dao.get_team_score.side_effect = [
            {"discoveryPoints": 10, "deceptionPoints": 0},  # team1
            {"discoveryPoints": 0, "deceptionPoints": 0},  # team2
        ]

        mock_images_dao.get_all_images.return_value = team_images
        mock_images_dao.get_hidden_image.return_value = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "http://example.com/hidden.png",
        }

        # Act
        result = service.calculate_scores()

        # Assert
        assert len(result) == 2

        # Verify team1 (6 deception + 10 discovery = 16 total)
        team1_result = [team for team in result if team["teamName"] == "team1"][0]
        assert team1_result["deceptionPoints"] == 6
        assert team1_result["discoveryPoints"] == 10
        assert team1_result["totalPoints"] == 16
        assert team1_result["votesReceived"] == 2

        # Verify team2 (3 deception + 0 discovery = 3 total)
        team2_result = [team for team in result if team["teamName"] == "team2"][0]
        assert team2_result["deceptionPoints"] == 3
        assert team2_result["discoveryPoints"] == 0
        assert team2_result["totalPoints"] == 3
        assert team2_result["votesReceived"] == 1

        # Verify scores sorted by totalPoints (descending)
        assert result[0]["teamName"] == "team1"
        assert result[1]["teamName"] == "team2"

        # Verify leaderboard updates
        assert mock_leaderboard_dao.update_score.call_count == 2

    def test_calculate_scores_challenge_not_in_scoring_state(
        self, service, mock_state_dao
    ):
        # Arrange
        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.VOTING.value
        }

        # Act & Assert
        with pytest.raises(ValueError, match=f"Challenge is not in scoring state"):
            service.calculate_scores()

    def test_finalize_challenge_success(self, service, mock_state_dao):
        # Arrange
        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.SCORING.value,
            "metadata": {},
        }

        # Mock calculate_scores to return some dummy scores
        with patch.object(service, "calculate_scores") as mock_calculate_scores:
            team_scores = [
                {"teamName": "team1", "totalPoints": 16},
                {"teamName": "team2", "totalPoints": 3},
            ]
            mock_calculate_scores.return_value = team_scores

            # Act
            result = service.finalize_challenge()

            # Assert
            assert result["success"] is True
            assert result["teams_scored"] == 2
            assert result["final_leaderboard"] == team_scores

            # Check challenge state updates
            mock_state_dao.update_challenge_state.assert_called_once()
            state_update = mock_state_dao.update_challenge_state.call_args[0][1]
            assert state_update["state"] == ChallengeState.COMPLETE.value
            assert state_update["metadata"]["hiddenImageRevealed"] is True
            assert "endTime" in state_update

    def test_transition_challenge_state_success(self, service, mock_state_dao):
        # Arrange
        current_state = ChallengeState.SUBMISSION
        target_state = ChallengeState.VOTING

        mock_state_dao.get_challenge_state.return_value = {"state": current_state.value}

        # Mock _is_valid_transition to return True
        with patch.object(service, "_is_valid_transition", return_value=True):
            # Act
            result = service.transition_challenge_state(target_state)

            # Assert
            assert result["success"] is True
            assert result["previous_state"] == current_state.value
            assert result["current_state"] == target_state.value

            mock_state_dao.update_challenge_state.assert_called_once_with(
                "pic-perfect", {"state": target_state.value}
            )

    def test_transition_challenge_state_invalid_transition(
        self, service, mock_state_dao
    ):
        # Arrange
        current_state = ChallengeState.SUBMISSION
        target_state = ChallengeState.COMPLETE  # Invalid direct transition

        mock_state_dao.get_challenge_state.return_value = {"state": current_state.value}

        # Mock _is_valid_transition to return False
        with patch.object(service, "_is_valid_transition", return_value=False):
            # Act
            result = service.transition_challenge_state(target_state)

            # Assert
            assert result["success"] is False
            assert "Invalid state transition" in result["message"]

            # State should not have been updated
            mock_state_dao.update_challenge_state.assert_not_called()

    def test_is_valid_transition(self, service):
        # Test all valid transitions

        # From LOCKED
        assert (
            service._is_valid_transition(
                ChallengeState.LOCKED, ChallengeState.SUBMISSION
            )
            is True
        )
        assert (
            service._is_valid_transition(ChallengeState.LOCKED, ChallengeState.VOTING)
            is False
        )

        # From SUBMISSION
        with patch.object(service, "can_transition_to_voting", return_value=True):
            assert (
                service._is_valid_transition(
                    ChallengeState.SUBMISSION, ChallengeState.VOTING
                )
                is True
            )

        with patch.object(service, "can_transition_to_voting", return_value=False):
            assert (
                service._is_valid_transition(
                    ChallengeState.SUBMISSION, ChallengeState.VOTING
                )
                is False
            )

        assert (
            service._is_valid_transition(
                ChallengeState.SUBMISSION, ChallengeState.LOCKED
            )
            is True
        )
        assert (
            service._is_valid_transition(
                ChallengeState.SUBMISSION, ChallengeState.COMPLETE
            )
            is False
        )

        # From VOTING
        with patch.object(service, "can_transition_to_scoring", return_value=True):
            assert (
                service._is_valid_transition(
                    ChallengeState.VOTING, ChallengeState.SCORING
                )
                is True
            )

        with patch.object(service, "can_transition_to_scoring", return_value=False):
            assert (
                service._is_valid_transition(
                    ChallengeState.VOTING, ChallengeState.SCORING
                )
                is False
            )

        assert (
            service._is_valid_transition(ChallengeState.VOTING, ChallengeState.LOCKED)
            is True
        )
        assert (
            service._is_valid_transition(ChallengeState.VOTING, ChallengeState.COMPLETE)
            is False
        )

        # From SCORING
        assert (
            service._is_valid_transition(
                ChallengeState.SCORING, ChallengeState.COMPLETE
            )
            is True
        )
        assert (
            service._is_valid_transition(ChallengeState.SCORING, ChallengeState.LOCKED)
            is True
        )
        assert (
            service._is_valid_transition(ChallengeState.SCORING, ChallengeState.VOTING)
            is False
        )

        # From COMPLETE
        assert (
            service._is_valid_transition(ChallengeState.COMPLETE, ChallengeState.LOCKED)
            is True
        )
        assert (
            service._is_valid_transition(
                ChallengeState.COMPLETE, ChallengeState.SUBMISSION
            )
            is False
        )

    def test_can_transition_to_voting(self, service, mock_teams_dao, mock_images_dao):
        # Arrange
        all_teams = [
            {"teamName": "team1"},
            {"teamName": "team2"},
        ]
        all_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]
        hidden_image = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "http://example.com/hidden.png",
        }

        mock_teams_dao.get_all_teams.return_value = all_teams
        mock_images_dao.get_all_images.return_value = all_images
        mock_images_dao.get_hidden_image.return_value = hidden_image

        # Act
        result = service.can_transition_to_voting()

        # Assert
        assert result is True
        mock_teams_dao.get_all_teams.assert_called_once()
        mock_images_dao.get_all_images.assert_called_once()
        mock_images_dao.get_hidden_image.assert_called_once()

    def test_can_transition_to_voting_missing_submissions(
        self, service, mock_teams_dao, mock_images_dao
    ):
        # Arrange
        all_teams = [
            {"teamName": "team1"},
            {"teamName": "team2"},
            {"teamName": "team3"},
        ]
        all_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]
        hidden_image = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "http://example.com/hidden.png",
        }

        mock_teams_dao.get_all_teams.return_value = all_teams
        mock_images_dao.get_all_images.return_value = all_images
        mock_images_dao.get_hidden_image.return_value = hidden_image

        # Act
        result = service.can_transition_to_voting()

        # Assert
        assert result is False  # team3 has not submitted

    def test_can_transition_to_voting_no_hidden_image(
        self, service, mock_teams_dao, mock_images_dao
    ):
        # Arrange
        all_teams = [
            {"teamName": "team1"},
            {"teamName": "team2"},
        ]
        all_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]

        mock_teams_dao.get_all_teams.return_value = all_teams
        mock_images_dao.get_all_images.return_value = all_images
        mock_images_dao.get_hidden_image.return_value = None

        # Act
        result = service.can_transition_to_voting()

        # Assert
        assert result is False  # no hidden image

    def test_can_transition_to_scoring(self, service, mock_images_dao):
        # Arrange
        all_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]

        mock_images_dao.get_all_images.return_value = all_images
        # All teams have 0 votes remaining
        mock_images_dao.get_votes_remaining.return_value = 0

        # Act
        result = service.can_transition_to_scoring()

        # Assert
        assert result is True
        mock_images_dao.get_all_images.assert_called_once()
        assert mock_images_dao.get_votes_remaining.call_count == 2

    def test_can_transition_to_scoring_votes_remaining(self, service, mock_images_dao):
        # Arrange
        all_images = [
            {"teamName": "team1", "imageUrl": "http://example.com/image1.png"},
            {"teamName": "team2", "imageUrl": "http://example.com/image2.png"},
        ]

        mock_images_dao.get_all_images.return_value = all_images
        # team1 has 0 votes remaining, team2 has 1 vote remaining
        mock_images_dao.get_votes_remaining.side_effect = [0, 1]

        # Act
        result = service.can_transition_to_scoring()

        # Assert
        assert result is False  # team2 still has votes remaining

    def test_start_challenge_success(
        self, service, mock_state_dao, mock_leaderboard_dao
    ):
        # Arrange
        image_url = "http://example.com/hidden.png"
        prompt = "hidden image prompt"
        config = {"time_limit": 3600}

        # Challenge not initialized yet
        mock_state_dao.get_challenge_state.return_value = None

        # Mock the submission method since it's tested elsewhere
        with patch.object(service, "submit_hidden_image") as mock_submit_hidden_image:
            mock_submit_hidden_image.return_value = {"success": True}

            # Act
            result = service.start_challenge(image_url, prompt, config)

            # Assert
            assert result["success"] is True
            assert result["challenge_state"] == ChallengeState.SUBMISSION.value

            mock_state_dao.initialize_challenge.assert_called_once_with(
                "pic-perfect", config
            )
            mock_leaderboard_dao.reset_leaderboard.assert_called_once_with(
                "pic-perfect"
            )
            mock_state_dao.update_challenge_state.assert_called_once_with(
                "pic-perfect", {"state": ChallengeState.SUBMISSION.value}
            )
            mock_submit_hidden_image.assert_called_once_with(image_url, prompt)

    def test_start_challenge_already_initialized(
        self, service, mock_state_dao, mock_leaderboard_dao
    ):
        # Arrange
        image_url = "http://example.com/hidden.png"
        prompt = "hidden image prompt"

        # Challenge already initialized
        mock_state_dao.get_challenge_state.return_value = {
            "state": ChallengeState.LOCKED.value
        }

        # Mock the submission method since it's tested elsewhere
        with patch.object(service, "submit_hidden_image") as mock_submit_hidden_image:
            mock_submit_hidden_image.return_value = {"success": True}

            # Act
            result = service.start_challenge(image_url, prompt)

            # Assert
            assert result["success"] is True

            # Should not initialize again or reset leaderboard
            mock_state_dao.initialize_challenge.assert_not_called()
            mock_leaderboard_dao.reset_leaderboard.assert_not_called()

            # Should still update state and submit hidden image
            mock_state_dao.update_challenge_state.assert_called_once_with(
                "pic-perfect", {"state": ChallengeState.SUBMISSION.value}
            )
            mock_submit_hidden_image.assert_called_once_with(image_url, prompt)
