"""
Base tool class that all content generation tools inherit from.

This module provides the abstract base class and common functionality
for all tools in the registry.
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from string import Template
from typing import Any, Dict, List, Optional, Type

from ..text_generation.core import (
    TextGenerationError,
    create_provider_from_env,
    generate_text,
)
from ..types.providers import GenerationOptions, LLMProvider, ProviderType
from ..types.scoring import (
    ContentScoreResult,
    ContentVariation,
    VariationGenerationResult,
)
from ..types.tools import (
    InputField,
    InputFieldType,
    InputSchema,
    OutputFormat,
    OutputSchema,
    ToolCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolMetadata,
)

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""

    def __init__(self, message: str, tool_id: str, original_error: Optional[Exception] = None):
        self.message = message
        self.tool_id = tool_id
        self.original_error = original_error
        super().__init__(self.message)


class BaseTool(ABC):
    """
    Abstract base class for all content generation tools.

    To create a new tool:
    1. Subclass BaseTool
    2. Implement the abstract properties and methods
    3. Register the tool with the ToolRegistry

    Example:
        class BlogTitleTool(BaseTool):
            @property
            def id(self) -> str:
                return "blog-title-generator"

            @property
            def name(self) -> str:
                return "Blog Title Generator"

            # ... implement other required properties/methods
    """

    # Class-level cache for tool definitions
    _definition_cache: Optional[ToolDefinition] = None

    # ==========================================================================
    # Abstract properties - MUST be implemented by subclasses
    # ==========================================================================

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the tool (slug format)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Category this tool belongs to."""
        pass

    @property
    @abstractmethod
    def input_fields(self) -> List[InputField]:
        """List of input fields for this tool."""
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> str:
        """
        Prompt template with placeholders.

        Use ${field_name} syntax for variable substitution.
        Example: "Write a blog post about ${topic} targeting ${audience}"
        """
        pass

    # ==========================================================================
    # Optional properties - CAN be overridden by subclasses
    # ==========================================================================

    @property
    def icon(self) -> Optional[str]:
        """Icon identifier or emoji for the tool."""
        return None

    @property
    def tags(self) -> List[str]:
        """Searchable tags for the tool."""
        return []

    @property
    def is_premium(self) -> bool:
        """Whether this tool requires premium access."""
        return False

    @property
    def is_beta(self) -> bool:
        """Whether this tool is in beta."""
        return False

    @property
    def estimated_time_seconds(self) -> int:
        """Estimated execution time in seconds."""
        return 30

    @property
    def output_format(self) -> OutputFormat:
        """Output format for this tool."""
        return OutputFormat.MARKDOWN

    @property
    def output_description(self) -> str:
        """Description of the output format."""
        return "Generated content"

    @property
    def system_prompt(self) -> Optional[str]:
        """
        Optional system prompt for the LLM.

        Override this to provide context or persona for the generation.
        """
        return None

    @property
    def examples(self) -> List[Dict[str, Any]]:
        """Example inputs and outputs for the tool."""
        return []

    @property
    def default_temperature(self) -> float:
        """Default temperature for text generation."""
        return 0.7

    @property
    def default_max_tokens(self) -> int:
        """Default max tokens for text generation."""
        return 2000

    # ==========================================================================
    # Core methods
    # ==========================================================================

    def get_definition(self) -> ToolDefinition:
        """
        Get the complete tool definition.

        Returns:
            ToolDefinition containing all tool metadata and configuration.
        """
        if self._definition_cache is not None:
            return self._definition_cache

        metadata = ToolMetadata(
            id=self.id,
            name=self.name,
            description=self.description,
            category=self.category,
            icon=self.icon,
            tags=self.tags,
            is_premium=self.is_premium,
            is_beta=self.is_beta,
            estimated_time_seconds=self.estimated_time_seconds,
        )

        input_schema = InputSchema(fields=self.input_fields)

        output_schema = OutputSchema(
            format=self.output_format,
            description=self.output_description,
        )

        self._definition_cache = ToolDefinition(
            metadata=metadata,
            input_schema=input_schema,
            output_schema=output_schema,
            prompt_template=self.prompt_template,
            system_prompt=self.system_prompt,
            examples=self.examples,
        )

        return self._definition_cache

    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Validate inputs against the tool's input schema.

        Args:
            inputs: Dictionary of input values.

        Returns:
            List of validation error messages (empty if valid).
        """
        definition = self.get_definition()
        return definition.input_schema.validate_input(inputs)

    def build_prompt(self, inputs: Dict[str, Any]) -> str:
        """
        Build the complete prompt from inputs.

        Args:
            inputs: Dictionary of input values.

        Returns:
            Formatted prompt string.
        """
        # Apply defaults for missing optional fields
        complete_inputs = {}
        for field in self.input_fields:
            if field.name in inputs:
                complete_inputs[field.name] = inputs[field.name]
            elif field.default is not None:
                complete_inputs[field.name] = field.default
            elif not field.required:
                complete_inputs[field.name] = ""

        # Use Template for safe substitution
        template = Template(self.prompt_template)
        return template.safe_substitute(complete_inputs)

    def pre_process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-process inputs before prompt building.

        Override this method to transform inputs before they're used.

        Args:
            inputs: Raw input values.

        Returns:
            Processed input values.
        """
        return inputs

    def post_process(self, output: str, inputs: Dict[str, Any]) -> str:
        """
        Post-process the generated output.

        Override this method to transform the output after generation.

        Args:
            output: Raw generated text.
            inputs: Original input values.

        Returns:
            Processed output.
        """
        return output.strip()

    def execute(
        self,
        inputs: Dict[str, Any],
        provider: Optional[LLMProvider] = None,
        provider_type: ProviderType = "openai",
        options: Optional[GenerationOptions] = None,
    ) -> ToolExecutionResult:
        """
        Execute the tool with the given inputs.

        Args:
            inputs: Dictionary of input values.
            provider: Optional pre-configured LLM provider.
            provider_type: Type of provider to use if not provided.
            options: Optional generation options.

        Returns:
            ToolExecutionResult with the generated content.
        """
        start_time = time.time()

        try:
            # Validate inputs
            errors = self.validate_inputs(inputs)
            if errors:
                return ToolExecutionResult(
                    success=False,
                    tool_id=self.id,
                    error="; ".join(errors),
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            # Pre-process inputs
            processed_inputs = self.pre_process(inputs)

            # Build prompt
            prompt = self.build_prompt(processed_inputs)

            # Get or create provider
            if provider is None:
                provider = create_provider_from_env(provider_type)

            # Set up generation options
            if options is None:
                options = GenerationOptions(
                    temperature=self.default_temperature,
                    max_tokens=self.default_max_tokens,
                )

            # Add system prompt if defined
            if self.system_prompt:
                full_prompt = f"{self.system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            # Generate text
            logger.info(f"Executing tool '{self.id}' with provider '{provider_type}'")
            output = generate_text(full_prompt, provider, options)

            # Post-process output
            processed_output = self.post_process(output, processed_inputs)

            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Tool '{self.id}' completed in {execution_time_ms}ms")

            return ToolExecutionResult(
                success=True,
                tool_id=self.id,
                output=processed_output,
                execution_time_ms=execution_time_ms,
                metadata={
                    "provider": provider_type,
                    "output_format": self.output_format.value,
                }
            )

        except TextGenerationError as e:
            logger.error(f"Tool '{self.id}' generation error: {e}")
            return ToolExecutionResult(
                success=False,
                tool_id=self.id,
                error=f"Generation failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            logger.exception(f"Tool '{self.id}' unexpected error: {e}")
            return ToolExecutionResult(
                success=False,
                tool_id=self.id,
                error=f"Unexpected error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    def execute_variations(
        self,
        inputs: Dict[str, Any],
        variation_count: int = 2,
        provider: Optional[LLMProvider] = None,
        provider_type: ProviderType = "openai",
        include_scores: bool = True,
        keywords: Optional[List[str]] = None,
    ) -> VariationGenerationResult:
        """
        Execute the tool multiple times with different parameters to generate variations.

        Args:
            inputs: Dictionary of input values.
            variation_count: Number of variations to generate (2-3).
            provider: Optional pre-configured LLM provider.
            provider_type: Type of provider to use if not provided.
            include_scores: Whether to calculate scores for each variation.
            keywords: Keywords for SEO scoring.

        Returns:
            VariationGenerationResult with all generated variations.
        """
        start_time = time.time()
        variation_count = max(2, min(3, variation_count))

        # Validate inputs first
        errors = self.validate_inputs(inputs)
        if errors:
            return VariationGenerationResult(
                success=False,
                tool_id=self.id,
                variations=[],
                error="; ".join(errors),
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Define variation configurations
        variation_configs = [
            {
                "label": "A",
                "temperature": self.default_temperature,
                "prompt_style": "standard",
                "prompt_modifier": "",
            },
            {
                "label": "B",
                "temperature": min(1.0, self.default_temperature + 0.2),
                "prompt_style": "creative",
                "prompt_modifier": "\n\nBe more creative and engaging in your response.",
            },
            {
                "label": "C",
                "temperature": max(0.3, self.default_temperature - 0.2),
                "prompt_style": "concise",
                "prompt_modifier": "\n\nBe more concise and direct in your response.",
            },
        ]

        variations: List[ContentVariation] = []

        try:
            # Pre-process inputs once
            processed_inputs = self.pre_process(inputs)
            base_prompt = self.build_prompt(processed_inputs)

            # Add system prompt if defined
            if self.system_prompt:
                base_prompt = f"{self.system_prompt}\n\n{base_prompt}"

            # Get or create provider
            if provider is None:
                provider = create_provider_from_env(provider_type)

            # Generate each variation
            for i in range(variation_count):
                config = variation_configs[i]

                options = GenerationOptions(
                    temperature=config["temperature"],
                    max_tokens=self.default_max_tokens,
                )

                # Modify prompt based on style
                full_prompt = base_prompt + config["prompt_modifier"]

                logger.info(
                    f"Generating variation {config['label']} for tool '{self.id}' "
                    f"(temp={config['temperature']})"
                )

                try:
                    output = generate_text(full_prompt, provider, options)
                    processed_output = self.post_process(output, processed_inputs)

                    # Calculate scores if requested
                    scores = None
                    if include_scores:
                        try:
                            from ..scoring import score_content
                            scores = score_content(
                                text=processed_output,
                                keywords=keywords,
                                content_type=self.category.value if hasattr(self.category, 'value') else str(self.category),
                            )
                        except Exception as score_error:
                            logger.warning(f"Failed to score variation: {score_error}")

                    variation = ContentVariation(
                        id=str(uuid.uuid4()),
                        content=processed_output,
                        label=config["label"],
                        temperature=config["temperature"],
                        prompt_style=config["prompt_style"],
                        scores=scores,
                    )
                    variations.append(variation)

                except TextGenerationError as e:
                    logger.error(f"Failed to generate variation {config['label']}: {e}")
                    # Continue with other variations

            if not variations:
                return VariationGenerationResult(
                    success=False,
                    tool_id=self.id,
                    variations=[],
                    error="All variation generations failed",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Generated {len(variations)} variations for tool '{self.id}' "
                f"in {execution_time_ms}ms"
            )

            return VariationGenerationResult(
                success=True,
                tool_id=self.id,
                variations=variations,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            logger.exception(f"Tool '{self.id}' variation generation error: {e}")
            return VariationGenerationResult(
                success=False,
                tool_id=self.id,
                variations=variations,  # Return any successful variations
                error=f"Unexpected error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )


# ==========================================================================
# Helper functions for creating common input fields
# ==========================================================================

def text_field(
    name: str,
    label: str,
    description: str = "",
    required: bool = True,
    placeholder: str = "",
    min_length: int = 1,
    max_length: int = 500,
) -> InputField:
    """Create a text input field."""
    return InputField(
        name=name,
        label=label,
        field_type=InputFieldType.TEXT,
        description=description,
        required=required,
        placeholder=placeholder,
        min_length=min_length,
        max_length=max_length,
    )


def textarea_field(
    name: str,
    label: str,
    description: str = "",
    required: bool = True,
    placeholder: str = "",
    min_length: int = 1,
    max_length: int = 5000,
) -> InputField:
    """Create a textarea input field."""
    return InputField(
        name=name,
        label=label,
        field_type=InputFieldType.TEXTAREA,
        description=description,
        required=required,
        placeholder=placeholder,
        min_length=min_length,
        max_length=max_length,
    )


def select_field(
    name: str,
    label: str,
    options: List[Dict[str, str]],
    description: str = "",
    required: bool = True,
    default: Optional[str] = None,
) -> InputField:
    """Create a select dropdown field."""
    return InputField(
        name=name,
        label=label,
        field_type=InputFieldType.SELECT,
        description=description,
        required=required,
        default=default,
        options=options,
    )


def keywords_field(
    name: str = "keywords",
    label: str = "Keywords",
    description: str = "Comma-separated keywords",
    required: bool = False,
    placeholder: str = "keyword1, keyword2, keyword3",
) -> InputField:
    """Create a keywords input field."""
    return InputField(
        name=name,
        label=label,
        field_type=InputFieldType.KEYWORDS,
        description=description,
        required=required,
        placeholder=placeholder,
    )


def number_field(
    name: str,
    label: str,
    description: str = "",
    required: bool = True,
    default: Optional[float] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> InputField:
    """Create a number input field."""
    return InputField(
        name=name,
        label=label,
        field_type=InputFieldType.NUMBER,
        description=description,
        required=required,
        default=default,
        min_value=min_value,
        max_value=max_value,
    )


def boolean_field(
    name: str,
    label: str,
    description: str = "",
    default: bool = False,
) -> InputField:
    """Create a boolean toggle field."""
    return InputField(
        name=name,
        label=label,
        field_type=InputFieldType.BOOLEAN,
        description=description,
        required=False,
        default=default,
    )


# Common select options used across multiple tools
TONE_OPTIONS = [
    {"label": "Professional", "value": "professional"},
    {"label": "Casual", "value": "casual"},
    {"label": "Friendly", "value": "friendly"},
    {"label": "Formal", "value": "formal"},
    {"label": "Persuasive", "value": "persuasive"},
    {"label": "Informative", "value": "informative"},
    {"label": "Humorous", "value": "humorous"},
    {"label": "Inspiring", "value": "inspiring"},
]

AUDIENCE_OPTIONS = [
    {"label": "General Public", "value": "general"},
    {"label": "Business Professionals", "value": "business"},
    {"label": "Technical Experts", "value": "technical"},
    {"label": "Students", "value": "students"},
    {"label": "Entrepreneurs", "value": "entrepreneurs"},
    {"label": "Marketers", "value": "marketers"},
    {"label": "Developers", "value": "developers"},
    {"label": "Executives", "value": "executives"},
]

LENGTH_OPTIONS = [
    {"label": "Short (100-200 words)", "value": "short"},
    {"label": "Medium (300-500 words)", "value": "medium"},
    {"label": "Long (600-1000 words)", "value": "long"},
    {"label": "Very Long (1000+ words)", "value": "very_long"},
]
