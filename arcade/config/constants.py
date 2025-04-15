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
PUBG_GAME_STATE_TABLE = "pubg-game-state"

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_SYSTEM_MESSAGE = """You are a dumb AI assistant."""
DEFAULT_TEMPERATURE = 0.8
DEFAULT_TOOLS = []

# Game Config
OVERRIDE_CODE = "Mike-One-Seven"


DEFAULT_POWER_DISTRIBUTION = {
    "total_available_power": 350.0,
    "current_allocation": {
        "life_support": {
            "system_id": 1,
            "current_power": 45.7,
            "minimum_required": 40.0,
            "status": "operational",
        },
        "main_engines": {
            "system_id": 2,
            "current_power": 80.3,
            "minimum_required": 75.0,
            "status": "warning",
        },
        "navigation": {
            "system_id": 3,
            "current_power": 10.2,
            "minimum_required": 25.0,
            "status": "error",
        },
        "communications": {
            "system_id": 4,
            "current_power": 10.5,
            "minimum_required": 5.0,
            "status": "operational",
        },
        "weapons_systems": {
            "system_id": 5,
            "current_power": 0.0,
            "minimum_required": 30.0,
            "status": "offline",
        },
        "shield_generators": {
            "system_id": 6,
            "current_power": 20.8,
            "minimum_required": 35.0,
            "status": "error",
        },
        "sensor_array": {
            "system_id": 7,
            "current_power": 22.4,
            "minimum_required": 15.0,
            "status": "operational",
        },
        "artificial_gravity": {
            "system_id": 8,
            "current_power": 50.0,
            "minimum_required": 40.0,
            "status": "operational",
        },
        "emergency_thrusters": {
            "system_id": 9,
            "current_power": 18.7,
            "minimum_required": 15.0,
            "status": "warning",
        },
        "quantum_stabilizers": {
            "system_id": 10,
            "current_power": 30.1,
            "minimum_required": 40.0,
            "status": "error",
        },
        "recreational_systems": {
            "system_id": 11,
            "current_power": 15.0,
            "minimum_required": 0.0,
            "status": "operational",
        },
        "science_labs": {
            "system_id": 12,
            "current_power": 25.0,
            "minimum_required": 0.0,
            "status": "operational",
        },
        "cargo_bay_systems": {
            "system_id": 13,
            "current_power": 12.0,
            "minimum_required": 5.0,
            "status": "operational",
        },
        "reserve_power": {
            "system_id": 14,
            "current_power": 9.3,
            "minimum_required": 0.0,
            "status": "operational",
        },
    },
    "power_generation_status": "stable",
}
