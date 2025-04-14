from typing import List, Optional

from pydantic import BaseModel, Field

from arcade.types import ChallengeState


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
    target_state: ChallengeState


class AgentStateUpdateRequest(BaseModel):
    """Request model for updating agent state."""

    system_message: Optional[str] = Field(
        None, description="System message/instructions for the agent"
    )
    temperature: Optional[float] = Field(
        None, description="Temperature value for agent responses", ge=0, le=1
    )
    last_response_id: Optional[str] = Field(
        None, description="ID of the last response from the agent"
    )


class AgentToolRequest(BaseModel):
    """Request model for adding a tool."""

    tool_name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool")


class ChatMessageRequest(BaseModel):
    """Request model for sending messages to the agent."""

    message: str = Field(..., description="Message to send to the agent")
