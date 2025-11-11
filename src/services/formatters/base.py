"""Base formatter interface."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Formatter(ABC, Generic[T]):
    """
    Abstract base class for content formatters.

    Formatters convert Pydantic models into output formats
    (MDX, DOCX, HTML, PDF, etc.).
    """

    @abstractmethod
    def format(self, content: T, **kwargs: Any) -> str | bytes | Any:
        """
        Format content into target output format.

        Args:
            content: Content model to format
            **kwargs: Formatter-specific options

        Returns:
            Formatted content (string for text formats, bytes for binary)

        Raises:
            FormattingError: If formatting fails
        """
        pass

    @property
    @abstractmethod
    def output_extension(self) -> str:
        """Get the file extension for this format (e.g., '.mdx', '.docx')."""
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Get the MIME type for this format."""
        pass
