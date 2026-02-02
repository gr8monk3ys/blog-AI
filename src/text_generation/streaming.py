"""
Streaming text generation functionality.

Provides async generators for token-by-token streaming from LLM providers.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Optional, Union

from ..types.providers import (
    AnthropicConfig,
    GeminiConfig,
    GenerationOptions,
    LLMProvider,
    OpenAIConfig,
    ProviderType,
)
from .core import TextGenerationError, create_provider_from_env
from .rate_limiter import OperationType, RateLimitExceededError, get_rate_limiter

logger = logging.getLogger(__name__)

# Default timeout for streaming LLM API calls (in seconds)
STREAMING_TIMEOUT = int(os.environ.get("LLM_STREAMING_TIMEOUT", "120"))


class StreamEventType(str, Enum):
    """Types of events that can occur during streaming."""

    TOKEN = "token"
    START = "start"
    END = "end"
    ERROR = "error"
    METADATA = "metadata"


@dataclass
class StreamEvent:
    """Represents a single event in the streaming response."""

    type: StreamEventType
    content: str = ""
    metadata: Optional[dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the event to a dictionary for serialization."""
        result = {"type": self.type.value, "content": self.content}
        if self.metadata:
            result["metadata"] = self.metadata
        if self.error:
            result["error"] = self.error
        return result


class StreamingError(TextGenerationError):
    """Exception raised for errors during streaming text generation."""

    def __init__(
        self,
        message: str,
        partial_content: str = "",
        is_recoverable: bool = False,
    ):
        super().__init__(message)
        self.partial_content = partial_content
        self.is_recoverable = is_recoverable


async def stream_text(
    prompt: str,
    provider: LLMProvider,
    options: Optional[GenerationOptions] = None,
    operation_type: Optional[OperationType] = None,
    check_rate_limit: bool = True,
) -> AsyncGenerator[StreamEvent, None]:
    """
    Stream text generation using the specified LLM provider.

    This is the main entry point for streaming text generation. It yields
    StreamEvent objects as tokens arrive from the provider.

    Args:
        prompt: The prompt to generate text from.
        provider: The LLM provider to use.
        options: Options for text generation.
        operation_type: Type of operation for rate limiting.
        check_rate_limit: Whether to check rate limits before calling the provider.

    Yields:
        StreamEvent objects containing tokens or status updates.

    Raises:
        StreamingError: If an error occurs during streaming.
    """
    options = options or GenerationOptions()
    op_type = operation_type or OperationType.DEFAULT

    # Check rate limit if enabled
    if check_rate_limit:
        try:
            rate_limiter = get_rate_limiter()
            await rate_limiter.acquire(operation_type=op_type, wait=False)
        except RateLimitExceededError as e:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error=f"Rate limit exceeded: {str(e)}",
            )
            return

    # Yield start event
    yield StreamEvent(
        type=StreamEventType.START,
        metadata={"provider": provider.type, "model": provider.config.model},
    )

    try:
        if provider.type == "openai":
            async for event in _stream_openai(prompt, provider.config, options):
                yield event
        elif provider.type == "anthropic":
            async for event in _stream_anthropic(prompt, provider.config, options):
                yield event
        elif provider.type == "gemini":
            async for event in _stream_gemini(prompt, provider.config, options):
                yield event
        else:
            yield StreamEvent(
                type=StreamEventType.ERROR,
                error=f"Unsupported provider for streaming: {provider.type}",
            )
            return
    except StreamingError as e:
        yield StreamEvent(
            type=StreamEventType.ERROR,
            error=str(e),
            content=e.partial_content,
        )
        return
    except Exception as e:
        logger.error(f"Unexpected streaming error: {e}", exc_info=True)
        yield StreamEvent(
            type=StreamEventType.ERROR,
            error=f"Unexpected error: {str(e)}",
        )
        return


async def _stream_openai(
    prompt: str,
    config: OpenAIConfig,
    options: GenerationOptions,
) -> AsyncGenerator[StreamEvent, None]:
    """
    Stream text generation using OpenAI.

    Args:
        prompt: The prompt to generate text from.
        config: The OpenAI configuration.
        options: Options for text generation.

    Yields:
        StreamEvent objects containing tokens.
    """
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise StreamingError(
            "OpenAI package not installed. Install it with 'pip install openai'."
        )

    client = AsyncOpenAI(
        api_key=config.api_key,
        timeout=STREAMING_TIMEOUT,
    )

    accumulated_content = ""

    try:
        stream = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            top_p=options.top_p,
            frequency_penalty=options.frequency_penalty,
            presence_penalty=options.presence_penalty,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                accumulated_content += token
                yield StreamEvent(type=StreamEventType.TOKEN, content=token)

            # Check for finish reason
            if chunk.choices and chunk.choices[0].finish_reason:
                yield StreamEvent(
                    type=StreamEventType.END,
                    metadata={"finish_reason": chunk.choices[0].finish_reason},
                )
                return

        # If we exit the loop without a finish_reason, yield end event
        yield StreamEvent(type=StreamEventType.END)

    except asyncio.CancelledError:
        logger.info("OpenAI stream cancelled")
        yield StreamEvent(
            type=StreamEventType.END,
            content=accumulated_content,
            metadata={"cancelled": True},
        )
        raise
    except Exception as e:
        error_msg = _categorize_openai_error(e)
        raise StreamingError(
            error_msg,
            partial_content=accumulated_content,
            is_recoverable=_is_recoverable_error(e),
        ) from e


