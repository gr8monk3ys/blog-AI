"""Base content generator class."""

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from ...config import Settings
from ...services.llm.base import LLMProvider

logger = logging.getLogger(__name__)

# Type variable for content structure
TStructure = TypeVar("TStructure", bound=BaseModel)


class ContentGenerator(ABC, Generic[TStructure]):
    """
    Abstract base class for content generators.

    Implements the template method pattern for content generation:
    1. Generate structure (outline)
    2. Fill in content for each section
    3. Return completed structure

    Subclasses implement specific logic for different content types.
    """

    def __init__(self, llm: LLMProvider, config: Settings):
        """
        Initialize generator with LLM provider and configuration.

        Args:
            llm: LLM provider for text generation
            config: Application configuration
        """
        self.llm = llm
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def generate_structure(self, topic: str, **kwargs) -> TStructure:
        """
        Generate the content structure/outline.

        This creates the skeleton of the content without detailed text.

        Args:
            topic: Main topic for content generation
            **kwargs: Additional generation parameters

        Returns:
            Content structure with empty/placeholder content

        Raises:
            GenerationError: If structure generation fails
        """
        pass

    @abstractmethod
    def generate_content(self, structure: TStructure, **kwargs) -> TStructure:
        """
        Fill in content for each section of the structure.

        Takes a structure with empty content and populates it with
        detailed, generated text.

        Args:
            structure: Content structure to fill
            **kwargs: Additional generation parameters

        Returns:
            Complete content structure with all sections filled

        Raises:
            GenerationError: If content generation fails
        """
        pass

    def generate(self, topic: str, **kwargs) -> TStructure:
        """
        Full generation pipeline: structure + content.

        This is the main entry point that orchestrates the full
        content generation process.

        Args:
            topic: Main topic for content generation
            **kwargs: Additional generation parameters

        Returns:
            Complete content structure

        Raises:
            GenerationError: If any step fails
        """
        self.logger.info(f"Starting content generation for topic: {topic}")

        # Step 1: Generate structure
        self.logger.debug("Generating content structure...")
        structure = self.generate_structure(topic, **kwargs)
        self.logger.info("Structure generated successfully")

        # Step 2: Fill content
        self.logger.debug("Generating content for each section...")
        complete_structure = self.generate_content(structure, **kwargs)
        self.logger.info("Content generation completed successfully")

        return complete_structure

    def _log_progress(self, message: str, current: int, total: int) -> None:
        """
        Log progress for long-running operations.

        Args:
            message: Progress message
            current: Current item number
            total: Total number of items
        """
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(f"{message} [{current}/{total}] ({percentage:.1f}%)")
