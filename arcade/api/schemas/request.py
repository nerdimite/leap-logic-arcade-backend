from typing import List, Optional

from pydantic import BaseModel


class TeamRegistrationRequest(BaseModel):
    """Schema for team registration request."""

    team_name: str
    members: List[str] = []  # Will be converted to Set in the handler


class SubmitRequest(BaseModel):
    image_url: str
    prompt: str


class VoteRequest(BaseModel):
    voted_teams: List[str]


class StartChallengeRequest(BaseModel):
    image_url: str
    prompt: str
    config: Optional[dict] = None


class TransitionStateRequest(BaseModel):
    target_state: str
