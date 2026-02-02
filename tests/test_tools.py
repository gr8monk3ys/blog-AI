"""
Tests for the tools module.

Tests the BaseTool class, ToolRegistry, and library tools.
"""

import os
import sys
import unittest
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment before imports
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.base import (
    AUDIENCE_OPTIONS,
    LENGTH_OPTIONS,
    TONE_OPTIONS,
    BaseTool,
    boolean_field,
    keywords_field,
    number_field,
    select_field,
    text_field,
    textarea_field,
)
from src.tools.registry import ToolRegistry, get_registry
from src.types.tools import (
    InputField,
    InputFieldType,
    OutputFormat,
    ToolCategory,
    ToolDefinition,
    ToolMetadata,
)


# =============================================================================
# Test Fixtures - Concrete Tool Implementation for Testing
# =============================================================================


class MockTool(BaseTool):
    """A mock tool implementation for testing."""

    @property
    def id(self) -> str:
        return "mock-tool"

    @property
    def name(self) -> str:
        return "Mock Tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing purposes"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BLOG

    @property
    def input_fields(self) -> List[InputField]:
        return [
            text_field("title", "Title", "Enter a title", required=True),
            textarea_field(
                "content", "Content", "Enter content", required=False
            ),
            select_field(
                "tone",
                "Tone",
                TONE_OPTIONS,
                description="Select tone",
                required=False,
                default="professional",
            ),
            keywords_field("keywords", "Keywords", "Enter keywords", required=False),
            number_field(
                "count", "Count", "Enter a count", required=False, default=5, min_value=1, max_value=10
            ),
            boolean_field("featured", "Featured", "Is featured?", default=False),
        ]

    @property
    def prompt_template(self) -> str:
        return "Generate content for: ${title}\nTone: ${tone}\nContent: ${content}"

    @property
    def output_format(self) -> OutputFormat:
        return OutputFormat.MARKDOWN

    @property
    def tags(self) -> List[str]:
        return ["test", "mock", "blog"]

    @property
    def icon(self) -> str:
        return "test-icon"

    @property
    def estimated_time_seconds(self) -> int:
        return 10


class PremiumMockTool(BaseTool):
    """A premium mock tool for testing."""

    @property
    def id(self) -> str:
        return "premium-mock-tool"

    @property
    def name(self) -> str:
        return "Premium Mock Tool"

    @property
    def description(self) -> str:
        return "A premium mock tool"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.BUSINESS

    @property
    def input_fields(self) -> List[InputField]:
        return [text_field("input", "Input", "Enter input")]

    @property
    def prompt_template(self) -> str:
        return "Process: ${input}"

    @property
    def is_premium(self) -> bool:
        return True

    @property
    def tags(self) -> List[str]:
        return ["premium", "business"]


class BetaMockTool(BaseTool):
    """A beta mock tool for testing."""

    @property
    def id(self) -> str:
        return "beta-mock-tool"

    @property
    def name(self) -> str:
        return "Beta Mock Tool"

    @property
    def description(self) -> str:
        return "A beta mock tool"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SEO

    @property
    def input_fields(self) -> List[InputField]:
        return [text_field("query", "Query", "Enter query")]

    @property
    def prompt_template(self) -> str:
        return "Analyze: ${query}"

    @property
    def is_beta(self) -> bool:
        return True

    @property
    def tags(self) -> List[str]:
        return ["beta", "seo", "test"]


# =============================================================================
# Field Helper Tests
# =============================================================================


