from typing import Optional

from fastapi import APIRouter, Depends, Header

from arcade.api.schemas.request import SubmitRequest, VoteRequest
from arcade.core.commons.logger import get_logger
from arcade.core.commons.utils import hash_team_name, is_hashed_team_name
from arcade.core.dao.images_dao import ImagesDao
from arcade.core.dao.leaderboard_dao import LeaderboardDao
from arcade.core.dao.state_dao import StateDao
from arcade.core.dao.teams_dao import TeamsDao
from arcade.services.pic_perfect.admin import PicPerfectAdminService
from arcade.services.pic_perfect.main import PicPerfectService

logger = get_logger(__name__)

router = APIRouter(prefix="/pic-perfect", tags=["pic-perfect"])


def get_pic_perfect_service() -> PicPerfectService:
    """Dependency injection for PicPerfectService."""
    return PicPerfectService(
        images_dao=ImagesDao(),
        state_dao=StateDao(),
        leaderboard_dao=LeaderboardDao(),
        teams_dao=TeamsDao(),
    )


@router.post("/submit")
async def submit_pic(
    request: SubmitRequest,
    team_name: Optional[str] = Header(None, alias="team-name"),
    service: PicPerfectService = Depends(get_pic_perfect_service),
):
    """Submit a team's generated image."""
    if not team_name:
        return {"status": "error", "message": "Team name is required"}

    result = service.submit_team_image(team_name, request.image_url, request.prompt)
    return result


@router.post("/vote")
async def cast_votes(
    request: VoteRequest,
    team_name: Optional[str] = Header(None, alias="team-name"),
    service: PicPerfectService = Depends(get_pic_perfect_service),
):
    """Cast votes for other teams' images."""
    if not team_name:
        return {"status": "error", "message": "Team name is required"}

    voted_teams = []
    for voted_team in request.voted_teams:
        if is_hashed_team_name(voted_team):
            voted_teams.append(service.teams_dao.get_team_by_hash(voted_team))
        else:
            voted_teams.append(voted_team)

    result = service.cast_votes(team_name, voted_teams)
    return result


@router.get("/voting-pool")
async def get_voting_pool(
    team_name: Optional[str] = Header(None, alias="team-name"),
    service: PicPerfectService = Depends(get_pic_perfect_service),
):
    """Get all images available for voting."""
    if not team_name:
        return {"status": "error", "message": "Team name is required"}

    result = service.get_voting_pool(team_name)

    # Convert teamName to hashedTeamName for anonymity so that end users don't know which one is the hidden image
    voting_pool = []
    for image in result:
        voting_pool.append(
            {
                "teamName": hash_team_name(image["teamName"]),
                "imageUrl": image["imageUrl"],
            }
        )

    return {"status": "success", "voting_pool": voting_pool}


@router.get("/team-status")
async def get_team_status(
    team_name: Optional[str] = Header(None, alias="team-name"),
    service: PicPerfectService = Depends(get_pic_perfect_service),
):
    """Get a team's current submission and voting status."""
    if not team_name:
        return {"status": "error", "message": "Team name is required"}

    result = service.get_team_status(team_name)
    return result


@router.get("/leaderboard")
async def get_leaderboard(
    service: PicPerfectService = Depends(get_pic_perfect_service),
):
    """Get the current leaderboard with team rankings and scores."""
    result = service.get_leaderboard()
    return result


@router.get("/status")
async def get_challenge_status(
    service: PicPerfectService = Depends(get_pic_perfect_service),
):
    """Get the current challenge status.

    Returns:
        Dict containing:
        - Current challenge state
    """
    # Get challenge state
    challenge_state = service.state_dao.get_challenge_state(service.challenge_id)
    current_state = challenge_state.get("state") if challenge_state else None

    return {"status": "success", "challenge_state": current_state}
