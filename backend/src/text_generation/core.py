"""
Core text generation functionality.
"""

import asyncio
import logging
import os
from typing import Dict, Optional, Tuple

from ..types.providers import (
    AnthropicConfig,
    GeminiConfig,
    GenerationOptions,
    LLMProvider,
    OpenAIConfig,
    ProviderType,
)
from .rate_limiter import (
    OperationType,
    RateLimitExceededError,
    get_rate_limiter,
)

logger = logging.getLogger(__name__)

try:
    import openai  # type: ignore
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

try:
    import anthropic  # type: ignore
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
    from google.api_core import exceptions as google_exceptions  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore
    google_exceptions = None  # type: ignore


class TextGenerationError(Exception):
    """Exception raised for errors in the text generation process."""

    pass


class RateLimitError(TextGenerationError):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        operation_type: Optional[OperationType] = None,
        wait_time: Optional[float] = None,
    ):
        super().__init__(message)
        self.operation_type = operation_type
        self.wait_time = wait_time


def generate_text(
    prompt: str,
    provider: LLMProvider,
    options: Optional[GenerationOptions] = None,
    operation_type: Optional[OperationType] = None,
    check_rate_limit: bool = True,
) -> str:
    """
    Generate text using the specified LLM provider.

    Args:
        prompt: The prompt to generate text from.
        provider: The LLM provider to use.
        options: Options for text generation.
        operation_type: Type of operation for rate limiting (e.g., 'analysis', 'generation').
        check_rate_limit: Whether to check rate limits before calling the provider.

    Returns:
        The generated text.

    Raises:
        TextGenerationError: If an error occurs during text generation.
        RateLimitError: If rate limit is exceeded.
    """
    options = options or GenerationOptions()
    op_type = operation_type or OperationType.DEFAULT

    # Check rate limit if enabled
    if check_rate_limit:
        try:
            # Run async rate limit check in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                future = asyncio.ensure_future(_check_rate_limit(op_type))
                # We can't await here in sync function, so we check synchronously
                rate_limiter = get_rate_limiter()
                if not rate_limiter.check_limit(op_type):
                    bucket = rate_limiter._buckets[op_type]
                    wait_time = bucket.get_wait_time()
                    limit = rate_limiter.get_limit(op_type)
                    logger.warning(
                        "Rate limit would be exceeded for %s: limit=%d/min, wait=%.2fs",
                        op_type.value,
                        limit,
                        wait_time,
                    )
                    raise RateLimitError(
                        f"Rate limit exceeded for {op_type.value}. "
                        f"Limit: {limit}/min. Please wait {wait_time:.2f}s before retrying.",
                        operation_type=op_type,
                        wait_time=wait_time,
                    )
                # Manually consume a token for sync context
                bucket = rate_limiter._buckets[op_type]
                bucket._refill()
                if bucket.tokens >= 1.0:
                    bucket.tokens -= 1.0
            else:
                # Run the async check synchronously
                loop.run_until_complete(_check_rate_limit(op_type))
        except RuntimeError:
            # No event loop running, create one
            asyncio.run(_check_rate_limit(op_type))
        except RateLimitExceededError as e:
            raise RateLimitError(
                str(e),
                operation_type=e.operation_type,
                wait_time=e.wait_time,
            ) from e

    if provider.type == "openai":
        return generate_with_openai(prompt, provider.config, options)
    elif provider.type == "anthropic":
        return generate_with_anthropic(prompt, provider.config, options)
    elif provider.type == "gemini":
        return generate_with_gemini(prompt, provider.config, options)
    else:
        raise TextGenerationError(f"Unsupported provider: {provider.type}")


async def _check_rate_limit(operation_type: OperationType) -> None:
    """Async helper to check rate limit."""
    rate_limiter = get_rate_limiter()
    await rate_limiter.acquire(operation_type=operation_type, wait=False)


