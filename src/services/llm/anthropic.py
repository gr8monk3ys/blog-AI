"""Anthropic Claude LLM provider implementation."""

import asyncio
import json
import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from ...config import settings
from ...exceptions import LLMError, ValidationError
from ...utils import CacheManager, async_retry_with_backoff, retry_with_backoff
from .base import LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude LLM provider.

    Provides retry logic, error handling, and structured output generation
    using Anthropic's Claude models.

    Note: Requires anthropic package to be installed:
        pip install anthropic
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        api_key: str | None = None,
        verbose: bool | None = None,
        cache: CacheManager | None = None,
    ):
        """
        Initialize Anthropic provider.

        Args:
            model: Model name (default: claude-3-5-sonnet-20241022)
            temperature: Sampling temperature (default: from settings)
            api_key: Anthropic API key (default: from settings)
            verbose: Enable verbose output (default: from settings)
            cache: Cache manager instance (optional)

        Raises:
            ImportError: If anthropic package is not installed
            LLMError: If initialization fails
        """
        self._model = model or "claude-3-5-sonnet-20241022"
        self._temperature = temperature if temperature is not None else settings.temperature
        self._api_key = api_key or getattr(settings, "anthropic_api_key", None)
        self._verbose = verbose if verbose is not None else settings.verbose
        self._cache = cache

        # Lazy import to avoid hard dependency
        try:
            import anthropic

            self._anthropic = anthropic
        except ImportError as e:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            ) from e

        # Validate API key
        if not self._api_key:
            raise LLMError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY in .env file.",
                details={
                    "help_url": "https://console.anthropic.com/settings/keys",
                },
            )

        # Create client
        self._client = self._create_client()

    def _create_client(self) -> Any:
        """Create Anthropic client instance."""
        try:
            return self._anthropic.Anthropic(api_key=self._api_key)
        except Exception as e:
            raise LLMError(
                f"Failed to initialize Anthropic client: {e}",
                details={"model": self._model},
            ) from e

    @retry_with_backoff(
        max_attempts=settings.api_retry_attempts,
        initial_delay=settings.api_retry_delay,
        backoff_factor=settings.api_retry_backoff,
        exceptions=(Exception,),
    )
    def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text from a prompt with retry logic.

        Args:
            prompt: The input prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate (default: 4096)
            **kwargs: Additional Anthropic parameters

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails after retries
        """
        # Check cache first
        if self._cache:
            cache_key = self._cache.generate_key(
                prompt=prompt,
                model=self._model,
                temperature=temperature or self._temperature,
                max_tokens=max_tokens,
            )
            cached_response = self._cache.get(cache_key)
            if cached_response is not None:
                logger.debug("Returning cached response")
                return cached_response

        try:
            logger.debug(f"Generating text with model {self._model}")

            # Create message
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens or 4096,
                temperature=temperature or self._temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )

            # Extract text from response
            if not response.content:
                raise LLMError(
                    "Empty response from Anthropic API",
                    details={"model": self._model},
                )

            # Claude returns a list of content blocks
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text

            # Rate limiting
            time.sleep(settings.api_retry_delay)

            if self._verbose:
                logger.debug(f"Generated {len(text)} characters")

            result = text.strip()

            # Cache the response
            if self._cache:
                self._cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise LLMError(
                f"Failed to generate text: {e}",
                details={
                    "model": self._model,
                    "temperature": temperature or self._temperature,
                },
            ) from e

    @retry_with_backoff(
        max_attempts=settings.api_retry_attempts,
        initial_delay=settings.api_retry_delay,
        backoff_factor=settings.api_retry_backoff,
        exceptions=(Exception,),
    )
    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Generate structured output matching a Pydantic model.

        Args:
            prompt: The input prompt (should request JSON output)
            response_model: Pydantic model for validation
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Validated instance of response_model

        Raises:
            LLMError: If generation fails
            ValidationError: If response doesn't match model
        """
        try:
            logger.debug(f"Generating structured output for {response_model.__name__}")

            # Enhanced prompt to ensure JSON output
            enhanced_prompt = (
                f"{prompt}\n\nReturn your response as valid JSON only, with no additional text."
            )

            # Generate raw text
            response_text = self.generate(
                prompt=enhanced_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Extract JSON from response (handle markdown code blocks)
            json_text = self._extract_json(response_text)

            # Parse JSON
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Failed to parse JSON response: {e}",
                    details={
                        "response": response_text[:500],
                        "model": response_model.__name__,
                    },
                ) from e

            # Validate with Pydantic model
            try:
                return (
                    response_model(**data)
                    if isinstance(data, dict)
                    else response_model.model_validate(data)
                )
            except PydanticValidationError as e:
                raise ValidationError(
                    f"Response doesn't match {response_model.__name__}: {e}",
                    details={
                        "errors": e.errors(),
                        "data": data,
                    },
                ) from e

        except (LLMError, ValidationError):
            raise
        except Exception as e:
            raise LLMError(
                f"Unexpected error in structured generation: {e}",
                details={"model": response_model.__name__},
            ) from e

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text, handling markdown code blocks.

        Args:
            text: Raw text potentially containing JSON

        Returns:
            Extracted JSON string
        """
        text = text.strip()

        # Check for markdown code block
        if text.startswith("```"):
            # Remove opening ```json or ```
            lines = text.split("\n")
            lines = lines[1:]  # Skip first line
            # Remove closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        return text

    @retry_with_backoff(
        max_attempts=settings.api_retry_attempts,
        initial_delay=settings.api_retry_delay,
        backoff_factor=settings.api_retry_backoff,
        exceptions=(Exception,),
    )
    def generate_with_memory(
        self,
        prompt: str,
        context: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text with conversation context.

        Args:
            prompt: The input prompt
            context: Previous messages [{"role": "user/assistant", "content": "..."}]
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        try:
            logger.debug(f"Generating with memory, context size: {len(context or [])}")

            # Build messages list from context
            messages = []
            if context:
                for msg in context:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")

                    # Anthropic uses "assistant" not "ai"
                    if role == "ai":
                        role = "assistant"

                    messages.append({"role": role, "content": content})

            # Add current prompt
            messages.append({"role": "user", "content": prompt})

            # Create message with context
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens or 4096,
                temperature=temperature or self._temperature,
                messages=messages,
                **kwargs,
            )

            # Extract text from response
            if not response.content:
                raise LLMError(
                    "Empty response from Anthropic API",
                    details={"model": self._model},
                )

            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text

            # Rate limiting
            time.sleep(settings.api_retry_delay)

            return text.strip()

        except Exception as e:
            logger.error(f"Anthropic generation with memory failed: {e}")
            raise LLMError(
                f"Failed to generate text with memory: {e}",
                details={"model": self._model},
            ) from e

    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model

    @property
    def default_temperature(self) -> float:
        """Get the default temperature."""
        return self._temperature

    # Async methods

    @async_retry_with_backoff(
        max_attempts=settings.api_retry_attempts,
        initial_delay=settings.api_retry_delay,
        backoff_factor=settings.api_retry_backoff,
        exceptions=(Exception,),
    )
    async def generate_async(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Async version of generate. Runs in thread pool to avoid blocking.

        Args:
            prompt: The input prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic parameters

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails after retries
        """
        logger.debug(f"Generating text async with model {self._model}")

        # Run sync method in thread pool to avoid blocking event loop
        try:
            response = await asyncio.to_thread(
                self.generate,
                prompt,
                temperature,
                max_tokens,
                **kwargs,
            )
            return response
        except Exception as e:
            logger.error(f"Async Anthropic generation failed: {e}")
            raise

    @async_retry_with_backoff(
        max_attempts=settings.api_retry_attempts,
        initial_delay=settings.api_retry_delay,
        backoff_factor=settings.api_retry_backoff,
        exceptions=(Exception,),
    )
    async def generate_structured_async(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Async version of generate_structured.

        Args:
            prompt: The input prompt
            response_model: Pydantic model for validation
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Validated instance of response_model

        Raises:
            LLMError: If generation fails
            ValidationError: If response doesn't match model
        """
        logger.debug(f"Generating structured output async for {response_model.__name__}")

        # Run sync method in thread pool
        try:
            response = await asyncio.to_thread(
                self.generate_structured,
                prompt,
                response_model,
                temperature,
                max_tokens,
                **kwargs,
            )
            return response
        except Exception as e:
            logger.error(f"Async structured generation failed: {e}")
            raise

    @async_retry_with_backoff(
        max_attempts=settings.api_retry_attempts,
        initial_delay=settings.api_retry_delay,
        backoff_factor=settings.api_retry_backoff,
        exceptions=(Exception,),
    )
    async def generate_with_memory_async(
        self,
        prompt: str,
        context: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Async version of generate_with_memory.

        Args:
            prompt: The input prompt
            context: Previous messages
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        logger.debug(f"Generating with memory async, context size: {len(context or [])}")

        # Run sync method in thread pool
        try:
            response = await asyncio.to_thread(
                self.generate_with_memory,
                prompt,
                context,
                temperature,
                max_tokens,
                **kwargs,
            )
            return response
        except Exception as e:
            logger.error(f"Async generation with memory failed: {e}")
            raise
