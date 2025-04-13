import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz

from arcade.config.constants import MAX_VOTES_PER_TEAM
from arcade.core.dao.images_dao import ImagesDao


@pytest.mark.unit
class TestImagesDaoUnit:
    """Unit tests for ImagesDao class."""

    @pytest.fixture
    def mock_dynamodb_dao(self):
        """Create a mock ImagesDao with mocked DynamoDB methods."""
        with patch("arcade.core.dao.images_dao.DynamoDBDao") as mock_ddb:
            images_dao = ImagesDao()
            # Mock the methods inherited from DynamoDBDao
            images_dao.get_item = MagicMock()
            images_dao.put_item = MagicMock(return_value=True)
            images_dao.update_item = MagicMock(return_value=True)
            images_dao.delete_item = MagicMock(return_value=True)
            images_dao.scan = MagicMock()
            yield images_dao

    def test_add_image_success(self, mock_dynamodb_dao):
        """Test successful image addition."""
        # Arrange
        mock_dynamodb_dao.get_item.return_value = None  # Team doesn't have an image yet
        team_name = "test_team"
        image_url = "https://example.com/image.jpg"
        prompt = "test prompt"

        # Act
        with patch("arcade.core.dao.images_dao.datetime") as mock_datetime:
            # Configure the mock to return a fixed timestamp
            mock_now = MagicMock()
            fixed_timestamp = "2023-01-01T12:00:00+05:30"
            mock_now.return_value.isoformat.return_value = fixed_timestamp
            mock_datetime.now = mock_now

            result = mock_dynamodb_dao.add_image(team_name, image_url, prompt)

        # Assert
        assert result["success"] is True
        assert result["timestamp"] == fixed_timestamp
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": team_name})
        mock_dynamodb_dao.put_item.assert_called_once()
        # Verify the item structure
        call_args = mock_dynamodb_dao.put_item.call_args[0][0]
        assert call_args["teamName"] == team_name
        assert call_args["imageUrl"] == image_url
        assert call_args["prompt"] == prompt
        assert call_args["timestamp"] == fixed_timestamp
        assert call_args["isHidden"] is False
        assert call_args["votes"] == set(["PLACEHOLDER"])
        assert call_args["votesGiven"] == set(["PLACEHOLDER"])

    def test_add_image_team_already_submitted(self, mock_dynamodb_dao):
        """Test adding image when team already submitted."""
        # Arrange
        mock_dynamodb_dao.get_item.return_value = {
            "teamName": "existing_team",
            "imageUrl": "https://example.com/existing.jpg",
        }
        team_name = "existing_team"
        image_url = "https://example.com/new.jpg"
        prompt = "test prompt"

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            mock_dynamodb_dao.add_image(team_name, image_url, prompt)
        assert f"Team '{team_name}' has already submitted an image" in str(
            excinfo.value
        )
        mock_dynamodb_dao.put_item.assert_not_called()

    def test_add_hidden_image(self, mock_dynamodb_dao):
        """Test adding a hidden image."""
        # Arrange
        image_url = "https://example.com/hidden.jpg"
        prompt = "hidden image prompt"

        # Act
        with patch("arcade.core.dao.images_dao.datetime") as mock_datetime:
            # Configure the mock to return a fixed timestamp
            mock_now = MagicMock()
            fixed_timestamp = "2023-01-01T12:00:00+05:30"
            mock_now.return_value.isoformat.return_value = fixed_timestamp
            mock_datetime.now = mock_now

            result = mock_dynamodb_dao.add_hidden_image(image_url, prompt)

        # Assert
        assert result["success"] is True
        mock_dynamodb_dao.put_item.assert_called_once()
        # Verify the item structure
        call_args = mock_dynamodb_dao.put_item.call_args[0][0]
        assert call_args["teamName"] == "HIDDEN_IMAGE"
        assert call_args["imageUrl"] == image_url
        assert call_args["prompt"] == prompt
        assert call_args["timestamp"] == fixed_timestamp
        assert call_args["isHidden"] is True
        assert call_args["votes"] == set(["PLACEHOLDER"])
        assert call_args["votesGiven"] == set(["PLACEHOLDER"])

    def test_vote_on_image_success_single_vote(self, mock_dynamodb_dao):
        """Test successful voting on a single team's image."""
        # Arrange
        voting_team = "team1"
        target_team = "team2"

        # Mock existing data
        voting_team_data = {
            "teamName": voting_team,
            "votesGiven": set(["PLACEHOLDER"]),
        }
        target_team_data = {
            "teamName": target_team,
            "votes": set(["PLACEHOLDER"]),
        }

        # Set up the mock get_item to return appropriate data
        def mock_get_item_side_effect(key):
            if key["teamName"] == voting_team:
                return voting_team_data
            elif key["teamName"] == target_team:
                return target_team_data
            return None

        mock_dynamodb_dao.get_item.side_effect = mock_get_item_side_effect

        # Act
        result = mock_dynamodb_dao.vote_on_image(voting_team, target_team)

        # Assert
        assert result["success"] is True
        assert target_team in result["voted_for"]
        assert result["votesRemaining"] == MAX_VOTES_PER_TEAM - 1
        # Check that update_item was called to update votes
        update_calls = mock_dynamodb_dao.update_item.call_args_list
        assert len(update_calls) == 2  # Once for target team, once for voting team

    def test_vote_on_image_success_multiple_votes(self, mock_dynamodb_dao):
        """Test successful voting on multiple teams' images."""
        # Arrange
        voting_team = "team1"
        target_teams = ["team2", "team3"]

        # Mock existing data
        voting_team_data = {
            "teamName": voting_team,
            "votesGiven": set(["PLACEHOLDER"]),
        }
        team2_data = {
            "teamName": "team2",
            "votes": set(["PLACEHOLDER"]),
        }
        team3_data = {
            "teamName": "team3",
            "votes": set(["PLACEHOLDER"]),
        }

        # Set up the mock get_item to return appropriate data
        def mock_get_item_side_effect(key):
            if key["teamName"] == voting_team:
                return voting_team_data
            elif key["teamName"] == "team2":
                return team2_data
            elif key["teamName"] == "team3":
                return team3_data
            return None

        mock_dynamodb_dao.get_item.side_effect = mock_get_item_side_effect

        # Act
        result = mock_dynamodb_dao.vote_on_image(voting_team, target_teams)

        # Assert
        assert result["success"] is True
        assert set(target_teams) == set(result["voted_for"])
        assert result["votesRemaining"] == MAX_VOTES_PER_TEAM - 2
        # Check that update_item was called to update votes
        update_calls = mock_dynamodb_dao.update_item.call_args_list
        assert len(update_calls) == 3  # Once for each target team, once for voting team

    def test_vote_on_image_team_not_registered(self, mock_dynamodb_dao):
        """Test voting when voting team is not registered."""
        # Arrange
        voting_team = "nonexistent_team"
        target_team = "team2"

        # Mock get_item to return None for the voting team
        mock_dynamodb_dao.get_item.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            mock_dynamodb_dao.vote_on_image(voting_team, target_team)
        assert f"Voting team '{voting_team}' is not registered" in str(excinfo.value)

    def test_vote_on_image_target_not_found(self, mock_dynamodb_dao):
        """Test voting when target team has no submission."""
        # Arrange
        voting_team = "team1"
        target_team = "nonexistent_team"

        # Mock existing data for voting team but not for target
        voting_team_data = {
            "teamName": voting_team,
            "votesGiven": set(["PLACEHOLDER"]),
        }

        # Set up the mock get_item to return appropriate data
        def mock_get_item_side_effect(key):
            if key["teamName"] == voting_team:
                return voting_team_data
            return None

        mock_dynamodb_dao.get_item.side_effect = mock_get_item_side_effect

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            mock_dynamodb_dao.vote_on_image(voting_team, target_team)
        assert f"Target team '{target_team}' has no image submission" in str(
            excinfo.value
        )

    def test_vote_on_image_self_vote(self, mock_dynamodb_dao):
        """Test voting for own team's image."""
        # Arrange
        team_name = "team1"

        # Mock team data
        team_data = {
            "teamName": team_name,
            "votesGiven": set(["PLACEHOLDER"]),
        }

        mock_dynamodb_dao.get_item.return_value = team_data

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            mock_dynamodb_dao.vote_on_image(team_name, team_name)
        assert "Teams cannot vote for their own image" in str(excinfo.value)

    def test_vote_on_image_exceeded_limit(self, mock_dynamodb_dao):
        """Test voting when team has already used all votes."""
        # Arrange
        voting_team = "team1"
        target_team = "team5"  # A team not yet voted for

        # Mock existing data with MAX_VOTES_PER_TEAM votes already given
        existing_votes = set(
            ["team" + str(i) for i in range(2, 2 + MAX_VOTES_PER_TEAM)]
        )
        voting_team_data = {
            "teamName": voting_team,
            "votesGiven": existing_votes,
        }

        mock_dynamodb_dao.get_item.return_value = voting_team_data

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            mock_dynamodb_dao.vote_on_image(voting_team, target_team)
        assert f"Cannot vote for 1 teams. You have 0 vote(s) remaining." in str(
            excinfo.value
        )

    def test_get_all_images(self, mock_dynamodb_dao):
        """Test getting all images."""
        # Arrange
        expected_images = [
            {"teamName": "team1", "imageUrl": "https://example.com/image1.jpg"},
            {"teamName": "team2", "imageUrl": "https://example.com/image2.jpg"},
            {"teamName": "team3", "imageUrl": "https://example.com/image3.jpg"},
        ]
        mock_dynamodb_dao.scan.return_value = expected_images

        # Act
        result = mock_dynamodb_dao.get_all_images()

        # Assert
        assert result == expected_images
        mock_dynamodb_dao.scan.assert_called_once_with(limit=100)

    def test_get_all_images_with_exclude(self, mock_dynamodb_dao):
        """Test getting all images with exclusion."""
        # Arrange
        all_images = [
            {"teamName": "team1", "imageUrl": "https://example.com/image1.jpg"},
            {"teamName": "team2", "imageUrl": "https://example.com/image2.jpg"},
            {"teamName": "team3", "imageUrl": "https://example.com/image3.jpg"},
        ]
        mock_dynamodb_dao.scan.return_value = all_images
        exclude_team = "team2"

        # Act
        result = mock_dynamodb_dao.get_all_images(exclude_teams=exclude_team)

        # Assert
        expected_result = [
            {"teamName": "team1", "imageUrl": "https://example.com/image1.jpg"},
            {"teamName": "team3", "imageUrl": "https://example.com/image3.jpg"},
        ]
        assert result == expected_result
        mock_dynamodb_dao.scan.assert_called_once_with(limit=100)

    def test_get_hidden_image(self, mock_dynamodb_dao):
        """Test getting the hidden image."""
        # Arrange
        expected_image = {
            "teamName": "HIDDEN_IMAGE",
            "imageUrl": "https://example.com/hidden.jpg",
            "isHidden": True,
        }
        mock_dynamodb_dao.get_item.return_value = expected_image

        # Act
        result = mock_dynamodb_dao.get_hidden_image()

        # Assert
        assert result == expected_image
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": "HIDDEN_IMAGE"})

    def test_get_team_image(self, mock_dynamodb_dao):
        """Test getting a team's image."""
        # Arrange
        team_name = "test_team"
        expected_image = {
            "teamName": team_name,
            "imageUrl": "https://example.com/team_image.jpg",
        }
        mock_dynamodb_dao.get_item.return_value = expected_image

        # Act
        result = mock_dynamodb_dao.get_team_image(team_name)

        # Assert
        assert result == expected_image
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": team_name})

    def test_get_votes_given_by_team(self, mock_dynamodb_dao):
        """Test getting votes given by a team."""
        # Arrange
        team_name = "test_team"
        votes_given = {"team1", "team2", "PLACEHOLDER"}
        mock_dynamodb_dao.get_item.return_value = {
            "teamName": team_name,
            "votesGiven": votes_given,
        }

        # Act
        result = mock_dynamodb_dao.get_votes_given_by_team(team_name)

        # Assert
        assert set(result) == {"team1", "team2"}  # PLACEHOLDER should be removed
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": team_name})

    def test_get_votes_given_by_nonexistent_team(self, mock_dynamodb_dao):
        """Test getting votes given by a nonexistent team."""
        # Arrange
        team_name = "nonexistent_team"
        mock_dynamodb_dao.get_item.return_value = None

        # Act
        result = mock_dynamodb_dao.get_votes_given_by_team(team_name)

        # Assert
        assert result == []
        mock_dynamodb_dao.get_item.assert_called_once_with({"teamName": team_name})

    def test_get_votes_remaining(self, mock_dynamodb_dao):
        """Test getting votes remaining for a team."""
        # Arrange
        team_name = "test_team"
        # Mock get_votes_given_by_team to return 1 vote used
        mock_dynamodb_dao.get_votes_given_by_team = MagicMock(return_value=["team1"])

        # Act
        result = mock_dynamodb_dao.get_votes_remaining(team_name)

        # Assert
        assert result == MAX_VOTES_PER_TEAM - 1
        mock_dynamodb_dao.get_votes_given_by_team.assert_called_once_with(team_name)