async def generate_text_async(
    prompt: str,
    provider: LLMProvider,
    options: Optional[GenerationOptions] = None,
    operation_type: Optional[OperationType] = None,
    check_rate_limit: bool = True,
    wait_for_rate_limit: bool = True,
) -> str:
    """
    Generate text using the specified LLM provider (async version).

    This async version properly integrates with the rate limiter and can
    wait for rate limits to clear before proceeding.

    Args:
        prompt: The prompt to generate text from.
        provider: The LLM provider to use.
        options: Options for text generation.
        operation_type: Type of operation for rate limiting.
        check_rate_limit: Whether to check rate limits before calling the provider.
        wait_for_rate_limit: Whether to wait for rate limits to clear (if True)
                            or raise immediately (if False).

    Returns:
        The generated text.

    Raises:
        TextGenerationError: If an error occurs during text generation.
        RateLimitError: If rate limit is exceeded and wait_for_rate_limit is False.
    """
    options = options or GenerationOptions()
    op_type = operation_type or OperationType.DEFAULT

    # Check rate limit if enabled
    if check_rate_limit:
        try:
            rate_limiter = get_rate_limiter()
            await rate_limiter.acquire(
                operation_type=op_type,
                wait=wait_for_rate_limit,
            )
        except RateLimitExceededError as e:
            raise RateLimitError(
                str(e),
                operation_type=e.operation_type,
                wait_time=e.wait_time,
            ) from e

    # Run the synchronous generation in a thread pool
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        lambda: _generate_text_internal(prompt, provider, options),
    )


def _generate_text_internal(
    prompt: str,
    provider: LLMProvider,
    options: GenerationOptions,
) -> str:
    """Internal text generation without rate limiting."""
    if provider.type == "openai":
        return generate_with_openai(prompt, provider.config, options)
    elif provider.type == "anthropic":
        return generate_with_anthropic(prompt, provider.config, options)
    elif provider.type == "gemini":
        return generate_with_gemini(prompt, provider.config, options)
    else:
        raise TextGenerationError(f"Unsupported provider: {provider.type}")


# Default timeout for LLM API calls (in seconds)
LLM_API_TIMEOUT = int(os.environ.get("LLM_API_TIMEOUT", "60"))

_openai_clients: Dict[Tuple[str, int], "openai.OpenAI"] = {}
_anthropic_clients: Dict[Tuple[str, int], "anthropic.Anthropic"] = {}


def _get_openai_client(api_key: str, timeout: int):
    key = (api_key, timeout)
    client = _openai_clients.get(key)
    if client is None:
        if openai is None:
            raise TextGenerationError(
                "OpenAI package not installed. Install it with 'pip install openai'."
            )

        client = openai.OpenAI(api_key=api_key, timeout=timeout)
        _openai_clients[key] = client
    return client


def _get_anthropic_client(api_key: str, timeout: int):
    key = (api_key, timeout)
    client = _anthropic_clients.get(key)
    if client is None:
        if anthropic is None:
            raise TextGenerationError(
                "Anthropic package not installed. Install it with 'pip install anthropic'."
            )

        client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
        _anthropic_clients[key] = client
    return client


def close_llm_clients() -> None:
    """Close any cached LLM clients (used during shutdown)."""
    for client in list(_openai_clients.values()):
        try:
            close = getattr(client, "close", None)
            if callable(close):
                close()
        except Exception as e:
            logger.warning("Failed to close OpenAI client: %s", e)
    for client in list(_anthropic_clients.values()):
        try:
            close = getattr(client, "close", None)
            if callable(close):
                close()
        except Exception as e:
            logger.warning("Failed to close Anthropic client: %s", e)
    _openai_clients.clear()
    _anthropic_clients.clear()


