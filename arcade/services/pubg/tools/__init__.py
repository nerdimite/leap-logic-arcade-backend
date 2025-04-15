from typing import Any, Dict

from .tool_codesandbox import *
from .tool_definitions import *
from .tool_docs import *
from .tool_navigation import *
from .tool_power import *
from .tool_system_database import *

function_map = {
    "get_crew_logs": get_crew_logs,
    "get_ship_docs": get_ship_docs,
    "force_system_login": force_system_login,
    "system_database": system_database,
    "update_power_distribution": update_power_distribution,
    "get_current_power_distribution": get_current_power_distribution,
    "get_region_map": get_region_map,
    "get_current_coordinates": get_current_coordinates,
    "davinci_coder": davinci_coder,
}


async def handle_function_call(name: str, args: Dict[str, Any]):
    """The core router for all function calls."""
    function = function_map.get(name)
    if function is None:
        raise ValueError(f"Function {name} not found")
    return await function(**args)
