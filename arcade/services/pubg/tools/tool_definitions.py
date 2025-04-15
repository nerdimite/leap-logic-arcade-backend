from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from arcade.core.agent import generate_function_schema


class GetCrewLogsArgs(BaseModel):
    """Get the crew logs."""

    model_config = ConfigDict(title="get_crew_logs")


class GetShipDocsArgs(BaseModel):
    """Get the ship docs. If section_num is provided, the specific section is returned else the table of contents is returned."""

    section_num: Optional[int]

    model_config = ConfigDict(title="get_ship_docs")


class ForceSystemLoginArgs(BaseModel):
    """Force a system login using an override code."""

    override_code: str

    model_config = ConfigDict(title="force_system_login")


class SystemDatabaseArgs(BaseModel):
    """Execute a SQL query on the ship database."""

    sql_query: str

    model_config = ConfigDict(title="system_database")


class SystemPower(BaseModel):
    """A system and the power it is currently using."""

    system_name: str
    current_power: float


class UpdatePowerDistributionArgs(BaseModel):
    """Update the power distribution on the ship."""

    updates: List[SystemPower]

    model_config = ConfigDict(title="update_power_distribution")


class GetCurrentPowerDistributionArgs(BaseModel):
    """Get the current power distribution on the ship."""

    model_config = ConfigDict(title="get_current_power_distribution")


class GetRegionMapArgs(BaseModel):
    """Get the region map."""

    model_config = ConfigDict(title="get_region_map")


class GetCurrentPositionArgs(BaseModel):
    """Get the current position and velocity of the ship."""

    model_config = ConfigDict(title="get_current_position")


class DavinciCoderArgs(BaseModel):
    """Execute a code snippet and return the output in a stateless sandbox.

    This is a stateless code execution sandbox that only persists for the duration of the execution.
    Beyond the basic Python libraries, it has access to the following preloaded modules:
    - math: Available without importing
    - numpy: Available without importing
    - scipy: Available without importing

    You don't need to import these libraries in your code as they are already preloaded.
    There's a limit of 10 seconds for the execution of the code.
    You might wanna use print statements to view the output of the code.
    Args:
        code: The Python code snippet to execute.

    Returns:
        The output of the code execution as a string."""

    code: str

    model_config = ConfigDict(title="davinci_coder")


class SetNavigationCourseArgs(BaseModel):
    """Set the course for the ship to navigate to the target coordinates."""

    target_coordinates: List[int]

    model_config = ConfigDict(title="set_navigation_course")


class SetEngineThrustArgs(BaseModel):
    """Set the thrust for the ship to navigate to the target coordinates."""

    thrust: float
    thrust_direction: List[int]

    model_config = ConfigDict(title="set_engine_thrust")


class StartEnginesArgs(BaseModel):
    """Start the engines and bon voyage."""

    model_config = ConfigDict(title="start_engines")


TOOLS = [
    generate_function_schema(GetCrewLogsArgs),
    generate_function_schema(GetShipDocsArgs),
    generate_function_schema(ForceSystemLoginArgs),
    generate_function_schema(SystemDatabaseArgs),
    generate_function_schema(UpdatePowerDistributionArgs),
    generate_function_schema(GetCurrentPowerDistributionArgs),
    generate_function_schema(GetRegionMapArgs),
    generate_function_schema(GetCurrentPositionArgs),
    generate_function_schema(DavinciCoderArgs),
    generate_function_schema(SetNavigationCourseArgs),
    generate_function_schema(SetEngineThrustArgs),
    generate_function_schema(StartEnginesArgs),
]
