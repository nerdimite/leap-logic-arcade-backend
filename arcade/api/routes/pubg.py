from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException

from arcade.api.schemas.request import (
    AgentStateUpdateRequest,
    AgentToolRequest,
    ChatMessageRequest,
)
from arcade.api.schemas.response import ChatMessageResponse, SuccessResponse
from arcade.services.pubg.agent_service import AgentService
from arcade.services.pubg.chat_service import ChatService

router = APIRouter(prefix="/api/pubg", tags=["pubg"])


def get_agent_service() -> AgentService:
    return AgentService()


def get_chat_service() -> ChatService:
    return ChatService()


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
) -> List[Dict[str, Any]]:
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


@router.get("/agent/available-tools")
async def get_available_tools(
    agent_service: AgentService = Depends(get_agent_service),
) -> List[Dict[str, Any]]:
    """Get all available tools that can be added to agents.

    Args:
        agent_service: Injected agent service

    Returns:
        List of all available tool configurations
    """
    try:
        return agent_service.get_available_tools()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    team_name: str = Header(..., description="Name of the team"),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatMessageResponse:
    """Send a message to the AI agent.

    Args:
        request: Request containing the message
        team_name: Team name from header
        chat_service: Injected chat service

    Returns:
        Agent's response
    """
    try:
        message = {"role": "user", "content": request.message}
        response = await chat_service.send_message(team_name=team_name, message=message)
        return ChatMessageResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/chat/history")
async def get_chat_history(
    team_name: str = Header(..., description="Name of the team"),
    chat_service: ChatService = Depends(get_chat_service),
) -> List[Dict[str, Any]]:
    """Get the chat history for a team.

    Args:
        team_name: Team name from header
        chat_service: Injected chat service

    Returns:
        List of chat messages
    """
    try:
        return await chat_service.get_chat_history(team_name=team_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
