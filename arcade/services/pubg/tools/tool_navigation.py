import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from arcade.config.constants import OVERRIDE_CODE
from arcade.core.dao import PubgGameDao
from arcade.services.pubg.tools.tool_codesandbox import CodeSandbox

CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR / "data"


async def get_region_map(**kwargs) -> str:
    """Get the region map."""
    with open(DATA_DIR / "map.json", "r") as f:
        return json.load(f)


async def get_current_position(**kwargs) -> str:
    """Get the current coordinates."""
    return {
        "coordinates": [127, 38, 95, 4],
        "velocity": [10, 0, 0],
    }


async def set_navigation_course(target_coordinates: List[int], **kwargs):
    """Set the course for the ship to navigate to the target coordinates."""
    pubg_game_dao = PubgGameDao()
    team_name = kwargs["team_name"]
    return pubg_game_dao.set_course_status(team_name, True)


async def set_engine_thrust(thrust: float, thrust_direction: List[int], **kwargs):
    """Set the thrust for the ship to navigate to the target coordinates."""
    pubg_game_dao = PubgGameDao()
    team_name = kwargs["team_name"]
    return pubg_game_dao.set_thrust_status(team_name, True)


async def start_engines(**kwargs):
    """Start the engines."""
    pubg_game_dao = PubgGameDao()
    team_name = kwargs["team_name"]
    return pubg_game_dao.complete_mission(team_name, True)