def _categorize_openai_error(e: Exception) -> str:
    """Categorize OpenAI errors into user-friendly messages."""
    try:
        import openai
    except ImportError:
        return str(e)

    if isinstance(e, openai.AuthenticationError):
        return "OpenAI authentication failed"
    elif isinstance(e, openai.RateLimitError):
        return "OpenAI rate limit exceeded"
    elif isinstance(e, openai.APIConnectionError):
        return "OpenAI connection error"
    elif isinstance(e, openai.APIStatusError):
        return f"OpenAI API error (status {e.status_code})"
    else:
        return f"OpenAI error: {str(e)}"


async def _stream_anthropic(
    prompt: str,
    config: AnthropicConfig,
    options: GenerationOptions,
) -> AsyncGenerator[StreamEvent, None]:
    """
    Stream text generation using Anthropic.

    Args:
        prompt: The prompt to generate text from.
        config: The Anthropic configuration.
        options: Options for text generation.

    Yields:
        StreamEvent objects containing tokens.
    """
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        raise StreamingError(
            "Anthropic package not installed. Install it with 'pip install anthropic'."
        )

    client = AsyncAnthropic(
        api_key=config.api_key,
        timeout=STREAMING_TIMEOUT,
    )

    accumulated_content = ""

    try:
        async with client.messages.stream(
            model=config.model,
            max_tokens=options.max_tokens,
            temperature=options.temperature,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                accumulated_content += text
                yield StreamEvent(type=StreamEventType.TOKEN, content=text)

        # Get final message for metadata
        final_message = await stream.get_final_message()
        yield StreamEvent(
            type=StreamEventType.END,
            metadata={
                "stop_reason": final_message.stop_reason,
                "input_tokens": final_message.usage.input_tokens,
                "output_tokens": final_message.usage.output_tokens,
            },
        )

    except asyncio.CancelledError:
        logger.info("Anthropic stream cancelled")
        yield StreamEvent(
            type=StreamEventType.END,
            content=accumulated_content,
            metadata={"cancelled": True},
        )
        raise
    except Exception as e:
        error_msg = _categorize_anthropic_error(e)
        raise StreamingError(
            error_msg,
            partial_content=accumulated_content,
            is_recoverable=_is_recoverable_error(e),
        ) from e


def _categorize_anthropic_error(e: Exception) -> str:
    """Categorize Anthropic errors into user-friendly messages."""
    try:
        import anthropic
    except ImportError:
        return str(e)

    if isinstance(e, anthropic.AuthenticationError):
        return "Anthropic authentication failed"
    elif isinstance(e, anthropic.RateLimitError):
        return "Anthropic rate limit exceeded"
    elif isinstance(e, anthropic.APIConnectionError):
        return "Anthropic connection error"
    elif isinstance(e, anthropic.APIStatusError):
        return f"Anthropic API error (status {e.status_code})"
    else:
        return f"Anthropic error: {str(e)}"


async def _stream_gemini(
    prompt: str,
    config: GeminiConfig,
    options: GenerationOptions,
) -> AsyncGenerator[StreamEvent, None]:
    """
    Stream text generation using Google's Gemini.

    Note: Gemini's streaming API is synchronous, so we run it in a thread pool
    and yield tokens as they become available.

    Args:
        prompt: The prompt to generate text from.
        config: The Gemini configuration.
        options: Options for text generation.

    Yields:
        StreamEvent objects containing tokens.
    """
    try:
        import google.generativeai as genai
        from google.api_core import exceptions as google_exceptions
    except ImportError:
        raise StreamingError(
            "Google Generative AI package not installed. "
            "Install it with 'pip install google-generativeai'."
        )

    genai.configure(api_key=config.api_key)

    generation_config = {
        "temperature": options.temperature,
        "top_p": options.top_p,
        "max_output_tokens": options.max_tokens,
    }

    model = genai.GenerativeModel(config.model, generation_config=generation_config)

    accumulated_content = ""

    # Use an asyncio Queue to bridge sync streaming to async
    queue: asyncio.Queue[Union[str, Exception, None]] = asyncio.Queue()

    def _run_sync_stream():
        """Run the synchronous Gemini stream in a thread."""
        try:
            response = model.generate_content(
                prompt,
                stream=True,
                request_options={"timeout": STREAMING_TIMEOUT},
            )
            for chunk in response:
                if chunk.text:
                    queue.put_nowait(chunk.text)
            queue.put_nowait(None)  # Signal completion
        except Exception as e:
            queue.put_nowait(e)

    # Start the sync stream in a thread
    loop = asyncio.get_running_loop()
    stream_task = loop.run_in_executor(None, _run_sync_stream)

    try:
        while True:
            try:
                # Wait for items with a timeout to allow cancellation checks
                item = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # Check if the stream task is done
                if stream_task.done():
                    break
                continue

            if item is None:
                # Stream completed
                yield StreamEvent(type=StreamEventType.END)
                return
            elif isinstance(item, Exception):
                raise item
            else:
                accumulated_content += item
                yield StreamEvent(type=StreamEventType.TOKEN, content=item)

    except asyncio.CancelledError:
        logger.info("Gemini stream cancelled")
        yield StreamEvent(
            type=StreamEventType.END,
            content=accumulated_content,
            metadata={"cancelled": True},
        )
        raise
    except google_exceptions.GoogleAPIError as e:
        error_msg = _categorize_gemini_error(e)
        raise StreamingError(
            error_msg,
            partial_content=accumulated_content,
            is_recoverable=_is_recoverable_error(e),
        ) from e
    except Exception as e:
        raise StreamingError(
            f"Gemini streaming error: {str(e)}",
            partial_content=accumulated_content,
            is_recoverable=_is_recoverable_error(e),
        ) from e


def _categorize_gemini_error(e: Exception) -> str:
    """Categorize Gemini errors into user-friendly messages."""
    try:
        from google.api_core import exceptions as google_exceptions
    except ImportError:
        return str(e)

    if isinstance(e, google_exceptions.Unauthenticated):
        return "Gemini authentication failed"
    elif isinstance(e, google_exceptions.ResourceExhausted):
        return "Gemini rate limit exceeded"
    elif isinstance(e, google_exceptions.ServiceUnavailable):
        return "Gemini service unavailable"
    elif isinstance(e, google_exceptions.InvalidArgument):
        return f"Gemini invalid argument: {str(e)}"
    elif isinstance(e, google_exceptions.DeadlineExceeded):
        return f"Gemini request timed out after {STREAMING_TIMEOUT}s"
    else:
        return f"Gemini error: {str(e)}"


def _is_recoverable_error(e: Exception) -> bool:
    """
    Determine if an error is recoverable (transient).

    Recoverable errors include rate limits and temporary service issues.
    """
    error_str = str(type(e).__name__).lower()
    return any(
        keyword in error_str
        for keyword in ["ratelimit", "timeout", "unavailable", "connection"]
    )


async def stream_text_simple(
    prompt: str,
    provider_type: ProviderType = "openai",
    options: Optional[GenerationOptions] = None,
) -> AsyncGenerator[str, None]:
    """
    Simplified streaming interface that yields only token strings.

    This is a convenience wrapper around stream_text() for cases where
    you only need the raw token content without metadata.

    Args:
        prompt: The prompt to generate text from.
        provider_type: The type of provider to use.
        options: Options for text generation.

    Yields:
        Token strings as they arrive.

    Example:
        async for token in stream_text_simple("Tell me a story"):
            print(token, end="", flush=True)
    """
    provider = create_provider_from_env(provider_type)

    async for event in stream_text(prompt, provider, options):
        if event.type == StreamEventType.TOKEN:
            yield event.content
        elif event.type == StreamEventType.ERROR:
            raise StreamingError(event.error or "Unknown streaming error")


async def collect_stream(
    prompt: str,
    provider: LLMProvider,
    options: Optional[GenerationOptions] = None,
) -> tuple[str, dict]:
    """
    Collect all tokens from a stream into a complete string.

    Useful when you want streaming behavior internally but need the
    complete response for processing.

    Args:
        prompt: The prompt to generate text from.
        provider: The LLM provider to use.
        options: Options for text generation.

    Returns:
        A tuple of (complete_text, metadata).

    Raises:
        StreamingError: If an error occurs during streaming.
    """
    content_parts: list[str] = []
    metadata: dict = {}

    async for event in stream_text(prompt, provider, options):
        if event.type == StreamEventType.TOKEN:
            content_parts.append(event.content)
        elif event.type == StreamEventType.END:
            if event.metadata:
                metadata.update(event.metadata)
        elif event.type == StreamEventType.ERROR:
            raise StreamingError(
                event.error or "Unknown error",
                partial_content="".join(content_parts),
            )

    return "".join(content_parts), metadata