def generate_with_openai(
    prompt: str, config: OpenAIConfig, options: GenerationOptions
) -> str:
    """
    Generate text using OpenAI.

    Args:
        prompt: The prompt to generate text from.
        config: The OpenAI configuration.
        options: Options for text generation.

    Returns:
        The generated text.

    Raises:
        TextGenerationError: If an error occurs during text generation.
    """
    if openai is None:
        raise TextGenerationError(
            "OpenAI package not installed. Install it with 'pip install openai'."
        )

    from httpx import TimeoutException

    try:
        client = _get_openai_client(config.api_key, LLM_API_TIMEOUT)

        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            top_p=options.top_p,
            frequency_penalty=options.frequency_penalty,
            presence_penalty=options.presence_penalty,
        )

        # Validate response structure before accessing
        if not response.choices:
            raise TextGenerationError("OpenAI returned empty response (no choices)")
        if not response.choices[0].message or not response.choices[0].message.content:
            raise TextGenerationError("OpenAI returned empty message content")

        return response.choices[0].message.content
    except TimeoutException as e:
        raise TextGenerationError(f"OpenAI request timed out after {LLM_API_TIMEOUT}s: {e}") from e
    except Exception as e:
        def _is_openai_exc(attr: str) -> bool:
            exc_cls = getattr(openai, attr, None)
            return (
                isinstance(exc_cls, type)
                and issubclass(exc_cls, Exception)
                and isinstance(e, exc_cls)
            )

        if _is_openai_exc("AuthenticationError"):
            raise TextGenerationError(f"OpenAI authentication failed: {e}") from e
        if _is_openai_exc("RateLimitError"):
            raise TextGenerationError(f"OpenAI rate limit exceeded: {e}") from e
        if _is_openai_exc("APIConnectionError"):
            raise TextGenerationError(f"OpenAI connection error: {e}") from e

        # v2 clients raise structured status errors.
        if _is_openai_exc("APIStatusError"):
            status_code = getattr(e, "status_code", "unknown")
            raise TextGenerationError(f"OpenAI API error (status {status_code}): {e}") from e
        if _is_openai_exc("OpenAIError"):
            raise TextGenerationError(f"OpenAI error: {e}") from e

        raise TextGenerationError(f"OpenAI error: {e}") from e


