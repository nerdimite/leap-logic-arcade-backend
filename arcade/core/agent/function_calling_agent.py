import json
from typing import Any, Callable, Dict, List, Optional

import openai
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from arcade.core.commons.logger import get_logger

logger = get_logger(__name__)


class FunctionCallingAgent:
    """
    An agent that can call functions based on LLM responses.

    This agent uses OpenAI's function calling capability to execute tools
    and manage conversation flow with tool execution.
    """

    def __init__(
        self,
        callback_function: Callable,
        model: str = "gpt-4o-mini",
        temperature: float = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        max_tool_calls: int = 2,
    ):
        """Initialize the function calling agent.

        Args:
            model: The OpenAI model to use
            temperature: Sampling temperature
            tools: List of tools/functions available to the agent
            instructions: System instructions for the agent
            previous_response_id: ID of a previous response to continue from
            max_tool_calls: Maximum number of tool calls allowed in a single turn
            callback_function: Callback function to handle tool execution. Make sure it is async and returns a string.
        """
        self.client = AsyncOpenAI()

        self.model = model
        self.temperature = temperature
        self.tools = tools
        self.instructions = instructions
        self.previous_response_id = previous_response_id

        self.callback_function = callback_function
        self.max_tool_calls = max_tool_calls

    async def _handle_tool_calls(self, tool_calls) -> Any:
        """
        Process tool calls from the model response.

        Args:
            tool_calls: List of tool call objects from the model

        Returns:
            List of tool results to be sent back to the model
        """
        tool_results = []
        for tool_call in tool_calls:
            if tool_call.type != "function_call":
                continue

            name = tool_call.name
            args = json.loads(tool_call.arguments)

            result = (
                await self.callback_function(name, args)
                if callable(self.callback_function)
                else None
            )
            logger.info(f"Function {name} called with args {args} and result {result}")

            tool_results.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": str(result),
                }
            )

        return tool_results

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    async def send_message(self, message: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Send a message to the model and handle any function calls.

        Args:
            message: The message to send to the model
            **kwargs: Additional parameters to override default settings

        Returns:
            The final response from the model after all function calls are processed
        """
        # resolve kwargs with default values
        params = {
            "previous_response_id": self.previous_response_id,
            "model": self.model,
            "temperature": self.temperature,
            "tools": self.tools,
            "instructions": self.instructions,
        }
        params.update(kwargs)

        messages = []
        if message:
            messages.append(message)

        tool_calls_remaining = self.max_tool_calls

        while tool_calls_remaining > 0:
            response = await self.client.responses.create(input=messages, **params)
            messages.extend(response.output)

            if not response.output or response.output[0].type != "function_call":
                break

            tool_results = await self._handle_tool_calls(response.output)
            messages.extend(tool_results)

            tool_calls_remaining -= 1
        else:
            logger.error(f"Exceeded max tool calls: {self.max_tool_calls}")
            return None, "Sorry, I exceeded the maximum number of tool calls I could make. Please try again."

        self.last_response_id = response.id

        output_text = response.output[0].content[0].text
        logger.info(output_text)

        return response, output_text

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    async def retrieve_chat_history(
        self, last_response_id: str, simplified: bool = True
    ):
        """
        Retrieve chat history from a previous response.

        Args:
            last_response_id: The ID of the response to retrieve history from
            simplified: Whether to return simplified message objects or raw API objects

        Returns:
            List of message objects representing the chat history
        """
        messages = []

        response_data = await self.client.responses.retrieve(last_response_id)
        system_message = {
            "role": "system",
            "content": response_data.instructions,
        }

        input_items = await self.client.responses.input_items.list(
            last_response_id, limit=100
        )
        for item in input_items.data:
            messages.append(item)
        messages = messages[::-1]

        response_output = await self.client.responses.retrieve(
            response_id=last_response_id
        )
        messages.extend(response_output.output)

        if simplified:
            dict_messages = []
            for item in messages:
                if item.type == "message":
                    dict_messages.append(
                        {
                            "role": item.role,
                            "content": item.content[0].text,
                            "type": "message",
                        }
                    )
                elif item.type == "function_call":
                    dict_messages.append(
                        {
                            "type": "function_call",
                            "name": item.name,
                            "arguments": item.arguments,
                            "call_id": item.call_id,
                        }
                    )
                elif item.type == "function_call_output":
                    dict_messages.append(
                        {
                            "type": "function_call_output",
                            "output": item.output,
                            "call_id": item.call_id,
                        }
                    )
            return [system_message] + dict_messages
        else:
            return [system_message] + messages
