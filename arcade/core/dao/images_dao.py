from datetime import datetime
from typing import Dict, List, Optional, Set, Union

import pytz

from arcade.config.constants import MAX_VOTES_PER_TEAM, PP_IMAGES_TABLE
from arcade.core.dao.base_ddb import DynamoDBDao


class ImagesDao(DynamoDBDao):
    """
    Data Access Object for handling image submissions and voting operations.

    DynamoDB Table Schema:
    - Primary Key: teamName (str) - Team identifier or 'HIDDEN_IMAGE' for original image
    - Attributes:
        - imageUrl (str) - URL to the generated/uploaded image
        - prompt (str) - Prompt used to generate the image
        - timestamp (str) - ISO format timestamp in Asia/Kolkata timezone
        - isHidden (bool) - Flag to identify if this is the hidden original image
        - votes (set[str]) - Set of team names that voted for this image
        - votesGiven (set[str]) - Set of teams this team has voted for
    """

    def __init__(self):
        """
        Initialize the DAO with the images table name from constants.
        """
        super().__init__(table_name=PP_IMAGES_TABLE)

    def add_image(self, team_name: str, image_url: str, prompt: str) -> Dict:
        """
        Add a team's submitted image to the database.

        Args:
            team_name (str): Name of the team submitting the image
            image_url (str): URL to the generated image
            prompt (str): Prompt used to generate the image

        Returns:
            dict: Result with success status and timestamp

        Raises:
            ValueError: If team has already submitted
        """
        # Check if team has already submitted
        existing_image = self.get_item({"teamName": team_name})
        if existing_image:
            raise ValueError(f"Team '{team_name}' has already submitted an image")

        # Create timestamp
        timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

        # Create item
        item = {
            "teamName": team_name,
            "imageUrl": image_url,
            "prompt": prompt,
            "timestamp": timestamp,
            "isHidden": False,
            "votes": set(["PLACEHOLDER"]),  # Empty set initially
            "votesGiven": set(["PLACEHOLDER"]),  # Track teams this team has voted for
        }

        # Store item
        success = self.put_item(item)

        return {"success": success, "timestamp": timestamp}

    def add_hidden_image(self, image_url: str, prompt: str) -> Dict:
        """
        Add the hidden original image for the challenge.

        Args:
            image_url (str): URL to the hidden original image
            prompt (str): The prompt used for the image

        Returns:
            dict: Result with success status
        """
        # Create timestamp
        timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

        # Create item with special identifier for hidden image
        item = {
            "teamName": "HIDDEN_IMAGE",  # Special identifier for hidden image
            "imageUrl": image_url,
            "prompt": prompt,
            "timestamp": timestamp,
            "isHidden": True,
            "votes": set(["PLACEHOLDER"]),
            "votesGiven": set(["PLACEHOLDER"]),  # Not used for hidden image
        }

        # Store item
        success = self.put_item(item)

        return {"success": success}

    def vote_on_image(
        self, voting_team: str, target_team: Union[str, List[str]]
    ) -> Dict:
        """
        Record a team's vote for another team's image(s).
        Each team can vote for up to 3 different teams.

        Args:
            voting_team (str): Name of the team casting the vote
            target_team (str or List[str]): Name(s) of the team(s) receiving the vote(s)

        Returns:
            dict: Result with success status

        Raises:
            ValueError: If voting team has already used all votes or targets don't exist
        """
        # Get voting team's image to check if they're registered
        voting_image = self.get_item({"teamName": voting_team})
        if not voting_image:
            raise ValueError(f"Voting team '{voting_team}' is not registered")

        # Get current votes given by the voting team
        votes_given = voting_image.get("votesGiven", set())
        if isinstance(votes_given, list):
            votes_given = set(votes_given)

        # Remove placeholder if it exists
        if "PLACEHOLDER" in votes_given:
            votes_given.remove("PLACEHOLDER")

        # Convert target_team to list if it's a single string
        if isinstance(target_team, str):
            target_teams = [target_team]
        else:
            target_teams = target_team

        # Validate uniqueness of target teams
        if len(set(target_teams)) != len(target_teams):
            raise ValueError("Duplicate teams found in the target teams list")

        # Check if voting team is trying to vote for themselves
        if voting_team in target_teams:
            raise ValueError("Teams cannot vote for their own image")

        # Check for already voted teams
        already_voted = []
        new_votes = []
        for team in target_teams:
            if team in votes_given:
                already_voted.append(team)
            else:
                new_votes.append(team)

        # If any already voted teams, don't proceed
        if already_voted:
            return {
                "success": False,
                "message": f"Already voted for: {', '.join(already_voted)}",
            }

        # Check if adding these votes would exceed the limit
        if len(votes_given) + len(new_votes) > MAX_VOTES_PER_TEAM:
            remaining = MAX_VOTES_PER_TEAM - len(votes_given)
            voted_teams = ", ".join(votes_given) if votes_given else "none"
            raise ValueError(
                f"Cannot vote for {len(new_votes)} teams. You have {remaining} vote(s) remaining. "
                f"Currently voted for: {voted_teams}"
            )

        # Verify all target teams exist and collect their current votes
        for team in new_votes:
            target_image = self.get_item({"teamName": team})
            if not target_image:
                raise ValueError(f"Target team '{team}' has no image submission")

        # Process the votes - this is done after all validation to ensure atomicity
        results = []
        for team in new_votes:
            # Get target team's current votes
            target_image = self.get_item({"teamName": team})
            current_votes = target_image.get("votes", set())
            if isinstance(current_votes, list):
                current_votes = set(current_votes)

            # Remove placeholder if it exists
            if "PLACEHOLDER" in current_votes:
                current_votes.remove("PLACEHOLDER")

            # Add vote
            current_votes.add(voting_team)

            # Update the target team's votes received
            update_result = self.update_item(
                key={"teamName": team}, updates={"votes": current_votes}
            )

            # Add to results
            results.append({"team": team, "success": update_result})

            # Add to votes given by voting team
            votes_given.add(team)

        # Update the voting team's votes given
        if new_votes:  # Only update if there are new votes
            self.update_item(
                key={"teamName": voting_team}, updates={"votesGiven": votes_given}
            )

        return {
            "success": True,
            "voted_for": new_votes,
            "results": results,
            "votesRemaining": MAX_VOTES_PER_TEAM - len(votes_given),
        }

    def get_all_images(
        self, exclude_teams: Optional[Union[List[str], str]] = None
    ) -> List[Dict]:
        """
        Get all submitted images for display in voting page.

        Args:
            exclude_teams (list or str, optional): Team name(s) to exclude from results

        Returns:
            list: List of image objects with team names and URLs
        """
        # Normalize exclude_teams to list
        if exclude_teams is None:
            exclude_teams = []
        elif isinstance(exclude_teams, str):
            exclude_teams = [exclude_teams]

        # Scan for all images
        all_images = self.scan(limit=100)  # Assuming we won't have more than 100 teams

        # Filter out excluded teams
        filtered_images = [
            image for image in all_images if image["teamName"] not in exclude_teams
        ]

        return filtered_images

    def get_hidden_image(self) -> Optional[Dict]:
        """
        Get the hidden original image for the challenge.

        Returns:
            dict or None: The hidden image data or None if not found
        """
        return self.get_item({"teamName": "HIDDEN_IMAGE"})

    def get_team_image(self, team_name: str) -> Optional[Dict]:
        """
        Get a specific team's image submission.

        Args:
            team_name (str): The name of the team

        Returns:
            dict or None: The team's image data or None if not found
        """
        return self.get_item({"teamName": team_name})

    def get_votes_given_by_team(self, team_name: str) -> List[str]:
        """
        Get the list of teams that a specific team has voted for.

        Args:
            team_name (str): The name of the team

        Returns:
            List[str]: List of team names that this team has voted for
        """
        team_image = self.get_item({"teamName": team_name})
        if not team_image:
            return []

        votes_given = team_image.get("votesGiven", set())
        if isinstance(votes_given, list):
            votes_given = set(votes_given)

        # Remove placeholder if it exists
        if "PLACEHOLDER" in votes_given:
            votes_given.remove("PLACEHOLDER")

        return list(votes_given)

    def get_votes_remaining(self, team_name: str) -> int:
        """
        Get the number of votes a team has remaining.

        Args:
            team_name (str): The name of the team

        Returns:
            int: Number of votes remaining (0-3)
        """
        votes_given = self.get_votes_given_by_team(team_name)
        return max(0, MAX_VOTES_PER_TEAM - len(votes_given))
