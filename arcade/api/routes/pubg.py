from typing import Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException

from arcade.api.schemas.request import AgentStateUpdateRequest, AgentToolRequest
from arcade.api.schemas.response import SuccessResponse
from arcade.services.pubg.agent_service import AgentService

router = APIRouter(prefix="/api/pubg", tags=["pubg"])


def get_agent_service() -> AgentService:
    return AgentService()


@router.get("/agent/state")
async def get_agent_state(
    team_name: str = Header(..., description="Name of the team"),
    agent_service: AgentService = Depends(get_agent_service),
) -> Dict:
    """Get the current state of an agent.

    Args:
        team_name: Team name from header
        agent_service: Injected agent service

    Returns:
        Current agent state including configuration and tools
    """
    try:
        return agent_service.get_agent_state(team_name=team_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/agent/state")
async def update_agent_state(
    update: AgentStateUpdateRequest,
    team_name: str = Header(..., description="Name of the team"),
    agent_service: AgentService = Depends(get_agent_service),
) -> SuccessResponse:
    """Update the AI agent state for a team.

    Args:
        update: State update parameters
        team_name: Team name from header
        agent_service: Injected agent service

    Returns:
        Success response
    """
    try:
        agent_service.update_agent_config(
            team_name=team_name,
            system_message=update.system_message,
            temperature=update.temperature,
            last_response_id=update.last_response_id,
        )
        return SuccessResponse(message="Agent state updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/tool")
async def add_agent_tool(
    tool: AgentToolRequest,
    team_name: str = Header(..., description="Name of the team"),
    agent_service: AgentService = Depends(get_agent_service),
) -> SuccessResponse:
    """Add a tool to the AI agent.

    Args:
        tool: Tool configuration to add
        team_name: Team name from header
        agent_service: Injected agent service

    Returns:
        Success response
    """
    try:
        agent_service.add_agent_tool(
            team_name=team_name, tool_name=tool.tool_name, description=tool.description
        )
        return SuccessResponse(message="Tool added successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agent/tool/{tool_name}")
async def delete_agent_tool(
    tool_name: str,
    team_name: str = Header(..., description="Name of the team"),
    agent_service: AgentService = Depends(get_agent_service),
) -> SuccessResponse:
    """Delete a tool from the AI agent.

    Args:
        tool_name: Name of the tool to delete
        team_name: Team name from header
        agent_service: Injected agent service

    Returns:
        Success response
    """
    try:
        agent_service.delete_agent_tool(team_name=team_name, tool_name=tool_name)
        return SuccessResponse(message="Tool deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/tools")
async def get_agent_tools(
    team_name: str = Header(..., description="Name of the team"),
    agent_service: AgentService = Depends(get_agent_service),
) -> List[Dict[str, str]]:
    """Get all tools available for an agent.

    Args:
        team_name: Team name from header
        agent_service: Injected agent service

    Returns:
        List of tool configurations
    """
    try:
        return agent_service.get_agent_tools(team_name=team_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
