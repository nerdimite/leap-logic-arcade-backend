from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from arcade.api.schemas.response import (
    CleanAgentsResponse,
    CleanTeamDataResponse,
    SuccessResponse,
)
from arcade.services.pubg.admin_service import AdminService

router = APIRouter(prefix="/api/admin/pubg", tags=["pubg-admin"])


def get_admin_agent_service() -> AdminService:
    return AdminService()


@router.post("/agent/initialize/{team_name}")
async def initialize_team_agent(
    team_name: str, admin_service: AdminService = Depends(get_admin_agent_service)
) -> SuccessResponse:
    """Initialize an agent for a specific team with default configuration.

    Args:
        team_name: Name of the team to initialize
        admin_service: Injected admin service

    Returns:
        Success response
    """
    try:
        admin_service.initialize_team_agent(team_name)
        return SuccessResponse(
            message=f"Agent initialized successfully for team {team_name}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def initialize_all_teams(
    admin_service: AdminService = Depends(get_admin_agent_service),
) -> Dict[str, str]:
    """Initialize agents and game states for all teams that don't have them yet.

    Args:
        admin_service: Injected admin service

    Returns:
        Dict mapping team names to initialization status
    """
    try:
        return admin_service.initialize_challenge()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/reset/{team_name}")
async def reset_team_agent(
    team_name: str, admin_service: AdminService = Depends(get_admin_agent_service)
) -> SuccessResponse:
    """Reset an agent to default configuration.

    Args:
        team_name: Name of the team whose agent to reset
        admin_service: Injected admin service

    Returns:
        Success response
    """
    try:
        admin_service.reset_team_agent(team_name)
        return SuccessResponse(message=f"Agent reset successfully for team {team_name}")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/game-state/reset/{team_name}")
async def reset_team_game_state(
    team_name: str, admin_service: AdminService = Depends(get_admin_agent_service)
) -> SuccessResponse:
    """Reset a team's game state to initial values.

    Args:
        team_name: Name of the team whose game state to reset
        admin_service: Injected admin service

    Returns:
        Success response
    """
    try:
        admin_service.reset_team_game_state(team_name)
        return SuccessResponse(
            message=f"Game state reset successfully for team {team_name}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-all")
async def reset_all_teams(
    admin_service: AdminService = Depends(get_admin_agent_service),
) -> Dict[str, str]:
    """Reset all teams' agents and game states to initial configuration.

    Args:
        admin_service: Injected admin service

    Returns:
        Dict mapping team names to reset status
    """
    try:
        return admin_service.reset_all_teams()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uninitialized")
async def get_uninitialized_teams(
    admin_service: AdminService = Depends(get_admin_agent_service),
) -> List[str]:
    """Get list of teams that don't have initialized agents or game states.

    Args:
        admin_service: Injected admin service

    Returns:
        List of team names without initialized agents or game states
    """
    try:
        return admin_service.get_uninitialized_teams()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clean-all", response_model=CleanTeamDataResponse)
async def clean_all_team_data(
    admin_service: AdminService = Depends(get_admin_agent_service),
) -> Dict[str, Any]:
    """Clean/reset all team data by deleting agent configurations and game states.

    WARNING: This is a destructive operation that will remove all agent configurations and game states.
    Teams will need to be reinitialized after this operation.

    Args:
        admin_service: Injected admin service

    Returns:
        Status of the operation including count of cleaned records and any errors
    """
    try:
        return admin_service.clean_all_team_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
