import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

import openai
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from logic_arcade.core.commons.logger import get_logger
from logic_arcade.core.interfaces.llm import BaseChatMessage, LLMProvider

logger = get_logger("openai")


class OpenAIError(Exception):
    """Base exception class for OpenAI API errors"""

    pass


def get_openai_retry_decorator():
    """Get OpenAI-specific retry decorator"""
    return retry(
        retry=retry_if_exception_type((openai.RateLimitError)),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
    )


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLM provider interface"""

    def __init__(self, api_key: Optional[str] = None):
        self.sync_client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)

    def _prepare_params(
        self,
        messages: List[BaseChatMessage],
        model: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Prepare parameters for API call"""
        params = {
            "model": model,
            "messages": messages,
            **kwargs,
        }
        return params

    @get_openai_retry_decorator()
    def chat_completion(
        self,
        messages: List[BaseChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Synchronous chat completion"""
        try:
            params = self._prepare_params(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )
            return self.sync_client.chat.completions.create(**params)
        except (openai.RateLimitError, openai.APIError, openai.APIConnectionError) as e:
            raise e
        except Exception as e:
            raise OpenAIError(f"Error calling OpenAI API: {str(e)}")

    @get_openai_retry_decorator()
    async def achat_completion(
        self,
        messages: List[BaseChatMessage],
        model: str,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatCompletion | AsyncIterator[ChatCompletionChunk]:
        """Asynchronous chat completion"""
        try:
            params = self._prepare_params(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )
            return await self.async_client.chat.completions.create(**params)
        except (openai.RateLimitError, openai.APIError, openai.APIConnectionError) as e:
            raise e
        except Exception as e:
            raise OpenAIError(f"Error calling OpenAI API: {str(e)}")

    @get_openai_retry_decorator()
    def chat_completion_structured(
        self,
        messages: List[BaseChatMessage],
        model: str,
        response_format: Any,
        **kwargs: Any,
    ) -> Any:
        """Synchronous structured chat completion that returns parsed responses

        Args:
            messages: List of messages representing a conversation
            model: The model to use for completion
            response_format: The Pydantic model to parse the response into
            **kwargs: Additional keyword arguments
        """
        try:
            params = self._prepare_params(
                messages=messages,
                model=model,
                **kwargs,
            )
            return self.sync_client.beta.chat.completions.parse(
                response_format=response_format, **params
            )
        except (openai.RateLimitError, openai.APIError, openai.APIConnectionError) as e:
            raise e
        except Exception as e:
            raise OpenAIError(f"Error calling OpenAI API: {str(e)}")

    @get_openai_retry_decorator()
    async def achat_structured_completion(
        self,
        messages: List[BaseChatMessage],
        model: str,
        response_format: Any,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """Asynchronous structured chat completion that returns parsed responses

        Args:
            messages: List of messages representing a conversation
            model: The model to use for completion
            response_format: The Pydantic model to parse the response into
            temperature: Sampling temperature between 0 and 2
            max_tokens: Maximum number of tokens to generate

        Returns:
            Parsed response in the format specified by response_format
        """
        try:
            params = self._prepare_params(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                **kwargs,
            )
            return await self.async_client.beta.chat.completions.parse(
                response_format=response_format, **params
            )
        except (openai.RateLimitError, openai.APIError, openai.APIConnectionError) as e:
            raise e
        except Exception as e:
            raise OpenAIError(f"Error calling OpenAI API: {str(e)}")

    @get_openai_retry_decorator()
    async def achat_completion_batch(
        self,
        messages: List[List[BaseChatMessage]],
        model: str,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> List[ChatCompletion]:
        """Asynchronous chat completion batch

        Args:
            messages: List of message lists, where each inner list represents a conversation
            model: The model to use for completion
            temperature: Sampling temperature between 0 and 2
            max_tokens: Maximum number of tokens to generate

        Returns:
            List of ChatCompletion objects, one for each input conversation
        """
        try:
            # Create async tasks for each message batch
            tasks = []
            for msg_batch in messages:
                params = self._prepare_params(
                    messages=msg_batch,
                    model=model,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                tasks.append(self.async_client.chat.completions.create(**params))

            # Execute all tasks in parallel and wait for results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle any errors that occurred
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {str(result)}")
                    raise OpenAIError(f"Batch processing failed: {str(result)}")
                processed_results.append(result)

            return processed_results

        except (openai.RateLimitError, openai.APIError, openai.APIConnectionError) as e:
            raise e
        except Exception as e:
            raise OpenAIError(f"Error in batch chat completion: {str(e)}")

    @get_openai_retry_decorator()
    async def achat_structured_completion_batch(
        self,
        messages: List[List[BaseChatMessage]],
        model: str,
        response_format: Any,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Any]:
        """Asynchronous structured chat completion batch

        Args:
            messages: List of message lists, where each inner list represents a conversation
            model: The model to use for completion
            response_format: The Pydantic model to parse the response into
            temperature: Sampling temperature between 0 and 2
            max_tokens: Maximum number of tokens to generate

        Returns:
            List of parsed responses in the format specified by response_format
        """
        try:
            # Create async tasks for each message batch
            tasks = []
            for msg_batch in messages:
                params = self._prepare_params(
                    messages=msg_batch,
                    model=model,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                tasks.append(
                    self.async_client.beta.chat.completions.parse(
                        response_format=response_format, **params
                    )
                )
            results = await asyncio.gather(*tasks, return_exceptions=True)

            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {str(result)}")
                    raise OpenAIError(f"Batch processing failed: {str(result)}")
                processed_results.append(result)

            return processed_results

        except (openai.RateLimitError, openai.APIError, openai.APIConnectionError) as e:
            raise e
        except Exception as e:
            raise OpenAIError(f"Error in batch structured chat completion: {str(e)}")
