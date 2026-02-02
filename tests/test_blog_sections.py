"""
Tests for blog section generators.

Tests cover:
- Introduction generation and hook/thesis extraction
- Conclusion generation and summary/CTA extraction
- FAQ generation and parsing
- Code example generation and markdown cleanup
"""

from unittest.mock import MagicMock, patch

import pytest

from src.blog_sections.code_examples_generator import (
    CodeExamplesGenerationError,
    generate_code_example,
    generate_code_examples_for_topic,
    generate_code_examples_section,
    generate_comparative_code_examples,
)
from src.blog_sections.conclusion_generator import (
    ConclusionGenerationError,
    extract_summary_and_cta,
    generate_conclusion,
    generate_conclusion_with_key_points,
)
from src.blog_sections.faq_generator import (
    FAQ,
    FAQGenerationError,
    generate_faq_from_questions,
    generate_faqs,
    parse_faqs,
)
from src.blog_sections.introduction_generator import (
    IntroductionGenerationError,
    extract_hook_and_thesis,
    generate_introduction,
    generate_introduction_with_research,
)
from src.types.providers import GenerationOptions, LLMProvider, OpenAIConfig


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    config = OpenAIConfig(api_key="test-key", model="gpt-4")
    return LLMProvider(type="openai", config=config)


@pytest.fixture
def generation_options():
    """Create generation options for testing."""
    return GenerationOptions()


# =============================================================================
# Tests for Introduction Generator
# =============================================================================


