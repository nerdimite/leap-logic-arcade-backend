import os
from unittest.mock import MagicMock, patch

import pytest

from arcade.config.constants import MAX_VOTES_PER_TEAM, PP_IMAGES_TABLE
from arcade.core.dao.images_dao import ImagesDao


# Just for debugging
def print_tables(dynamodb_resource):
    print("Available tables:", [t.name for t in dynamodb_resource.tables.all()])


@pytest.mark.integration
class TestImagesDaoIntegration:
    """Integration tests for ImagesDao class with DynamoDB."""

    @pytest.fixture
    def images_dao(self, dynamodb_resource, setup_test_tables):
        """Create an ImagesDao instance with real DynamoDB mocked by moto."""
        # Initialize the DAO and patch it to use the test table name
        with patch(
            "arcade.config.constants.PP_IMAGES_TABLE",
            os.environ["DYNAMODB_TABLE_PREFIX"] + PP_IMAGES_TABLE,
        ):
            dao = ImagesDao()
            dao.table = dynamodb_resource.Table(
                os.environ["DYNAMODB_TABLE_PREFIX"] + PP_IMAGES_TABLE
            )
            yield dao

    def test_add_image_integration(self, images_dao):
        """Test image addition with DynamoDB integration."""
        # Arrange
        team_name = "integration_team"
        image_url = "https://example.com/image.jpg"
        prompt = "test prompt"

        # Act
        # Use a fixed timestamp for testing
        current_time = "2023-01-01T12:00:00+05:30"
        with patch("arcade.core.dao.images_dao.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.return_value.isoformat.return_value = current_time
            mock_datetime.now = mock_now

            result = images_dao.add_image(team_name, image_url, prompt)

        # Assert
        assert result["success"] is True
        assert result["timestamp"] == current_time

        # Verify the item was stored correctly by retrieving it
        saved_item = images_dao.get_team_image(team_name)
        assert saved_item is not None
        assert saved_item["teamName"] == team_name
        assert saved_item["imageUrl"] == image_url
        assert saved_item["prompt"] == prompt
        assert saved_item["timestamp"] == current_time
        assert saved_item["isHidden"] is False
        assert "votes" in saved_item
        assert "votesGiven" in saved_item

    def test_add_hidden_image_integration(self, images_dao):
        """Test adding hidden image with DynamoDB integration."""
        # Arrange
        image_url = "https://example.com/hidden.jpg"
        prompt = "hidden image prompt"

        # Act
        # Use a fixed timestamp for testing
        current_time = "2023-01-01T12:00:00+05:30"
        with patch("arcade.core.dao.images_dao.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.return_value.isoformat.return_value = current_time
            mock_datetime.now = mock_now

            result = images_dao.add_hidden_image(image_url, prompt)

        # Assert
        assert result["success"] is True

        # Verify the item was stored correctly by retrieving it
        saved_item = images_dao.get_hidden_image()
        assert saved_item is not None
        assert saved_item["teamName"] == "HIDDEN_IMAGE"
        assert saved_item["imageUrl"] == image_url
        assert saved_item["prompt"] == prompt
        assert saved_item["timestamp"] == current_time
        assert saved_item["isHidden"] is True
        assert "votes" in saved_item
        assert "votesGiven" in saved_item

    def test_vote_on_image_integration(self, images_dao):
        """Test voting on an image with DynamoDB integration."""
        # Arrange - first create the teams and images
        voting_team = "voting_team"
        target_team = "target_team"

        # Add the voting team
        images_dao.add_image(
            voting_team, "https://example.com/voting_team.jpg", "voting team prompt"
        )

        # Add the target team
        images_dao.add_image(
            target_team, "https://example.com/target_team.jpg", "target team prompt"
        )

        # Act
        result = images_dao.vote_on_image(voting_team, target_team)

        # Assert
        assert result["success"] is True
        assert target_team in result["voted_for"]

        # Verify votes were recorded correctly by retrieving the updated items
        voting_team_data = images_dao.get_team_image(voting_team)
        target_team_data = images_dao.get_team_image(target_team)

        # Check voting team's votesGiven
        votes_given = voting_team_data.get("votesGiven", set())
        if "PLACEHOLDER" in votes_given:
            votes_given.remove("PLACEHOLDER")
        assert target_team in votes_given

        # Check target team's votes
        votes_received = target_team_data.get("votes", set())
        if "PLACEHOLDER" in votes_received:
            votes_received.remove("PLACEHOLDER")
        assert voting_team in votes_received

    def test_get_all_images_integration(self, images_dao):
        """Test retrieving all images with DynamoDB integration."""
        # Arrange - first add some images
        team1 = "team1_all"
        team2 = "team2_all"

        images_dao.add_image(team1, "https://example.com/image1.jpg", "prompt1")

        images_dao.add_image(team2, "https://example.com/image2.jpg", "prompt2")

        # Act
        result = images_dao.get_all_images()

        # Assert
        assert len(result) >= 2  # May include other images from other tests
        team_names = [img["teamName"] for img in result]
        assert team1 in team_names
        assert team2 in team_names

    def test_get_all_images_with_exclude_integration(self, images_dao):
        """Test retrieving all images with exclusion and DynamoDB integration."""
        # Arrange - first add some images
        team1 = "team1_exclude"
        team2 = "team2_exclude"
        team3 = "team3_exclude"

        images_dao.add_image(team1, "https://example.com/image1_exclude.jpg", "prompt1")

        images_dao.add_image(team2, "https://example.com/image2_exclude.jpg", "prompt2")

        images_dao.add_image(team3, "https://example.com/image3_exclude.jpg", "prompt3")

        # Act
        result = images_dao.get_all_images(exclude_teams=team2)

        # Assert
        team_names = [img["teamName"] for img in result]
        assert team1 in team_names
        assert team3 in team_names
        assert team2 not in team_names

    def test_get_hidden_image_integration(self, images_dao):
        """Test retrieving hidden image with DynamoDB integration."""
        # Arrange - Add a hidden image
        image_url = "https://example.com/hidden_test.jpg"
        prompt = "hidden prompt test"

        images_dao.add_hidden_image(image_url, prompt)

        # Act
        result = images_dao.get_hidden_image()

        # Assert
        assert result is not None
        assert result["teamName"] == "HIDDEN_IMAGE"
        assert result["imageUrl"] == image_url
        assert result["prompt"] == prompt
        assert result["isHidden"] is True

    def test_get_team_image_integration(self, images_dao):
        """Test retrieving team image with DynamoDB integration."""
        # Arrange
        team_name = "test_team_get"
        image_url = "https://example.com/team_get.jpg"
        prompt = "team get prompt"

        # Add the team image
        images_dao.add_image(team_name, image_url, prompt)

        # Act
        result = images_dao.get_team_image(team_name)

        # Assert
        assert result is not None
        assert result["teamName"] == team_name
        assert result["imageUrl"] == image_url
        assert result["prompt"] == prompt
        assert result["isHidden"] is False

    def test_get_votes_given_by_team_integration(self, images_dao):
        """Test retrieving votes given by a team with DynamoDB integration."""
        # Arrange
        voting_team = "team_votes_given"
        target_team1 = "team_voted_for1"
        target_team2 = "team_voted_for2"

        # Add teams
        images_dao.add_image(
            voting_team, "https://example.com/voting_team.jpg", "voting team prompt"
        )

        images_dao.add_image(
            target_team1, "https://example.com/target1.jpg", "target1 prompt"
        )

        images_dao.add_image(
            target_team2, "https://example.com/target2.jpg", "target2 prompt"
        )

        # Vote for two teams
        images_dao.vote_on_image(voting_team, [target_team1, target_team2])

        # Act
        result = images_dao.get_votes_given_by_team(voting_team)

        # Assert
        assert set(result) == {target_team1, target_team2}

    def test_get_votes_remaining_integration(self, images_dao):
        """Test retrieving votes remaining for a team with DynamoDB integration."""
        # Arrange
        team_name = "team_votes_remaining"
        target_team = "team_voted_for_remaining"

        # Add teams
        images_dao.add_image(
            team_name, "https://example.com/team_remaining.jpg", "team remaining prompt"
        )

        images_dao.add_image(
            target_team,
            "https://example.com/target_remaining.jpg",
            "target remaining prompt",
        )

        # Vote for one team
        images_dao.vote_on_image(team_name, target_team)

        # Act
        result = images_dao.get_votes_remaining(team_name)

        # Assert
        assert result == MAX_VOTES_PER_TEAM - 1

    def test_vote_on_image_exceeded_limit_integration(self, images_dao):
        """Test voting when team has already used all votes with DynamoDB integration."""
        # Arrange
        voting_team = "team_max_votes"
        # Create target teams for initial votes
        target_teams = []
        for i in range(MAX_VOTES_PER_TEAM):
            target_name = f"target_max_{i}"
            target_teams.append(target_name)
            images_dao.add_image(
                target_name,
                f"https://example.com/target_max_{i}.jpg",
                f"target max {i} prompt",
            )

        # One more team to try voting for after limit reached
        extra_team = "target_extra"
        images_dao.add_image(
            extra_team, "https://example.com/target_extra.jpg", "target extra prompt"
        )

        # Add voting team
        images_dao.add_image(
            voting_team, "https://example.com/voting_max.jpg", "voting max prompt"
        )

        # Use all available votes
        images_dao.vote_on_image(voting_team, target_teams)

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            images_dao.vote_on_image(voting_team, extra_team)
        assert "Cannot vote for 1 teams. You have 0 vote(s) remaining." in str(
            excinfo.value
        )