class TestFieldHelpers(unittest.TestCase):
    """Tests for field helper functions."""

    def test_text_field_creates_correct_type(self):
        """text_field should create TEXT type field."""
        field = text_field("name", "Name", "Enter name")
        self.assertEqual(field.field_type, InputFieldType.TEXT)
        self.assertEqual(field.name, "name")
        self.assertEqual(field.label, "Name")

    def test_textarea_field_creates_correct_type(self):
        """textarea_field should create TEXTAREA type field."""
        field = textarea_field("content", "Content", "Enter content")
        self.assertEqual(field.field_type, InputFieldType.TEXTAREA)

    def test_select_field_creates_correct_type(self):
        """select_field should create SELECT type field with options."""
        options = [{"value": "a", "label": "Option A"}]
        field = select_field("choice", "Choice", options, description="Pick one")
        self.assertEqual(field.field_type, InputFieldType.SELECT)
        self.assertEqual(field.options, options)

    def test_keywords_field_creates_correct_type(self):
        """keywords_field should create KEYWORDS type field."""
        field = keywords_field("tags", "Tags", "Enter tags")
        self.assertEqual(field.field_type, InputFieldType.KEYWORDS)

    def test_number_field_creates_correct_type(self):
        """number_field should create NUMBER type field with constraints."""
        field = number_field("count", "Count", "Enter count", min_value=1, max_value=100)
        self.assertEqual(field.field_type, InputFieldType.NUMBER)
        self.assertEqual(field.min_value, 1)
        self.assertEqual(field.max_value, 100)

    def test_boolean_field_creates_correct_type(self):
        """boolean_field should create BOOLEAN type field."""
        field = boolean_field("enabled", "Enabled", "Is enabled?")
        self.assertEqual(field.field_type, InputFieldType.BOOLEAN)

    def test_field_with_default_value(self):
        """Fields should accept default values."""
        field = number_field("count", "Count", "Enter count", default=42)
        self.assertEqual(field.default, 42)

    def test_field_required_flag(self):
        """Fields should respect required flag."""
        required_field = text_field("name", "Name", "Enter name", required=True)
        optional_field = text_field("name", "Name", "Enter name", required=False)
        self.assertTrue(required_field.required)
        self.assertFalse(optional_field.required)


class TestPredefinedOptions(unittest.TestCase):
    """Tests for predefined option constants."""

    def test_tone_options_has_entries(self):
        """TONE_OPTIONS should have tone options."""
        self.assertGreater(len(TONE_OPTIONS), 0)
        # Check structure
        for option in TONE_OPTIONS:
            self.assertIn("value", option)
            self.assertIn("label", option)

    def test_audience_options_has_entries(self):
        """AUDIENCE_OPTIONS should have audience options."""
        self.assertGreater(len(AUDIENCE_OPTIONS), 0)

    def test_length_options_has_entries(self):
        """LENGTH_OPTIONS should have length options."""
        self.assertGreater(len(LENGTH_OPTIONS), 0)


# =============================================================================
# BaseTool Tests
# =============================================================================


class TestBaseToolDefinition(unittest.TestCase):
    """Tests for BaseTool.get_definition()."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = MockTool()

    def test_get_definition_returns_tool_definition(self):
        """get_definition should return a ToolDefinition object."""
        definition = self.tool.get_definition()
        self.assertIsInstance(definition, ToolDefinition)

    def test_definition_contains_metadata(self):
        """Definition should contain correct metadata."""
        definition = self.tool.get_definition()
        self.assertEqual(definition.metadata.id, "mock-tool")
        self.assertEqual(definition.metadata.name, "Mock Tool")
        self.assertEqual(definition.metadata.category, ToolCategory.BLOG)

    def test_definition_contains_input_schema(self):
        """Definition should contain input schema."""
        definition = self.tool.get_definition()
        self.assertIsNotNone(definition.input_schema)
        self.assertGreater(len(definition.input_schema.fields), 0)

    def test_definition_contains_output_schema(self):
        """Definition should contain output schema."""
        definition = self.tool.get_definition()
        self.assertIsNotNone(definition.output_schema)
        self.assertEqual(definition.output_schema.format, OutputFormat.MARKDOWN)

    def test_definition_is_cached(self):
        """Definition should be cached after first call."""
        definition1 = self.tool.get_definition()
        definition2 = self.tool.get_definition()
        # Same object reference (cached)
        self.assertIs(definition1, definition2)


class TestBaseToolValidation(unittest.TestCase):
    """Tests for BaseTool.validate_inputs()."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = MockTool()

    def test_valid_inputs_returns_empty_list(self):
        """Valid inputs should return empty error list."""
        inputs = {"title": "Test Title"}
        errors = self.tool.validate_inputs(inputs)
        self.assertEqual(errors, [])

    def test_missing_required_field_returns_error(self):
        """Missing required field should return error."""
        inputs = {}  # Missing required 'title'
        errors = self.tool.validate_inputs(inputs)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("title" in e.lower() or "required" in e.lower() for e in errors))

    def test_optional_field_can_be_missing(self):
        """Optional fields should not cause errors when missing."""
        inputs = {"title": "Test"}  # 'content' is optional
        errors = self.tool.validate_inputs(inputs)
        self.assertEqual(errors, [])

    def test_number_field_min_constraint(self):
        """Number field should validate min constraint."""
        inputs = {"title": "Test", "count": 0}  # count min is 1
        errors = self.tool.validate_inputs(inputs)
        self.assertGreater(len(errors), 0)

    def test_number_field_max_constraint(self):
        """Number field should validate max constraint."""
        inputs = {"title": "Test", "count": 100}  # count max is 10
        errors = self.tool.validate_inputs(inputs)
        self.assertGreater(len(errors), 0)


