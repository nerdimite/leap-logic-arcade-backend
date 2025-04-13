# Technical Design (Pic Perfect Challenge)

The Pic Perfect Challenge component follows the design principles outlined in the style guide, with clear separation between data, service, and API layers.

## Data Model

### Constants

The following constants are defined in `arcade/config/constants.py`:

```python
# DynamoDB Tables
TEAMS_TABLE = "logic-arcade-teams"
PP_IMAGES_TABLE = "pic-perfect-images"
PP_LEADERBOARD_TABLE = "pic-perfect-leaderboard"
ARCADE_STATE_TABLE = "arcade-challenge-state"

# Maximum number of votes a team can cast
MAX_VOTES_PER_TEAM = 3
```

Challenge State Enum (defined in arcade/types/**init**.py as it is a shared type)

```python
from enum import Enum, auto

class ChallengeState(Enum):
    LOCKED = "locked"       # Challenge is locked and not available
    SUBMISSION = "submission"  # Teams can submit entries
    VOTING = "voting"       # Teams can vote on entries
    SCORING = "scoring"     # Scores are being calculated
    COMPLETE = "complete"   # Challenge is completed
```

### DynamoDB Tables

**Table: `pic-perfect-images`**

- **Primary Key**: `teamName` (String) - Team identifier or 'HIDDEN_IMAGE' for original image
- **Attributes**:
  - `imageUrl` (String) - URL to the generated/uploaded image
  - `prompt` (String) - Prompt used to generate the image
  - `timestamp` (String) - ISO format timestamp in Asia/Kolkata timezone
  - `isHidden` (Boolean) - Flag to identify if this is the hidden original image
  - `votes` (StringSet) - Set of team names that voted for this image
  - `votesGiven` (StringSet) - Set of teams this team has voted for

**Table: `pic-perfect-leaderboard`**

- **Composite Key**:
  - **Partition Key**: `challengeId` (String) - Challenge identifier (e.g., "pic-perfect", "treasure-hunt")
  - **Sort Key**: `teamName` (String) - Team identifier
- **Attributes**:
  - `deceptionPoints` (Number) - Points earned from votes received (3 per vote)
  - `discoveryPoints` (Number) - Points earned from correctly identifying hidden image (10 points)
  - `totalPoints` (Number) - Sum of deception and discovery points
  - `imageUrl` (String) - URL to the team's submitted image
  - `votedForHidden` (Boolean) - Whether the team correctly identified the hidden image

**Table: `arcade-challenge-state`**

- **Primary Key**: `challengeId` (String) - Challenge identifier (e.g., "pic-perfect", "treasure-hunt")
- **Attributes**:
  - `state` (String) - Current challenge state (from ChallengeState enum)
  - `startTime` (String) - ISO format timestamp when the challenge started
  - `endTime` (String) - ISO format timestamp when the challenge was finalized
  - `metadata` (Map) - Challenge-specific metadata (e.g., hiddenImageRevealed for Pic Perfect)
  - `config` (Map) - Challenge configuration parameters

**Table: `logic-arcade-teams`**

- **Primary Key**: `teamName` (String) - Team identifier
- **Attributes**:
  - `createdAt` (String) - ISO format timestamp of team creation
  - `lastActive` (String) - ISO format timestamp of last activity
  - `members` (StringSet) - Set of member identifiers

### Core Interfaces

**`IDynamoDBDao` Interface**

```python
class IDynamoDBDao(Protocol):
    """Interface for DynamoDB data access operations."""

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]: ...
    def put_item(self, item: Dict[str, Any]) -> bool: ...
    def update_item(self, key: Dict[str, Any], updates: Dict[str, Any]) -> bool: ...
    def delete_item(self, key: Dict[str, Any]) -> bool: ...
    def scan(self, limit: int = 100) -> List[Dict[str, Any]]: ...
```

**`IImagesDao` Interface**

```python
class IImagesDao(Protocol):
    """Interface for image submission and voting operations."""

    def add_image(self, team_name: str, image_url: str, prompt: str) -> Dict: ...
    def add_hidden_image(self, image_url: str, prompt: str) -> Dict: ...
    def vote_on_image(self, voting_team: str, target_team: Union[str, List[str]]) -> Dict: ...
    def get_all_images(self, exclude_teams: Optional[Union[List[str], str]] = None) -> List[Dict]: ...
    def get_hidden_image(self) -> Optional[Dict]: ...
    def get_team_image(self, team_name: str) -> Optional[Dict]: ...
    def get_votes_given_by_team(self, team_name: str) -> List[str]: ...
    def get_votes_remaining(self, team_name: str) -> int: ...
```

**`ILeaderboardDao` Interface**

```python
class ILeaderboardDao(Protocol):
    """Interface for leaderboard operations."""

    def update_score(
        self, challenge_id: str, team_name: str, score_updates: Dict[str, Union[int, bool, str]]
    ) -> bool: ...
    def get_leaderboard(self, challenge_id: str) -> List[Dict]: ...
    def get_team_score(self, challenge_id: str, team_name: str) -> Optional[Dict]: ...
    def reset_leaderboard(self, challenge_id: str) -> bool: ...
```

**`IStateDao` Interface**

```python
class IStateDao(Protocol):
    """Interface for challenge state operations."""

    def get_challenge_state(self, challenge_id: str) -> Optional[Dict[str, Any]]: ...
    def update_challenge_state(self, challenge_id: str, state_updates: Dict[str, Any]) -> bool: ...
    def initialize_challenge(self, challenge_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def finalize_challenge(self, challenge_id: str, end_time: Optional[str] = None) -> bool: ...
    def lock_challenge(self, challenge_id: str) -> bool: ...
    def unlock_challenge(self, challenge_id: str, target_state: ChallengeState = ChallengeState.SUBMISSION) -> bool: ...
    def is_challenge_active(self, challenge_id: str) -> bool: ...
    def is_challenge_locked(self, challenge_id: str) -> bool: ...
    def is_challenge_complete(self, challenge_id: str) -> bool: ...
    def get_all_challenges(self) -> List[Dict[str, Any]]: ...
```

### Data Access Objects

**`DynamoDBDao`**

- Base class providing common DynamoDB operations
- Handles low-level AWS SDK interactions
- Manages serialization/deserialization
- Implements `IDynamoDBDao` interface

**`ImagesDao`**

- Extends `DynamoDBDao`
- Implements `IImagesDao` interface
- Handles all image submission and voting operations
- Validates inputs and enforces business rules:
  - One submission per team
  - Maximum votes per team
  - No self-voting
  - No duplicate votes

**`LeaderboardDao`**

- Extends `DynamoDBDao`
- Implements `ILeaderboardDao` interface
- Handles leaderboard operations for multiple challenges using composite key
- Stores scores with challengeId + teamName as the primary key
- Retrieves leaderboard entries by querying on challengeId
- Validates inputs and enforces business rules:
  - Reset leaderboard for specific challenges
  - Isolate data between different challenges

**`StateDao`**

- Extends `DynamoDBDao`
- Implements `IStateDao` interface
- Handles challenge state operations for all arcade challenges
- Manages state transitions based on the ChallengeState enum:
  - LOCKED → SUBMISSION → VOTING → SCORING → COMPLETE
- Enforces state validation:
  - Certain operations only allowed in specific states
  - State transitions must follow the defined flow
- Supports challenge-specific configuration via the config map
- Provides challenge lifecycle management:
  - Initialization with default or custom configuration
  - Locking/unlocking challenges for maintenance or scheduling
  - Finalization with automatic timestamp recording
- Handles metadata for challenge-specific extended attributes

**`TeamsDao`**

- Extends `DynamoDBDao`
- Implements `ITeamsDao` interface
- Handles basic CRUD operations for the `logic-arcade-teams` table
  - register_team
  - get_team
  - update_team
  - delete_team
  - get_all_teams
  - get_team_count

## Service Design

### Core Service Boilerplate

The typed boilerplate for the service is as follows:

**`PicPerfectService` Class**

```python
class IPicPerfectService():
    """Service for Pic Perfect challenge business logic."""

    def submit_team_image(self, team_name: str, image_url: str, prompt: str) -> Dict:
        """
        Submit a team's generated image to the challenge.

        Args:
            team_name: Identifier of the submitting team
            image_url: URL to the generated image
            prompt: Text prompt used to generate the image

        Returns:
            Dict containing submission status, timestamp, and any error messages

        Raises:
            ValueError: If team has already submitted an image
        """
        ...

    def submit_hidden_image(self, image_url: str, prompt: str) -> Dict:
        """
        Submit the hidden original image (admin only).

        Args:
            image_url: URL to the original image
            prompt: Text prompt describing the image

        Returns:
            Dict containing submission status and any error messages

        Raises:
            ValueError: If hidden image already exists
        """
        ...

    def cast_votes(self, team_name: str, voted_teams: List[str]) -> Dict:
        """
        Cast votes from a team to other teams' images.

        Args:
            team_name: Identifier of the voting team
            voted_teams: List of team identifiers receiving votes

        Returns:
            Dict containing voting results, list of successfully voted teams, and remaining votes

        Raises:
            ValueError: If team tries to vote more than MAX_VOTES_PER_TEAM times
                       If team tries to vote for their own image
                       If team tries to vote for the same image multiple times
        """
        ...

    def get_voting_pool(self, requesting_team: str) -> List[Dict]:
        """
        Get all images available for voting, excluding the requesting team's image.

        Args:
            requesting_team: Identifier of the team requesting the voting pool

        Returns:
            List of image details (team name, image URL, prompt) for voting
        """
        ...

    def get_team_status(self, team_name: str) -> Dict:
        """
        Get a team's current submission and voting status.

        Args:
            team_name: Identifier of the team to check

        Returns:
            Dict containing submission status, image details (if submitted),
            list of teams voted for, and remaining votes
        """
        ...

    def calculate_scores(self) -> List[Dict]:
        """
        Calculate scores for all teams based on voting results.

        Scoring logic:
        - 3 points per vote received (deception points)
        - 10 points for correctly identifying hidden image (discovery points)

        Returns:
            List of team scores with deception, discovery, and total points
        """
        ...

    def get_leaderboard(self) -> Dict:
        """
        Get the current leaderboard with team rankings and scores.

        Returns:
            Dict containing:
            - List of teams with scores, ranked by total points
            - Hidden image details
            - Current challenge state
        """
        ...

    def finalize_challenge(self) -> Dict:
        """
        Finalize the challenge, calculate final scores, and transition to completed state.

        This method:
        1. Calculates final scores for all teams
        2. Updates the leaderboard with final results
        3. Transitions the challenge state to COMPLETE using StateDao
        4. Records the end time of the challenge
        5. Updates metadata to indicate the hidden image is revealed

        Returns:
            Dict containing success status, number of teams scored, and any error messages
        """
        ...

    def transition_challenge_state(self, target_state: ChallengeState) -> Dict:
        """
        Transition the challenge to a new state.

        Args:
            target_state: The state to transition to

        Returns:
            Dict containing success status, previous state, current state, and any error messages

        Raises:
            ValueError: If the state transition is not valid
        """
        ...

    def get_submission_status(self) -> Dict:
        """
        Get the status of team submissions.

        Checks which teams have submitted images against the total registered teams.

        Returns:
            Dict containing counts of teams submitted, total teams, list of pending teams,
            and a flag indicating if the challenge can transition to voting phase
        """
        ...

    def get_voting_status(self) -> Dict:
        """
        Get the status of team voting.

        Checks which teams have used all their votes against the total participating teams.

        Returns:
            Dict containing counts of teams that have completed voting, total teams,
            list of pending teams, and a flag indicating if the challenge can transition to scoring phase
        """
        ...

    def can_transition_to_voting(self) -> bool:
        """
        Check if the challenge can transition to voting phase.

        Returns:
            Boolean indicating if all teams have submitted entries
        """
        ...

    def can_transition_to_scoring(self) -> bool:
        """
        Check if the challenge can transition to scoring phase.

        Returns:
            Boolean indicating if voting period should be closed
        """
        ...
```

### Service Implementation

**`PicPerfectService`**

- Implements `IPicPerfectService` interface
- Dependencies:
  - `IImagesDao` for image data access
  - `ILeaderboardDao` for leaderboard operations
  - `IStateDao` for challenge state management
- Constructor:
  - Initializes with the fixed challenge ID "pic-perfect"
  - Injects required DAO dependencies
- Business logic:
  - Orchestrates submission workflow
  - Manages voting process
  - Calculates scores based on voting results
  - Updates leaderboard with final scores
  - Coordinates challenge state transitions using StateDao
- State Transition Logic:
  - LOCKED → SUBMISSION: Admin initializes challenge
  - SUBMISSION → VOTING: Admin triggers transition when all teams have submitted
  - VOTING → SCORING: Admin triggers transition when voting period ends
  - SCORING → COMPLETE: Admin finalizes challenge after scores are calculated
- State-Based API Access Control:
  - SUBMISSION state: Only submission APIs are enabled for users
  - VOTING state: Only voting APIs are enabled for users
  - SCORING/COMPLETE state: Only leaderboard viewing is enabled for users
  - Admin APIs remain accessible regardless of state
- State Validation Methods:
  - `can_transition_to_voting()`: Checks if all teams have submitted
  - `can_transition_to_scoring()`: Checks if voting period has ended
- Scoring logic:
  - 3 points per vote received (deception points)
  - 10 points for correctly identifying hidden image (discovery points)
  - Total = Deception + Discovery points

### Challenge Workflow

1. **Challenge Initialization**

   - Admin submits hidden image
   - Admin sets challenge parameters (time limits, etc.)
   - Reset leaderboard if necessary

2. **Submission Phase**

   - Teams submit their generated images
   - System validates submissions
   - System stores image URL and prompt

3. **Voting Phase**

   - All images, including hidden image, are presented
   - Teams cast votes (up to MAX_VOTES_PER_TEAM = 3)
   - System tracks votes and prevents duplicates

4. **Scoring Phase**
   - System identifies if teams voted for the hidden image
   - System calculates deception points (3 × votes received)
   - System calculates discovery points (10 if voted for hidden image)
   - System updates leaderboard with total scores
   - Leaderboard is finalized and published

## API Design

### API Endpoints

**Image Submission Endpoints**

```
POST /api/pic-perfect/team-image
- Description: Submit a team's generated image
- Request:
  - team_name: string
  - image_url: string
  - prompt: string
- Response:
  - success: boolean
  - timestamp: string
  - error?: string

POST /api/pic-perfect/hidden-image
- Description: Submit the hidden original image (admin only)
- Request:
  - image_url: string
  - prompt: string
- Response:
  - success: boolean
  - error?: string
```

**Voting Endpoints**

```
POST /api/pic-perfect/votes
- Description: Cast votes for other teams' images
- Request:
  - team_name: string
  - voted_teams: string[]
- Response:
  - success: boolean
  - voted_for: string[]
  - votesRemaining: number
  - error?: string

GET /api/pic-perfect/voting-pool/{team_name}
- Description: Get all images for voting (excluding own team's image)
- Response:
  - images: [
      {
        teamName: string,
        imageUrl: string,
        prompt: string
      }
    ]
```

**Status and Results Endpoints**

```
GET /api/pic-perfect/team-status/{team_name}
- Description: Get team's submission and voting status
- Response:
  - hasSubmitted: boolean
  - submission?: {
      imageUrl: string,
      prompt: string,
      timestamp: string
    }
  - votesGiven: string[]
  - votesRemaining: number (0-3)

GET /api/pic-perfect/leaderboard
- Description: Get challenge results and scores
- Response:
  - teams: [
      {
        teamName: string,
        deceptionPoints: number,
        discoveryPoints: number,
        totalPoints: number,
        imageUrl: string,
        votedForHidden: boolean
      }
    ]
  - hiddenImage: {
      imageUrl: string,
      prompt: string
    }
  - challengeState: ChallengeState (enum value from ChallengeState)
```

**Admin Endpoints**

```
POST /api/pic-perfect/admin/finalize
- Description: Finalize the challenge and calculate scores (admin only)
- Response:
  - success: boolean
  - teamsScored: number
  - error?: string

POST /api/pic-perfect/admin/reset
- Description: Reset the challenge for a new round (admin only)
- Request:
  - preserveTeams: boolean
- Response:
  - success: boolean
  - error?: string

POST /api/pic-perfect/admin/transition
- Description: Transition the challenge to a new state (admin only)
- Request:
  - targetState: ChallengeState
- Response:
  - success: boolean
  - previousState: ChallengeState
  - currentState: ChallengeState
  - error?: string

POST /api/pic-perfect/admin/start-challenge
- Description: Initialize challenge and set hidden image in one operation (admin only)
- Request:
  - image_url: string
  - prompt: string
  - config?: object (optional challenge configuration)
- Response:
  - success: boolean
  - challengeState: ChallengeState
  - hiddenImageSet: boolean
  - error?: string

GET /api/pic-perfect/admin/submission-status
- Description: Get status of team submissions (admin only)
- Response:
  - teamsSubmitted: number
  - totalTeams: number
  - pendingTeams: string[]
  - canTransitionToVoting: boolean

GET /api/pic-perfect/admin/voting-status
- Description: Get status of team voting (admin only)
- Response:
  - teamsVoted: number
  - totalTeams: number
  - pendingTeams: string[]
  - canTransitionToScoring: boolean
```

### Schema Definitions

**TeamImageSubmission**

```
{
  team_name: string
  image_url: string
  prompt: string
}
```

**VotingRequest**

```
{
  team_name: string
  voted_teams: string[]
}
```

**ImageDetails**

```
{
  teamName: string
  imageUrl: string
  prompt: string
  timestamp: string
  isHidden: boolean
}
```

**TeamScore**

```
{
  teamName: string
  deceptionPoints: number
  discoveryPoints: number
  totalPoints: number
  imageUrl: string
  votedForHidden: boolean
}
```

**LeaderboardEntry**

```
{
  teamName: string
  deceptionPoints: number
  discoveryPoints: number
  totalPoints: number
  imageUrl: string
  votedForHidden: boolean
  rank: number
}
```

## Challenge Lifecycle and Service Interactions

The following sequence details the integrated flow between controllers, services, and data access layers during each phase of the Pic Perfect Challenge.

### 1. Challenge Initialization

1. Admin API call: `POST /api/pic-perfect/admin/start-challenge`
   - PicPerfectController receives request with image_url, prompt, and optional config
   - Controller calls `PicPerfectService.start_challenge(image_url, prompt, config)`
   - Service performs the following operations:
     - Calls `StateDao.initialize_challenge("pic-perfect", config)` to set state to SUBMISSION
     - Calls `ImagesDao.add_hidden_image(teamName="HIDDEN_IMAGE", image_url, prompt)` to set the hidden image
     - Updates challenge metadata to record initialization timestamp
   - StateDao performs DynamoDB update to ARCADE_STATE_TABLE
   - ImagesDao performs DynamoDB put_item to PP_IMAGES_TABLE with teamName="HIDDEN_IMAGE"

### 2. Submission Phase

1. Team API call: `GET /api/pic-perfect/team-status/{team_name}`

   - PicPerfectController receives request with team_name
   - Controller calls `PicPerfectService.get_team_status(team_name)`
   - Service calls `ImagesDao.get_team_image(team_name)` to check if team has submitted
   - Service calls `ImagesDao.get_votes_given_by_team(team_name)` to calculate votes remaining
   - ImagesDao performs DynamoDB get_item operations on PP_IMAGES_TABLE

2. Team API call: `POST /api/pic-perfect/team-image`

   - PicPerfectController receives request with team_name, image_url, prompt
   - Controller calls `PicPerfectService.submit_team_image(team_name, image_url, prompt)`
   - Service validates state is SUBMISSION
   - Service calls `ImagesDao.add_image(team_name, image_url, prompt)`
   - ImagesDao performs DynamoDB put_item to PP_IMAGES_TABLE

3. Admin API call: `GET /api/pic-perfect/admin/submission-status`

   - PicPerfectController receives request
   - Controller calls `PicPerfectService.get_submission_status()`
   - Service calls `ImagesDao.get_all_images()` to count team submissions
   - Service calls `can_transition_to_voting()` to check completion status
   - ImagesDao performs DynamoDB scan on PP_IMAGES_TABLE

4. Admin API call: `POST /api/pic-perfect/admin/transition`
   - PicPerfectController receives request with target state = VOTING
   - Controller calls `PicPerfectService.transition_challenge_state(ChallengeState.VOTING)`
   - Service validates `can_transition_to_voting()` returns true
   - Service calls `StateDao.update_challenge_state("pic-perfect", {"state": ChallengeState.VOTING})`
   - StateDao performs DynamoDB update_item on ARCADE_STATE_TABLE

### 3. Voting Phase

1. Team API call: `GET /api/pic-perfect/voting-pool/{team_name}`

   - PicPerfectController receives request with team_name
   - Controller calls `PicPerfectService.get_voting_pool(team_name)`
   - Service validates state is VOTING
   - Service calls `ImagesDao.get_all_images(exclude_teams=team_name)`
   - ImagesDao performs DynamoDB scan on PP_IMAGES_TABLE filtering out the team's own image

2. Team API call: `POST /api/pic-perfect/votes`

   - PicPerfectController receives request with team_name and voted_teams array
   - Controller calls `PicPerfectService.cast_votes(team_name, voted_teams)`
   - Service validates state is VOTING
   - Service validates votes are within MAX_VOTES_PER_TEAM limit
   - Service calls `ImagesDao.vote_on_image(team_name, voted_teams)`
   - ImagesDao performs multiple DynamoDB update_item operations on PP_IMAGES_TABLE:
     - Updates votes attribute for each target team
     - Updates votesGiven attribute for the voting team

3. Admin API call: `GET /api/pic-perfect/admin/voting-status`

   - PicPerfectController receives request
   - Controller calls `PicPerfectService.get_voting_status()`
   - Service calls `ImagesDao.get_all_images()` to check team voting completion
   - Service calls `can_transition_to_scoring()` to check readiness
   - ImagesDao performs DynamoDB scan on PP_IMAGES_TABLE

4. Admin API call: `POST /api/pic-perfect/admin/transition`
   - PicPerfectController receives request with target state = SCORING
   - Controller calls `PicPerfectService.transition_challenge_state(ChallengeState.SCORING)`
   - Service validates `can_transition_to_scoring()` returns true
   - Service calls `StateDao.update_challenge_state("pic-perfect", {"state": ChallengeState.SCORING})`
   - StateDao performs DynamoDB update_item on ARCADE_STATE_TABLE

### 4. Scoring Phase

1. Admin API call: `POST /api/pic-perfect/admin/finalize`

   - PicPerfectController receives request
   - Controller calls `PicPerfectService.finalize_challenge()`
   - Service validates state is SCORING
   - Service calls `calculate_scores()` which:
     - Calls `ImagesDao.get_all_images()` to retrieve voting data
     - Calls `ImagesDao.get_hidden_image()` to identify hidden image
     - For each team:
       - Calculates deception points (3 × votes received)
       - Determines if team voted for hidden image (discovery points = 10 if true)
       - Calls `LeaderboardDao.update_score(team_name, score_data)`
   - Service calls `StateDao.finalize_challenge("pic-perfect")` to set state to COMPLETE
   - Service calls `StateDao.update_challenge_state("pic-perfect", {"metadata": {"hiddenImageRevealed": true}})`
   - LeaderboardDao performs DynamoDB put_item operations to PP_LEADERBOARD_TABLE
   - StateDao performs DynamoDB update_item on ARCADE_STATE_TABLE

2. Team/Admin API call: `GET /api/pic-perfect/leaderboard`
   - PicPerfectController receives request
   - Controller calls `PicPerfectService.get_leaderboard()`
   - Service calls `LeaderboardDao.get_leaderboard()` to retrieve scores
   - Service calls `ImagesDao.get_hidden_image()` to include hidden image details
   - Service calls `StateDao.get_challenge_state("pic-perfect")` to include challenge state
   - LeaderboardDao performs DynamoDB scan on PP_LEADERBOARD_TABLE
   - ImagesDao performs DynamoDB get_item on PP_IMAGES_TABLE
   - StateDao performs DynamoDB get_item on ARCADE_STATE_TABLE

### 5. Challenge Reset (Optional)

1. Admin API call: `POST /api/pic-perfect/admin/reset`
   - PicPerfectController receives request
   - Controller calls service method to reset challenge
   - Service calls `LeaderboardDao.reset_leaderboard()`
   - Service calls `ImagesDao` to clear images table
   - Service calls `StateDao.lock_challenge("pic-perfect")`
   - Multiple DynamoDB operations across all tables to clear data

## Security Considerations

1. **Authentication**

   - Authentication handled by Clerk (third-party service)
   - All endpoints require authenticated user context
   - Admin privileges managed through Clerk roles

2. **Input Validation**

   - Validate all inputs: team names, URLs, prompts
   - Enforce URL format and security checks
   - Sanitize all user inputs

3. **Rate Limiting**

   - Limit submission attempts
   - Prevent voting spam

4. **Data Protection**
   - No sensitive data stored in the database
   - URLs should point to secure storage
