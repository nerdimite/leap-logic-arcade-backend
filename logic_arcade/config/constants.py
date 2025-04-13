from pathlib import Path

PROMPTS_PATH = Path(__file__).parent.parent / "prompts"

# DynamoDB Tables
TEAMS_TABLE = "logic-arcade-teams"

PP_IMAGES_TABLE = "pic-perfect-images"
PP_LEADERBOARD_TABLE = "pic-perfect-leaderboard"

# Maximum number of votes a team can cast
MAX_VOTES_PER_TEAM = 3
