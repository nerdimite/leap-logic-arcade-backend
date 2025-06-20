from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException

from arcade.api.schemas.request import (
    AgentStateUpdateRequest,
    AgentToolRequest,
    ChatMessageRequest,
)
from arcade.api.schemas.response import ChatMessageResponse, SuccessResponse
from arcade.core.commons.logger import get_logger
from arcade.core.dao import PubgGameDao
from arcade.services.pubg.admin_service import AdminService
from arcade.services.pubg.agent_service import AgentService
from arcade.services.pubg.chat_service import ChatService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/pubg", tags=["pubg"])


def get_agent_service() -> AgentService:
    return AgentService()


def get_chat_service() -> ChatService:
    return ChatService()


def get_pubg_game_dao() -> PubgGameDao:
    return PubgGameDao()


def get_admin_service() -> AdminService:
    return AdminService()


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
    return agent_service.get_agent_state(team_name=team_name)


@router.get("/game-state")
async def get_game_state(
    team_name: str = Header(..., description="Name of the team"),
    game_dao: PubgGameDao = Depends(get_pubg_game_dao),
) -> Dict:
    """Get the current game state for a team.

    Args:
        team_name: Team name from header
        game_dao: Injected game DAO

    Returns:
        Current game state including system access, power distribution, and mission status
    """
    game_state = game_dao.get_team_game_state(team_name=team_name)
    if not game_state:
        raise HTTPException(
            status_code=404,
            detail=f"Game state not found for team {team_name}. The team may need to be initialized.",
        )
    return game_state


@router.get("/leaderboard")
async def get_leaderboard(
    admin_service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    """Get the leaderboard for all teams.

    Returns:
        Dict containing 'leaderboard' (list of completed teams sorted by completion time)
        and 'pending_teams' (list of teams that haven't completed the mission)
    """
    return admin_service.get_leaderboard()


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
    agent_service.update_agent_config(
        team_name=team_name,
        system_message=update.system_message,
        temperature=update.temperature,
        last_response_id=update.last_response_id,
    )
    return SuccessResponse(message="Agent state updated successfully")


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
    agent_service.add_agent_tool(
        team_name=team_name, tool_name=tool.tool_name, description=tool.description
    )
    return SuccessResponse(message="Tool added successfully")


@router.patch("/agent/tool")
async def update_agent_tool(
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
    agent_service.add_agent_tool(
        team_name=team_name, tool_name=tool.tool_name, description=tool.description
    )
    return SuccessResponse(message="Tool updated successfully")


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
    agent_service.delete_agent_tool(team_name=team_name, tool_name=tool_name)
    return SuccessResponse(message="Tool deleted successfully")


@router.get("/agent/tool")
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
    return agent_service.get_agent_tools(team_name=team_name)


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
    return agent_service.get_available_tools()


@router.post("/agent/chat", response_model=ChatMessageResponse)
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
    message = {"role": "user", "content": request.message}
    response = await chat_service.send_message(team_name=team_name, message=message)
    return ChatMessageResponse(response=response)


@router.get("/agent/chat")
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
    return await chat_service.get_chat_history(team_name=team_name)


@router.get("/challenge-status")
async def get_challenge_status(
    admin_service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    """Get the current state of the PUBG challenge.

    Returns:
        Dict containing 'status' (current state of the challenge)
    """
    return admin_service.state_dao.get_challenge_state(admin_service.CHALLENGE_ID)
