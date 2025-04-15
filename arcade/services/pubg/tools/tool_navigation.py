import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from arcade.config.constants import OVERRIDE_CODE
from arcade.services.pubg.tools.tool_codesandbox import CodeSandbox

CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR / "data"


async def get_region_map() -> str:
    """Get the region map."""
    with open(DATA_DIR / "map.json", "r") as f:
        return json.load(f)


async def get_current_coordinates() -> str:
    """Get the current coordinates."""
    return [127, 38, 95, 4]


async def propulsion_system(command: str, payload: Dict[str, Any]):
    pass