class TestIntroductionGenerator:
    """Tests for introduction generation."""

    def test_generate_introduction_basic(self, mock_provider):
        """Test basic introduction generation."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            # First call: generate introduction, second call: extract hook/thesis
            mock_gen.side_effect = [
                "This is an engaging introduction about AI. It hooks readers in. The thesis is that AI will change everything.",
                "Hook: This is an engaging introduction about AI.\nThesis: AI will change everything.",
            ]

            result = generate_introduction(
                title="Introduction to AI",
                keywords=["AI", "machine learning"],
                tone="informative",
                provider=mock_provider,
            )

            assert result.content is not None
            assert result.hook == "This is an engaging introduction about AI."
            assert result.thesis == "AI will change everything."

    def test_generate_introduction_with_outline(self, mock_provider):
        """Test introduction generation with outline."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "Introduction content with outline context.",
                "Hook: Opening statement.\nThesis: Main thesis.",
            ]

            result = generate_introduction(
                title="Test Title",
                outline="1. Section 1\n2. Section 2",
                provider=mock_provider,
            )

            # Verify outline was included in prompt
            call_args = mock_gen.call_args_list[0]
            assert "Outline" in str(call_args)

    def test_generate_introduction_with_target_audience(self, mock_provider):
        """Test introduction generation with target audience."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "Introduction for developers.",
                "Hook: Developers need this.\nThesis: Learn modern practices.",
            ]

            result = generate_introduction(
                title="Test Title",
                target_audience="Software developers",
                provider=mock_provider,
            )

            # Verify target audience was included in prompt
            call_args = mock_gen.call_args_list[0]
            assert "Software developers" in str(call_args)

    def test_generate_introduction_error_handling(self, mock_provider):
        """Test that errors are wrapped in IntroductionGenerationError."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            mock_gen.side_effect = Exception("API error")

            with pytest.raises(IntroductionGenerationError) as exc_info:
                generate_introduction(title="Test", provider=mock_provider)

            assert "Error generating introduction" in str(exc_info.value)

    def test_generate_introduction_with_research(self, mock_provider):
        """Test introduction generation with research results."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "Research-backed introduction.",
                "Hook: Studies show.\nThesis: Evidence supports.",
            ]

            result = generate_introduction_with_research(
                title="Test Title",
                research_results={"findings": "Important data"},
                provider=mock_provider,
            )

            assert result.content == "Research-backed introduction."


class TestExtractHookAndThesis:
    """Tests for hook and thesis extraction."""

    def test_extract_hook_and_thesis_basic(self, mock_provider):
        """Test basic hook and thesis extraction."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            mock_gen.return_value = "Hook: The attention grabber.\nThesis: The main point."

            hook, thesis = extract_hook_and_thesis(
                "Sample introduction text", mock_provider
            )

            assert hook == "The attention grabber."
            assert thesis == "The main point."

    def test_extract_hook_and_thesis_multiline(self, mock_provider):
        """Test extraction with multiline response."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            mock_gen.return_value = """
            Hook: First line of the hook.

            Thesis: Main thesis statement here.
            """

            hook, thesis = extract_hook_and_thesis(
                "Sample introduction text", mock_provider
            )

            assert hook == "First line of the hook."
            assert thesis == "Main thesis statement here."

    def test_extract_hook_and_thesis_error(self, mock_provider):
        """Test error handling in extraction."""
        with patch("src.blog_sections.introduction_generator.generate_text") as mock_gen:
            mock_gen.side_effect = Exception("Extraction failed")

            with pytest.raises(IntroductionGenerationError) as exc_info:
                extract_hook_and_thesis("Sample text", mock_provider)

            assert "extracting hook and thesis" in str(exc_info.value)


# =============================================================================
# Tests for Conclusion Generator
# =============================================================================


class TestConclusionGenerator:
    """Tests for conclusion generation."""

    def test_generate_conclusion_basic(self, mock_provider):
        """Test basic conclusion generation."""
        with patch("src.blog_sections.conclusion_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "In conclusion, the key points are summarized here. Take action now!",
                "Summary: Key points are summarized.\nCall to Action: Take action now!",
            ]

            result = generate_conclusion(
                title="Test Article",
                content="Full article content here...",
                keywords=["test", "article"],
                provider=mock_provider,
            )

            assert result.content is not None
            assert result.summary == "Key points are summarized."
            assert result.call_to_action == "Take action now!"

    def test_generate_conclusion_without_cta(self, mock_provider):
        """Test conclusion generation without call to action."""
        with patch("src.blog_sections.conclusion_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "Simple conclusion without CTA.",
                "Summary: Simple summary.\nCall to Action: None",
            ]

            result = generate_conclusion(
                title="Test",
                content="Content",
                include_call_to_action=False,
                provider=mock_provider,
            )

            assert result.call_to_action is None

    def test_generate_conclusion_error_handling(self, mock_provider):
        """Test error handling in conclusion generation."""
        with patch("src.blog_sections.conclusion_generator.generate_text") as mock_gen:
            mock_gen.side_effect = Exception("Generation failed")

            with pytest.raises(ConclusionGenerationError) as exc_info:
                generate_conclusion(
                    title="Test", content="Content", provider=mock_provider
                )

            assert "Error generating conclusion" in str(exc_info.value)

    def test_generate_conclusion_with_key_points(self, mock_provider):
        """Test conclusion generation with key points."""
        with patch("src.blog_sections.conclusion_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "Conclusion from key points.",
                "Summary: Key points summary.\nCall to Action: Act now!",
            ]

            result = generate_conclusion_with_key_points(
                title="Test",
                key_points=["Point 1", "Point 2", "Point 3"],
                provider=mock_provider,
            )

            assert result.content == "Conclusion from key points."


class TestExtractSummaryAndCta:
    """Tests for summary and CTA extraction."""

    def test_extract_summary_and_cta_basic(self, mock_provider):
        """Test basic summary and CTA extraction."""
        with patch("src.blog_sections.conclusion_generator.generate_text") as mock_gen:
            mock_gen.return_value = (
                "Summary: The main points.\nCall to Action: Subscribe now!"
            )

            summary, cta = extract_summary_and_cta("Conclusion text", mock_provider)

            assert summary == "The main points."
            assert cta == "Subscribe now!"

    def test_extract_summary_and_cta_no_cta(self, mock_provider):
        """Test extraction when no CTA present."""
        with patch("src.blog_sections.conclusion_generator.generate_text") as mock_gen:
            mock_gen.return_value = "Summary: The main points.\nCall to Action: None"

            summary, cta = extract_summary_and_cta("Conclusion text", mock_provider)

            assert summary == "The main points."
            assert cta is None


# =============================================================================
# Tests for FAQ Generator
# =============================================================================


class TestFAQGenerator:
    """Tests for FAQ generation."""

    def test_generate_faqs_basic(self, mock_provider):
        """Test basic FAQ generation."""
        with patch("src.blog_sections.faq_generator.generate_text") as mock_gen:
            mock_gen.return_value = """
            Q1: What is AI?
            A1: AI stands for Artificial Intelligence.

            Q2: How does it work?
            A2: It uses algorithms to process data.

            Q3: Is it safe?
            A3: Yes, when properly implemented.
            """

            result = generate_faqs(
                content="Content about AI and machine learning.",
                count=3,
                provider=mock_provider,
            )

            assert result.title == "Frequently Asked Questions"
            assert len(result.faqs) == 3
            assert result.faqs[0].question == "What is AI?"
            assert result.faqs[0].answer == "AI stands for Artificial Intelligence."

    def test_generate_faqs_requests_more_when_needed(self, mock_provider):
        """Test that more FAQs are generated if initial count is insufficient."""
        with patch("src.blog_sections.faq_generator.generate_text") as mock_gen:
            # First call returns only 2 FAQs, second call returns 1 more
            mock_gen.side_effect = [
                """
                Q1: Question 1?
                A1: Answer 1.

                Q2: Question 2?
                A2: Answer 2.
                """,
                """
                Q1: Question 3?
                A1: Answer 3.
                """,
            ]

            result = generate_faqs(content="Content", count=3, provider=mock_provider)

            assert len(result.faqs) == 3
            assert mock_gen.call_count == 2

    def test_generate_faqs_error_handling(self, mock_provider):
        """Test error handling in FAQ generation."""
        with patch("src.blog_sections.faq_generator.generate_text") as mock_gen:
            mock_gen.side_effect = Exception("Generation failed")

            with pytest.raises(FAQGenerationError) as exc_info:
                generate_faqs(content="Content", provider=mock_provider)

            assert "Error generating FAQs" in str(exc_info.value)

    def test_generate_faq_from_questions(self, mock_provider):
        """Test FAQ generation from provided questions."""
        with patch("src.blog_sections.faq_generator.generate_text") as mock_gen:
            mock_gen.side_effect = ["Answer to first question.", "Answer to second question."]

            result = generate_faq_from_questions(
                questions=["First question?", "Second question?"],
                content="Content",
                provider=mock_provider,
            )

            assert len(result.faqs) == 2
            assert result.faqs[0].question == "First question?"
            assert result.faqs[0].answer == "Answer to first question."


class TestParseFAQs:
    """Tests for FAQ parsing."""

    def test_parse_faqs_standard_format(self):
        """Test parsing FAQs in standard format."""
        text = """
        Q1: What is Python?
        A1: Python is a programming language.

        Q2: Why use it?
        A2: It's easy to learn and versatile.
        """

        faqs = parse_faqs(text)

        assert len(faqs) == 2
        assert faqs[0].question == "What is Python?"
        assert faqs[0].answer == "Python is a programming language."
        assert faqs[1].question == "Why use it?"
        assert faqs[1].answer == "It's easy to learn and versatile."

    def test_parse_faqs_with_extra_whitespace(self):
        """Test parsing FAQs with extra whitespace."""
        text = """

        Q1:   What is this?
        A1:   This is a test.


        Q2:   Another question?
        A2:   Another answer.

        """

        faqs = parse_faqs(text)

        assert len(faqs) == 2
        assert faqs[0].question == "What is this?"
        assert faqs[0].answer == "This is a test."

    def test_parse_faqs_empty_text(self):
        """Test parsing empty text."""
        faqs = parse_faqs("")
        assert len(faqs) == 0

    def test_parse_faqs_no_valid_pairs(self):
        """Test parsing text with no valid Q/A pairs."""
        text = "This is just regular text without any Q/A format."
        faqs = parse_faqs(text)
        assert len(faqs) == 0

    def test_parse_faqs_incomplete_pairs(self):
        """Test parsing with incomplete Q/A pairs."""
        text = """
        Q1: Question without answer

        A2: Answer without question

        Q3: Complete question
        A3: Complete answer
        """

        faqs = parse_faqs(text)

        # Should only get the complete pair
        assert len(faqs) == 1
        assert faqs[0].question == "Complete question"


# =============================================================================
# Tests for Code Examples Generator
# =============================================================================


class TestCodeExamplesGenerator:
    """Tests for code examples generation."""

    def test_generate_code_example_basic(self, mock_provider):
        """Test basic code example generation."""
        with patch("src.blog_sections.code_examples_generator.generate_text") as mock_gen:
            mock_gen.return_value = """
