from typing import Any, Dict

from .tool_definitions import *
from .tools import *

function_map = {
    "get_crew_logs": get_crew_logs,
    "get_ship_docs": get_ship_docs,
    "force_system_login": force_system_login,
}


async def handle_function_call(name: str, args: Dict[str, Any]):
    """The core router for all function calls."""
    function = function_map.get(name)
    if function is None:
        raise ValueError(f"Function {name} not found")
    return await function(**args)
