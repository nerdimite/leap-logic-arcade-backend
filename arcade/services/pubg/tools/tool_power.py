from pathlib import Path
from typing import List

from dynamodb_json import json_util

from arcade.core.commons.logger import get_logger
from arcade.core.dao import PubgGameDao

logger = get_logger(__name__)

from .tool_definitions import SystemPower

CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR / "data"


async def get_current_power_distribution(**kwargs):
    """Get the current power distribution on the ship."""
    pubg_game_dao = PubgGameDao()
    team_name = kwargs["team_name"]
    return pubg_game_dao.get_team_game_state(team_name)["powerDistribution"]


async def update_power_distribution(updates: List[SystemPower], **kwargs):
    """Update the power distribution on the ship."""
    pubg_game_dao = PubgGameDao()
    team_name = kwargs["team_name"]
    updates = [SystemPower(**update) for update in updates]

    power_distribution = pubg_game_dao.get_team_game_state(team_name)[
        "powerDistribution"
    ]
    try:
        for update in updates:
            power_distribution["current_allocation"][update.system_name][
                "current_power"
            ] = update.current_power
            if (
                update.current_power
                >= power_distribution["current_allocation"][update.system_name][
                    "minimum_required"
                ]
            ):
                power_distribution["current_allocation"][update.system_name][
                    "status"
                ] = "operational"
            else:
                power_distribution["current_allocation"][update.system_name][
                    "status"
                ] = "error"

        return pubg_game_dao.update_power_distribution(
            team_name, json_util.dumps(power_distribution)
        )
    except Exception as e:
        logger.error(f"Error updating power distribution: {e}", exc_info=True)
        return False