class TestBaseToolPromptBuilding(unittest.TestCase):
    """Tests for BaseTool.build_prompt()."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = MockTool()

    def test_build_prompt_substitutes_variables(self):
        """build_prompt should substitute template variables."""
        inputs = {"title": "My Title", "tone": "casual", "content": "My content"}
        prompt = self.tool.build_prompt(inputs)
        self.assertIn("My Title", prompt)
        self.assertIn("casual", prompt)
        self.assertIn("My content", prompt)

    def test_build_prompt_uses_defaults_for_missing(self):
        """build_prompt should use defaults for missing optional fields."""
        inputs = {"title": "My Title"}  # tone and content have defaults
        prompt = self.tool.build_prompt(inputs)
        self.assertIn("My Title", prompt)
        self.assertIn("professional", prompt)  # default tone

    def test_build_prompt_handles_missing_without_default(self):
        """build_prompt should handle missing fields gracefully."""
        inputs = {"title": "Test"}
        # Should not raise an error
        prompt = self.tool.build_prompt(inputs)
        self.assertIsInstance(prompt, str)


class TestBaseToolExecution(unittest.TestCase):
    """Tests for BaseTool.execute()."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = MockTool()

    @patch("src.tools.base.generate_text")
    def test_execute_returns_result(self, mock_generate):
        """execute should return ToolExecutionResult."""
        mock_generate.return_value = "Generated content here"

        inputs = {"title": "Test Title"}
        result = self.tool.execute(inputs)

        self.assertTrue(result.success)
        self.assertEqual(result.output, "Generated content here")

    @patch("src.tools.base.generate_text")
    def test_execute_includes_metadata(self, mock_generate):
        """execute should include metadata in result."""
        mock_generate.return_value = "Output"

        inputs = {"title": "Test"}
        result = self.tool.execute(inputs)

        # tool_id is a top-level field, not in metadata
        self.assertEqual(result.tool_id, "mock-tool")
        # metadata contains provider and output_format
        self.assertIsNotNone(result.metadata)
        self.assertIn("output_format", result.metadata)

    @patch("src.tools.base.generate_text")
    def test_execute_with_invalid_inputs_returns_failure(self, mock_generate):
        """execute with invalid inputs should return failure."""
        inputs = {}  # Missing required title
        result = self.tool.execute(inputs)

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)

    @patch("src.tools.base.generate_text")
    def test_execute_handles_generation_error(self, mock_generate):
        """execute should handle text generation errors."""
        from src.text_generation.core import TextGenerationError

        mock_generate.side_effect = TextGenerationError("API Error")

        inputs = {"title": "Test"}
        result = self.tool.execute(inputs)

        self.assertFalse(result.success)
        self.assertIn("API Error", result.error)

    @patch("src.tools.base.generate_text")
    def test_execute_tracks_execution_time(self, mock_generate):
        """execute should track execution time."""
        mock_generate.return_value = "Output"

        inputs = {"title": "Test"}
        result = self.tool.execute(inputs)

        self.assertIsNotNone(result.execution_time_ms)
        self.assertGreaterEqual(result.execution_time_ms, 0)


# =============================================================================
# ToolRegistry Tests
# =============================================================================


