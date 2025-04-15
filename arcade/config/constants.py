from pathlib import Path

PROMPTS_PATH = Path(__file__).parent.parent / "prompts"

# === Pic Perfect ===
# DynamoDB Tables
TEAMS_TABLE = "logic-arcade-teams"
PP_IMAGES_TABLE = "pic-perfect-images"
PP_LEADERBOARD_TABLE = "pic-perfect-leaderboard"
ARCADE_STATE_TABLE = "arcade-challenge-state"

# Maximum number of votes a team can cast
MAX_VOTES_PER_TEAM = 3

# === PUBG ===
# DynamoDB Tables
PUBG_AGENTS_TABLE = "pubg-agents"

DEFAULT_MODEL = "gpt-4.1-mini"

# Game Config
OVERRIDE_CODE = "Mike-One-Seven"