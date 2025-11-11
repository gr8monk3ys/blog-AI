"""Base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """
    Abstract base class for Large Language Model providers.

    Provides a common interface for interacting with different LLM APIs
    (OpenAI, Anthropic, local models, etc.).
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
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
            prompt: The input prompt
            response_model: Pydantic model class for the response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Instance of response_model populated with generated data

        Raises:
            LLMError: If generation fails
            ValidationError: If response doesn't match model
        """
        pass

    @abstractmethod
    def generate_with_memory(
        self,
        prompt: str,
        context: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text with conversation context/memory.

        Args:
            prompt: The input prompt
            context: Previous messages [{"role": "user", "content": "..."}, ...]
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the current model."""
        pass

    @property
    @abstractmethod
    def default_temperature(self) -> float:
        """Get the default temperature setting."""
        pass

    # Async methods (optional, not all providers need to implement)

    async def generate_async(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Async version of generate. Default implementation calls sync version.

        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails
        """
        # Default: call sync version (subclasses can override for true async)
        return self.generate(prompt, temperature, max_tokens, **kwargs)

    async def generate_structured_async(
        self,
        prompt: str,
        response_model: type[T],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Async version of generate_structured. Default implementation calls sync version.

        Args:
            prompt: The input prompt
            response_model: Pydantic model class for the response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Instance of response_model populated with generated data

        Raises:
            LLMError: If generation fails
            ValidationError: If response doesn't match model
        """
        # Default: call sync version (subclasses can override for true async)
        return self.generate_structured(prompt, response_model, temperature, max_tokens, **kwargs)

    async def generate_with_memory_async(
        self,
        prompt: str,
        context: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Async version of generate_with_memory. Default implementation calls sync version.

        Args:
            prompt: The input prompt
            context: Previous messages [{"role": "user", "content": "..."}, ...]
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails
        """
        # Default: call sync version (subclasses can override for true async)
        return self.generate_with_memory(prompt, context, temperature, max_tokens, **kwargs)
