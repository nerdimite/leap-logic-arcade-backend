import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from arcade.config.constants import DEFAULT_MODEL
from arcade.core.agent.function_calling_agent import FunctionCallingAgent
from arcade.core.dao.agents_dao import AgentsDao
from arcade.services.pubg.tools import handle_function_call

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for handling chat interactions with LLM-powered agents.
    Maintains conversation history using DynamoDB and provides methods
    for sending messages and retrieving chat history.
    """

    def __init__(self, callback_function: Callable = handle_function_call):
        """
        Initialize the chat service.

        Args:
            callback_function: Function to handle tool/function executions
        """
        self.agents_dao = AgentsDao()
        self.callback_function = callback_function

    async def send_message(
        self,
        team_name: str,
        message: Dict[str, Any],
        model: Optional[str] = DEFAULT_MODEL,
        temperature: Optional[float] = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[str] = None,
    ) -> Tuple[Any, str]:
        """
        Send a message to the agent and update the conversation history.

        Args:
            team_name: The team associated with this conversation
            message: The message to send
            model: The model to use
            temperature: Temperature for sampling
            tools: List of tools available to the agent
            instructions: System instructions

        Returns:
            Tuple of (full_response, text_response)
        """
        # Get agent state from DAO
        agent_state = self.agents_dao.get_agent_state(team_name)

        # Use stored values if not provided in the call
        if temperature is None and "temperature" in agent_state:
            temperature = agent_state.get("temperature")

        if instructions is None and "instructions" in agent_state:
            instructions = agent_state.get("instructions")

        if tools is None and "tools" in agent_state:
            tools = agent_state.get("tools")

        # Get previous response ID if available
        previous_response_id = agent_state.get("previousResponseId")
        if previous_response_id == "":
            previous_response_id = None

        # Create agent with previous response ID
        agent = FunctionCallingAgent(
            team_name=team_name,
            callback_function=self.callback_function,
            model=model,
            temperature=temperature,
            tools=tools,
            instructions=instructions,
            previous_response_id=previous_response_id,
        )

        # Send message
        response, output_text = await agent.send_message(message)

        # Update previous response ID in DAO
        if response:
            self.agents_dao.update_previous_response_id(team_name, response.id)

        return output_text

    async def get_chat_history(
        self, team_name: str, simplified: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the chat history for a team.

        Args:
            team_name: The team to get history for
            simplified: Whether to return simplified message objects

        Returns:
            List of chat messages
        """
        # Get previous response ID from DAO
        agent_state = self.agents_dao.get_agent_state(team_name)
        previous_response_id = agent_state.get("previousResponseId")

        if not previous_response_id:
            return []

        # Create temporary agent just to access history
        agent = FunctionCallingAgent(
            callback_function=self.callback_function,
        )

        # Retrieve chat history
        return await agent.retrieve_chat_history(
            previous_response_id, simplified=simplified
        )
