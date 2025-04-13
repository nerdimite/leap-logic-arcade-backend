from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, List, Optional, TypedDict, Union

from openai.types.chat import ChatCompletion, ChatCompletionChunk
from pydantic import BaseModel


class BaseChatMessage(TypedDict):
    role: str
    content: str


class LLMConfig(BaseModel):
    """Configuration for LLM providers"""

    model: str
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    streaming: bool = False
    additional_kwargs: dict = {}


class LLMProvider(ABC):
    """Abstract base class defining the interface for LLM providers"""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def chat_completion(
        self,
        messages: List[BaseChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = None,
        **kwargs: Any
    ) -> ChatCompletion:
        """
        Synchronous chat completion.

        Args:
            messages: List of chat messages
            model: Model to use (overrides config)
            temperature: Temperature setting (overrides config)
            max_tokens: Max tokens to generate (overrides config)
            stream: Whether to stream responses (overrides config)
            **kwargs: Additional arguments for the specific implementation

        Returns:
            ChatCompletion response
        """
        pass

    @abstractmethod
    async def achat_completion(
        self,
        messages: List[BaseChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = None,
        **kwargs: Any
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        """
        Asynchronous chat completion.

        Args:
            messages: List of chat messages
            model: Model to use (overrides config)
            temperature: Temperature setting (overrides config)
            max_tokens: Max tokens to generate (overrides config)
            stream: Whether to stream responses (overrides config)
            **kwargs: Additional arguments for the specific implementation

        Returns:
            ChatCompletion response or AsyncIterator of ChatCompletionChunks if streaming
        """
        pass