class TestToolRegistryBasics(unittest.TestCase):
    """Tests for basic ToolRegistry operations."""

    def setUp(self):
        """Set up a fresh registry for each test."""
        self.registry = ToolRegistry()

    def test_register_tool(self):
        """register should add tool to registry."""
        tool = MockTool()
        self.registry.register(tool)
        self.assertTrue(self.registry.has_tool("mock-tool"))

    def test_get_tool_returns_registered_tool(self):
        """get_tool should return the registered tool."""
        tool = MockTool()
        self.registry.register(tool)
        retrieved = self.registry.get_tool("mock-tool")
        self.assertEqual(retrieved.id, tool.id)

    def test_get_tool_raises_for_unknown(self):
        """get_tool should raise ToolNotFoundError for unknown tool."""
        from src.tools.registry import ToolNotFoundError

        with self.assertRaises(ToolNotFoundError):
            self.registry.get_tool("nonexistent-tool")

    def test_has_tool_returns_false_for_unknown(self):
        """has_tool should return False for unknown tool."""
        self.assertFalse(self.registry.has_tool("nonexistent"))

    def test_unregister_tool(self):
        """unregister should remove tool from registry."""
        tool = MockTool()
        self.registry.register(tool)
        result = self.registry.unregister("mock-tool")
        self.assertTrue(result)
        self.assertFalse(self.registry.has_tool("mock-tool"))

    def test_unregister_unknown_returns_false(self):
        """unregister should return False for unknown tool."""
        result = self.registry.unregister("nonexistent")
        self.assertFalse(result)

    def test_get_definition(self):
        """get_definition should return tool definition."""
        tool = MockTool()
        self.registry.register(tool)
        definition = self.registry.get_definition("mock-tool")
        self.assertIsInstance(definition, ToolDefinition)
        self.assertEqual(definition.metadata.id, "mock-tool")


class TestToolRegistryListing(unittest.TestCase):
    """Tests for ToolRegistry.list_tools()."""

    def setUp(self):
        """Set up registry with multiple tools."""
        self.registry = ToolRegistry()
        self.registry.register(MockTool())
        self.registry.register(PremiumMockTool())
        self.registry.register(BetaMockTool())

    def test_list_tools_returns_all(self):
        """list_tools should return all tools by default."""
        result = self.registry.list_tools()
        self.assertEqual(result.total, 3)

    def test_list_tools_filter_by_category(self):
        """list_tools should filter by category."""
        result = self.registry.list_tools(category=ToolCategory.BLOG)
        self.assertEqual(result.total, 1)
        self.assertEqual(result.tools[0].id, "mock-tool")

    def test_list_tools_filter_by_tags(self):
        """list_tools should filter by tags."""
        result = self.registry.list_tools(tags=["test"])
        # mock-tool and beta-mock-tool have 'test' tag
        self.assertGreaterEqual(result.total, 1)

    def test_list_tools_search(self):
        """list_tools should search by name/description."""
        result = self.registry.list_tools(search="Premium")
        self.assertEqual(result.total, 1)
        self.assertEqual(result.tools[0].id, "premium-mock-tool")

    def test_list_tools_exclude_premium(self):
        """list_tools should exclude premium tools when requested."""
        result = self.registry.list_tools(include_premium=False)
        tool_ids = [t.id for t in result.tools]
        self.assertNotIn("premium-mock-tool", tool_ids)

    def test_list_tools_exclude_beta(self):
        """list_tools should exclude beta tools when requested."""
        result = self.registry.list_tools(include_beta=False)
        tool_ids = [t.id for t in result.tools]
        self.assertNotIn("beta-mock-tool", tool_ids)

    def test_list_tools_pagination_limit(self):
        """list_tools should respect limit parameter."""
        result = self.registry.list_tools(limit=2)
        self.assertEqual(len(result.tools), 2)
        self.assertEqual(result.total, 3)  # Total unchanged

    def test_list_tools_pagination_offset(self):
        """list_tools should respect offset parameter."""
        result = self.registry.list_tools(offset=2, limit=10)
        self.assertEqual(len(result.tools), 1)  # Only 1 remaining after offset


class TestToolRegistryCategories(unittest.TestCase):
    """Tests for category-related registry operations."""

    def setUp(self):
        """Set up registry with multiple tools."""
        self.registry = ToolRegistry()
        self.registry.register(MockTool())
        self.registry.register(PremiumMockTool())
        self.registry.register(BetaMockTool())

    def test_list_categories(self):
        """list_categories should return all categories with counts."""
        categories = self.registry.list_categories()
        self.assertGreater(len(categories), 0)
        # Each category should have a tool_count
        for cat in categories:
            self.assertIsNotNone(cat.tool_count)

    def test_get_tools_by_category(self):
        """get_tools_by_category should return tools in category."""
        tools = self.registry.get_tools_by_category(ToolCategory.BLOG)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].id, "mock-tool")


