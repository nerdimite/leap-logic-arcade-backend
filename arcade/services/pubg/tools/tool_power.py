import json
from pathlib import Path
from typing import List

from .tool_definitions import SystemPower

CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR / "data"


async def get_current_power_distribution():
    """Get the current power distribution on the ship."""
    # TODO: Get the current power distribution from the database
    with open(DATA_DIR / "default_power_dist.json", "r") as f:
        return json.load(f)


async def update_power_distribution(updates: List[SystemPower]):
    """Update the power distribution on the ship."""
    # TODO: Update the power distribution on the ship
    return {"success": True, "message": "Power distribution updated successfully"}