def generate_with_anthropic(
    prompt: str, config: AnthropicConfig, options: GenerationOptions
) -> str:
    """
    Generate text using Anthropic.

    Args:
        prompt: The prompt to generate text from.
        config: The Anthropic configuration.
        options: Options for text generation.

    Returns:
        The generated text.

    Raises:
        TextGenerationError: If an error occurs during text generation.
    """
    if anthropic is None:
        raise TextGenerationError(
            "Anthropic package not installed. Install it with 'pip install anthropic'."
        )

    from httpx import TimeoutException

    try:
        client = _get_anthropic_client(config.api_key, LLM_API_TIMEOUT)

        response = client.messages.create(
            model=config.model,
            max_tokens=options.max_tokens,
            temperature=options.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        # Validate response structure before accessing
        if not response.content:
            raise TextGenerationError("Anthropic returned empty response (no content)")
        if not hasattr(response.content[0], "text") or not response.content[0].text:
            raise TextGenerationError("Anthropic returned empty text content")

        return response.content[0].text
    except TimeoutException as e:
        raise TextGenerationError(f"Anthropic request timed out after {LLM_API_TIMEOUT}s: {e}") from e
    except Exception as e:
        def _is_anthropic_exc(attr: str) -> bool:
            exc_cls = getattr(anthropic, attr, None)
            return (
                isinstance(exc_cls, type)
                and issubclass(exc_cls, Exception)
                and isinstance(e, exc_cls)
            )

        if _is_anthropic_exc("AuthenticationError"):
            raise TextGenerationError(f"Anthropic authentication failed: {e}") from e
        if _is_anthropic_exc("RateLimitError"):
            raise TextGenerationError(f"Anthropic rate limit exceeded: {e}") from e
        if _is_anthropic_exc("APIConnectionError"):
            raise TextGenerationError(f"Anthropic connection error: {e}") from e
        if _is_anthropic_exc("APIStatusError"):
            status_code = getattr(e, "status_code", "unknown")
            raise TextGenerationError(f"Anthropic API error (status {status_code}): {e}") from e
        if _is_anthropic_exc("AnthropicError"):
            raise TextGenerationError(f"Anthropic error: {e}") from e

        raise TextGenerationError(f"Anthropic error: {e}") from e


def generate_with_gemini(
    prompt: str, config: GeminiConfig, options: GenerationOptions
) -> str:
    """
    Generate text using Google's Gemini.

    Args:
        prompt: The prompt to generate text from.
        config: The Gemini configuration.
        options: Options for text generation.

    Returns:
        The generated text.

    Raises:
        TextGenerationError: If an error occurs during text generation.
    """
    if genai is None:
        raise TextGenerationError(
            "Google Generative AI package not installed. Install it with 'pip install google-generativeai'."
        )

    try:
        genai.configure(api_key=config.api_key)

        generation_config = {
            "temperature": options.temperature,
            "top_p": options.top_p,
            "max_output_tokens": options.max_tokens,
        }

        model = genai.GenerativeModel(config.model, generation_config=generation_config)

        # Gemini uses request_options for timeout
        response = model.generate_content(
            prompt,
            request_options={"timeout": LLM_API_TIMEOUT},
        )

        # Validate response structure before accessing
        if not response.text:
            raise TextGenerationError("Gemini returned empty response text")

        return response.text
    except ValueError as e:
        # Gemini raises ValueError for content safety issues
        raise TextGenerationError(f"Gemini content generation failed: {e}") from e
    except Exception as e:
        if google_exceptions is not None:
            # Map common Google API errors when available.
            if isinstance(e, getattr(google_exceptions, "Unauthenticated", ())):
                raise TextGenerationError(f"Gemini authentication failed: {e}") from e
            if isinstance(e, getattr(google_exceptions, "ResourceExhausted", ())):
                raise TextGenerationError(f"Gemini rate limit exceeded: {e}") from e
            if isinstance(e, getattr(google_exceptions, "ServiceUnavailable", ())):
                raise TextGenerationError(f"Gemini service unavailable: {e}") from e
            if isinstance(e, getattr(google_exceptions, "InvalidArgument", ())):
                raise TextGenerationError(f"Gemini invalid argument: {e}") from e
            if isinstance(e, getattr(google_exceptions, "DeadlineExceeded", ())):
                raise TextGenerationError(
                    f"Gemini request timed out after {LLM_API_TIMEOUT}s: {e}"
                ) from e
            if isinstance(e, getattr(google_exceptions, "GoogleAPIError", ())):
                raise TextGenerationError(f"Gemini API error: {e}") from e

        raise TextGenerationError(f"Gemini API error: {e}") from e


def create_provider_from_env(provider_type: ProviderType) -> LLMProvider:
    """
    Create a provider from environment variables.

    Args:
        provider_type: The type of provider to create.

    Returns:
        The created provider.

    Raises:
        TextGenerationError: If an error occurs during provider creation.
    """
    if provider_type == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise TextGenerationError("OPENAI_API_KEY environment variable not set")

        model = os.environ.get("OPENAI_MODEL", "gpt-4")
        config = OpenAIConfig(api_key=api_key, model=model)
        return LLMProvider(type=provider_type, config=config)

    elif provider_type == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise TextGenerationError("ANTHROPIC_API_KEY environment variable not set")

        model = os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        config = AnthropicConfig(api_key=api_key, model=model)
        return LLMProvider(type=provider_type, config=config)

    elif provider_type == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise TextGenerationError("GEMINI_API_KEY environment variable not set")

        model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-latest")
        config = GeminiConfig(api_key=api_key, model=model)
        return LLMProvider(type=provider_type, config=config)

    else:
        raise TextGenerationError(f"Unsupported provider type: {provider_type}")