class TestToolRegistryExecution(unittest.TestCase):
    """Tests for ToolRegistry.execute()."""

    def setUp(self):
        """Set up registry with tool."""
        self.registry = ToolRegistry()
        self.registry.register(MockTool())

    @patch("src.tools.base.generate_text")
    def test_execute_routes_to_correct_tool(self, mock_generate):
        """execute should route request to correct tool."""
        from src.types.tools import ToolExecutionRequest

        mock_generate.return_value = "Generated output"

        request = ToolExecutionRequest(
            tool_id="mock-tool", inputs={"title": "Test Title"}
        )
        result = self.registry.execute(request)

        self.assertTrue(result.success)
        self.assertEqual(result.output, "Generated output")

    def test_execute_returns_failure_for_unknown_tool(self):
        """execute should return failure result for unknown tool."""
        from src.types.tools import ToolExecutionRequest

        request = ToolExecutionRequest(tool_id="nonexistent", inputs={})
        result = self.registry.execute(request)

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)


class TestToolRegistryStats(unittest.TestCase):
    """Tests for ToolRegistry.get_stats()."""

    def setUp(self):
        """Set up registry with tools."""
        self.registry = ToolRegistry()
        self.registry.register(MockTool())
        self.registry.register(PremiumMockTool())
        self.registry.register(BetaMockTool())

    def test_get_stats_returns_counts(self):
        """get_stats should return tool counts."""
        stats = self.registry.get_stats()
        self.assertEqual(stats["total_tools"], 3)

    def test_get_stats_includes_category_breakdown(self):
        """get_stats should include category breakdown."""
        stats = self.registry.get_stats()
        self.assertIn("categories", stats)

    def test_get_stats_counts_premium_and_beta(self):
        """get_stats should count premium and beta tools."""
        stats = self.registry.get_stats()
        self.assertEqual(stats["premium_tools"], 1)
        self.assertEqual(stats["beta_tools"], 1)


class TestGlobalRegistry(unittest.TestCase):
    """Tests for global registry singleton."""

    def test_get_registry_returns_instance(self):
        """get_registry should return ToolRegistry instance."""
        registry = get_registry()
        self.assertIsInstance(registry, ToolRegistry)

    def test_get_registry_returns_same_instance(self):
        """get_registry should return singleton instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        self.assertIs(registry1, registry2)


# =============================================================================
# Library Tool Tests
# =============================================================================


class TestLibraryToolsStructure(unittest.TestCase):
    """Tests for library tools following correct pattern."""

    def test_blog_title_tool_exists(self):
        """Blog title generator tool should be discoverable."""
        try:
            from src.tools.library.blog.blog_title import BlogTitleGeneratorTool

            tool = BlogTitleGeneratorTool()
            self.assertEqual(tool.id, "blog-title-generator")
            self.assertEqual(tool.category, ToolCategory.BLOG)
        except ImportError:
            self.skipTest("Blog title tool not available")

    def test_summarizer_tool_exists(self):
        """Summarizer tool should be discoverable."""
        try:
            from src.tools.library.rewriting.summarizer import SummarizerTool

            tool = SummarizerTool()
            self.assertEqual(tool.id, "summarizer")
            self.assertEqual(tool.category, ToolCategory.REWRITING)
        except ImportError:
            self.skipTest("Summarizer tool not available")

    def test_library_tools_have_required_properties(self):
        """Library tools should have all required properties."""
        try:
            from src.tools.library.blog.blog_title import BlogTitleGeneratorTool

            tool = BlogTitleGeneratorTool()
            # Check all required properties exist and are valid
            self.assertIsNotNone(tool.id)
            self.assertIsNotNone(tool.name)
            self.assertIsNotNone(tool.description)
            self.assertIsNotNone(tool.category)
            self.assertIsNotNone(tool.input_fields)
            self.assertIsNotNone(tool.prompt_template)
            self.assertGreater(len(tool.input_fields), 0)
        except ImportError:
            self.skipTest("Blog title tool not available")


class TestAutoDiscovery(unittest.TestCase):
    """Tests for tool auto-discovery."""

    def test_auto_discover_finds_tools(self):
        """auto_discover should find and register tools."""
        registry = ToolRegistry()
        count = registry.auto_discover()
        # Should find at least some tools
        self.assertGreater(count, 0)

    def test_auto_discover_registers_tools(self):
        """auto_discover should register tools in registry."""
        registry = ToolRegistry()
        registry.auto_discover()
        # Should have tools registered
        stats = registry.get_stats()
        self.assertGreater(stats["total_tools"], 0)


if __name__ == "__main__":
    unittest.main()
