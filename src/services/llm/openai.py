"""OpenAI LLM provider implementation."""

import asyncio
import json
import logging
import time
from typing import Any, TypeVar

try:
    # LangChain 1.0+ moved LLMChain to langchain-classic
    from langchain_classic.chains import LLMChain
except ImportError:
    # Fallback for older versions
    from langchain.chains import LLMChain  # type: ignore[no-redef]

try:
    from langchain_classic.memory import ConversationBufferMemory
except ImportError:
    from langchain.memory import ConversationBufferMemory  # type: ignore[no-redef]

try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    try:
        from langchain_classic.prompts import PromptTemplate
    except ImportError:
        from langchain.prompts import PromptTemplate  # type: ignore[no-redef]
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from ...config import settings
from ...exceptions import LLMError, ValidationError
from ...utils import CacheManager, async_retry_with_backoff, retry_with_backoff
from .base import LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider using LangChain's ChatOpenAI.

    Provides retry logic, error handling, and structured output generation.
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
        Initialize OpenAI provider.

        Args:
            model: Model name (default: from settings)
            temperature: Sampling temperature (default: from settings)
            api_key: OpenAI API key (default: from settings)
            verbose: Enable verbose output (default: from settings)
            cache: Cache manager instance (optional)
        """
        self._model = model or settings.default_model
        self._temperature = temperature if temperature is not None else settings.temperature
        self._api_key = api_key or settings.openai_api_key
        self._verbose = verbose if verbose is not None else settings.verbose
        self._cache = cache

        self._llm = self._create_llm()

    def _create_llm(self) -> ChatOpenAI:
        """Create ChatOpenAI instance."""
        try:
            return ChatOpenAI(  # type: ignore[call-arg]
                model=self._model,
                temperature=self._temperature,
                openai_api_key=self._api_key,
            )
        except Exception as e:
            raise LLMError(
                f"Failed to initialize OpenAI client: {e}",
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
            max_tokens: Maximum tokens to generate
            **kwargs: Additional LangChain parameters

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

            # Create temporary LLM with custom settings if needed
            llm = self._llm
            if temperature is not None or max_tokens is not None:
                llm = ChatOpenAI(  # type: ignore[call-arg]
                    model=self._model,
                    temperature=temperature or self._temperature,
                    max_tokens=max_tokens,
                    openai_api_key=self._api_key,
                )

            # Create simple chain
            prompt_template = PromptTemplate(
                input_variables=["prompt"],
                template="{prompt}",
            )
            chain = LLMChain(
                llm=llm,
                prompt=prompt_template,
                verbose=self._verbose,
            )

            # Generate
            response = chain.run(prompt=prompt)

            # Rate limiting
            time.sleep(settings.api_retry_delay)

            result = response.strip()

            # Cache the response
            if self._cache:
                self._cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
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

            llm = self._llm
            if temperature is not None or max_tokens is not None:
                llm = ChatOpenAI(  # type: ignore[call-arg]
                    model=self._model,
                    temperature=temperature or self._temperature,
                    max_tokens=max_tokens,
                    openai_api_key=self._api_key,
                )

            # Create chain with memory
            memory = ConversationBufferMemory(
                input_key="input",
                memory_key="chat_history",
            )

            # Add context to memory
            if context:
                for msg in context:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        memory.chat_memory.add_user_message(content)
                    elif role == "assistant":
                        memory.chat_memory.add_ai_message(content)

            prompt_template = PromptTemplate(
                input_variables=["input"],
                template="{input}",
            )

            chain = LLMChain(
                llm=llm,
                prompt=prompt_template,
                memory=memory,
                verbose=self._verbose,
            )

            response = chain.run(input=prompt)

            # Rate limiting
            time.sleep(settings.api_retry_delay)

            return response.strip()

        except Exception as e:
            logger.error(f"OpenAI generation with memory failed: {e}")
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
            **kwargs: Additional LangChain parameters

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
            logger.error(f"Async OpenAI generation failed: {e}")
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
