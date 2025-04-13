from datetime import datetime
from typing import Set

import pytz
from fastapi import APIRouter, HTTPException

from arcade.api.schemas.request import TeamRegistrationRequest
from arcade.core.commons.logger import get_logger
from arcade.core.dao.teams_dao import TeamsDao

logger = get_logger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/register")
async def register_team(request: TeamRegistrationRequest):
    """Register a new team.

    Args:
        request: Team registration details including team name and optional members

    Returns:
        Dict containing registration status and timestamp

    Raises:
        HTTPException: If team name already exists or registration fails
    """
    try:
        teams_dao = TeamsDao()

        # Convert list to set for members
        members: Set[str] = set(request.members) if request.members else None

        # Register team using TeamsDao's register_team method
        success = teams_dao.register_team(request.team_name, members)

        # Get the registered team details
        team = teams_dao.get_team(request.team_name)

        return {
            "status": "success",
            "message": "Team registered successfully",
            "team_name": request.team_name,
            "timestamp": team.get("createdAt"),
            "members": list(team.get("members", set())) if team.get("members") else [],
        }

    except ValueError as e:
        # Handle case where team already exists
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering team: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{team_name}")
async def get_team_info(team_name: str):
    """Get information about a specific team.

    Args:
        team_name: Name of the team to look up

    Returns:
        Dict containing team details if found

    Raises:
        HTTPException: If team not found or lookup fails
    """
    try:
        teams_dao = TeamsDao()
        team = teams_dao.get_team(team_name)

        if not team:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

        # Convert members set to list for response
        members = list(team.get("members", set())) if team.get("members") else []
        if "PLACEHOLDER" in members:
            members.remove("PLACEHOLDER")

        return {
            "status": "success",
            "team": {
                "teamName": team.get("teamName"),
                "members": members,
                "createdAt": team.get("createdAt"),
                "lastActive": team.get("lastActive"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