def hello_world():
    print("Hello, World!")
"""

            result = generate_code_example(
                language="python",
                description="Print hello world",
                provider=mock_provider,
            )

            assert result.language == "python"
            assert result.description == "Print hello world"
            assert "hello_world" in result.code

    def test_generate_code_example_strips_markdown(self, mock_provider):
        """Test that markdown code blocks are stripped."""
        with patch("src.blog_sections.code_examples_generator.generate_text") as mock_gen:
            mock_gen.return_value = """```python
def hello():
    pass
```"""

            result = generate_code_example(
                language="python", description="Test", provider=mock_provider
            )

            assert not result.code.startswith("```")
            assert not result.code.endswith("```")
            assert "def hello" in result.code

    def test_generate_code_example_error_handling(self, mock_provider):
        """Test error handling in code example generation."""
        with patch("src.blog_sections.code_examples_generator.generate_text") as mock_gen:
            mock_gen.side_effect = Exception("Generation failed")

            with pytest.raises(CodeExamplesGenerationError) as exc_info:
                generate_code_example(
                    language="python", description="Test", provider=mock_provider
                )

            assert "Error generating code example" in str(exc_info.value)

    def test_generate_code_examples_section(self, mock_provider):
        """Test generating a section with multiple code examples."""
        with patch("src.blog_sections.code_examples_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "print('Hello')",
                "console.log('Hello');",
            ]

            result = generate_code_examples_section(
                title="Example Section",
                examples_descriptions=[
                    {"language": "python", "description": "Python hello"},
                    {"language": "javascript", "description": "JS hello"},
                ],
                provider=mock_provider,
            )

            assert result.title == "Example Section"
            assert len(result.examples) == 2
            assert result.examples[0].language == "python"
            assert result.examples[1].language == "javascript"

    def test_generate_code_examples_for_topic(self, mock_provider):
        """Test generating code examples for a topic."""
        with patch("src.blog_sections.code_examples_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                # First call: descriptions
                "Language: Python\nDescription: Implement sorting\n\nLanguage: JavaScript\nDescription: Implement sorting in JS",
                # Second and third calls: actual code
                "def sort(arr): return sorted(arr)",
                "const sort = arr => arr.sort();",
            ]

            result = generate_code_examples_for_topic(
                topic="Sorting Algorithms",
                languages=["Python", "JavaScript"],
                provider=mock_provider,
            )

            assert "Sorting" in result.title
            assert len(result.examples) >= 1

    def test_generate_comparative_code_examples(self, mock_provider):
        """Test generating comparative code examples."""
        with patch("src.blog_sections.code_examples_generator.generate_text") as mock_gen:
            mock_gen.side_effect = [
                "# Python implementation\nresult = sum(range(10))",
                "// JavaScript implementation\nconst result = [...Array(10)].reduce((a,b,i) => a+i, 0);",
            ]

            result = generate_comparative_code_examples(
                task="sum numbers 1-10",
                languages=["Python", "JavaScript"],
                provider=mock_provider,
            )

            assert "sum numbers" in result.title.lower()
            assert len(result.examples) == 2
            assert result.examples[0].language == "Python"
            assert result.examples[1].language == "JavaScript"


# =============================================================================
# Tests for Error Classes
# =============================================================================


class TestErrorClasses:
    """Tests for custom error classes."""

    def test_introduction_generation_error(self):
        """Test IntroductionGenerationError."""
        error = IntroductionGenerationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_conclusion_generation_error(self):
        """Test ConclusionGenerationError."""
        error = ConclusionGenerationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_faq_generation_error(self):
        """Test FAQGenerationError."""
        error = FAQGenerationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_code_examples_generation_error(self):
        """Test CodeExamplesGenerationError."""
        error = CodeExamplesGenerationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
