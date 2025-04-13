from typing import Optional

from fastapi import APIRouter, Depends, Header

from arcade.api.schemas.request import (
    StartChallengeRequest,
    SubmitRequest,
    TransitionStateRequest,
)
from arcade.core.commons.logger import get_logger
from arcade.core.dao.images_dao import ImagesDao
from arcade.core.dao.leaderboard_dao import LeaderboardDao
from arcade.core.dao.state_dao import StateDao
from arcade.core.dao.teams_dao import TeamsDao
from arcade.services.pic_perfect.admin import PicPerfectAdminService
from arcade.types import ChallengeState

logger = get_logger(__name__)

router = APIRouter(prefix="/pic-perfect/admin", tags=["pic-perfect-admin"])


def get_pic_perfect_admin_service() -> PicPerfectAdminService:
    """Dependency injection for PicPerfectAdminService."""
    return PicPerfectAdminService(
        images_dao=ImagesDao(),
        state_dao=StateDao(),
        leaderboard_dao=LeaderboardDao(),
        teams_dao=TeamsDao(),
    )


@router.post("/start")
async def start_challenge(
    request: StartChallengeRequest,
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Start the challenge and set the hidden image."""
    result = service.start_challenge(request.image_url, request.prompt, request.config)
    return result


@router.post("/hidden-image")
async def submit_hidden_image(
    request: SubmitRequest,
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Submit the hidden original image."""
    result = service.submit_hidden_image(request.image_url, request.prompt)
    return result


@router.post("/transition")
async def transition_state(
    request: TransitionStateRequest,
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Transition the challenge to a new state."""
    try:
        target_state = ChallengeState(request.target_state)
        result = service.transition_challenge_state(target_state)
        return result
    except ValueError as e:
        return {"success": False, "message": str(e)}


@router.post("/calculate-scores")
async def calculate_scores(
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Calculate scores for all teams based on voting results."""
    result = service.calculate_scores()
    return {"success": True, "scores": result}


@router.post("/finalize")
async def finalize_challenge(
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Finalize the challenge and calculate final scores."""
    result = service.finalize_challenge()
    return result


@router.get("/submission-status")
async def get_submission_status(
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Get the status of team submissions.

    Returns:
        Dict containing:
        - Number of teams that have submitted
        - Total number of teams
        - List of teams that haven't submitted yet
        - Whether the challenge can transition to voting phase
    """
    result = service.get_submission_status()
    return result


@router.get("/voting-status")
async def get_voting_status(
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Get the status of team voting.

    Returns:
        Dict containing:
        - Number of teams that have completed voting
        - Total number of participating teams
        - List of teams that haven't completed voting
        - Whether the challenge can transition to scoring phase
    """
    result = service.get_voting_status()
    return result


@router.post("/reset")
async def clean_reset(
    service: PicPerfectAdminService = Depends(get_pic_perfect_admin_service),
):
    """Reset all challenge data by deleting all entries from tables.

    This will:
    - Delete all submitted images (including hidden image)
    - Reset the leaderboard
    - Reset challenge state
    - Keep team registrations intact
    """
    result = service.clean_reset()
    return result
