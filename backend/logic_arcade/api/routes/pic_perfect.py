from typing import Optional

from fastapi import APIRouter, Header

from logic_arcade.api.schemas.request import SubmitRequest
from logic_arcade.core.commons.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/pic-perfect", tags=["pic-perfect"])


@router.post("/submit")
async def submit_pic(
    request: SubmitRequest, team_name: Optional[str] = Header(None, alias="team-name")
):
    logger.info(f"Received request: {request}")
    logger.info(f"Team name: {team_name}")

    # Mock response for now
    return {
        "status": "success",
        "message": "Image submitted successfully",
        "team_name": team_name,
        "data": {
            "image_url": request.image_url,
            "prompt": request.prompt,
            "score": 85,  # Mock score
        },
    }
