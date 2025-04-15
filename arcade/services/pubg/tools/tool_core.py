import re
from pathlib import Path
from typing import Optional

from arcade.config.constants import OVERRIDE_CODE
from arcade.core.dao import PubgGameDao

CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR / "data"


async def get_crew_logs(**kwargs) -> str:
    """Get the crew logs.

    Returns:
        The crew logs.
    """
    with open(DATA_DIR / "crew_logs.log", "r") as f:
        return f.read()


async def get_ship_docs(section_num: Optional[int] = None, **kwargs) -> str:
    """Get the ship docs.

    Args:
        section_num: The section number to get. If None, the table of contents is returned.

    Returns:
        The ship docs.
    """
    if section_num is None:
        with open(DATA_DIR / "ship_docs_index.md", "r") as f:
            return f.read()

    if section_num is not None and (section_num < 1 or section_num > 4):
        raise ValueError("Section number must be between 1 and 4")

    with open(DATA_DIR / "ship_docs.md", "r") as f:
        docs = f.read()
        # Skip the first h1 line
        docs = docs.split("\n", 1)[1] if "\n" in docs else docs

    # Find all H2 headers in the document
    h2_headers = re.findall(r"^## .+$", docs, flags=re.MULTILINE)

    # Initialize dictionary to store sections
    h2_sections = []

    # For each H2 header, extract content until the next H2 header
    for i in range(len(h2_headers)):
        header = h2_headers[i]

        # Find the start position of current header
        start_pos = docs.find(header)

        # Find the end position (next H2 header or end of document)
        if i < len(h2_headers) - 1:
            end_pos = docs.find(h2_headers[i + 1], start_pos)
        else:
            end_pos = len(docs)

        # Extract content between current header and next header
        content = docs[start_pos:end_pos].strip()

        # Store in list - no need to add header again as it's already in the content
        h2_sections.append(content)

    return h2_sections[section_num - 1]


async def force_system_login(override_code: str, **kwargs) -> bool:
    """Force a system login using an override code.

    Args:
        override_code: The override code.

    Returns:
        True if the login was successful, False otherwise.
    """
    normalized_override_code = re.sub(r"[^a-z0-9]", "", override_code.lower())
    normalized_real_override_code = re.sub(r"[^a-z0-9]", "", OVERRIDE_CODE.lower())

    pubg_game_dao = PubgGameDao()
    team_name = kwargs["team_name"]

    pubg_game_dao.set_system_access(team_name, True)

    return {
        "success": normalized_override_code == normalized_real_override_code,
        "message": (
            "Login successful"
            if normalized_override_code == normalized_real_override_code
            else "Login failed"
        ),
    }
