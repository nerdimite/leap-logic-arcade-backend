from typing import List, Optional

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """Standard success response model."""

    success: bool = Field(True, description="Whether the operation was successful")
    message: str = Field(..., description="Success message")


class CleanAgentsResponse(BaseModel):
    """Response model for clean agents operation."""

    status: str = Field(..., description="Operation status (success/partial_success)")
    cleaned_count: int = Field(..., description="Number of agents cleaned")
    errors: Optional[List[str]] = Field(
        None, description="List of errors if any occurred"
    )


class ChatMessageResponse(BaseModel):
    """Response model for agent chat messages."""
    
    response: str = Field(..., description="Response from the agent")
