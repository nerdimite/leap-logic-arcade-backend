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


TOOLS = [
    generate_function_schema(GetCrewLogsArgs),
    generate_function_schema(GetShipDocsArgs),
    generate_function_schema(ForceSystemLoginArgs),
]
