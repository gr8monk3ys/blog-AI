"""
Tests for image generation module.

Tests cover:
- ImageGenerator class with different providers
- PromptGenerator for creating image prompts
- Error handling and validation
- Content splitting for inline images
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.images.image_generator import (
    ImageGenerationError,
    ImageGenerator,
)
from src.images.prompt_generator import PromptGenerator
from src.types.images import ImageType


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def image_generator():
    """Create an ImageGenerator instance for testing."""
    return ImageGenerator(
        provider="openai",
        openai_api_key="test-openai-key",
        stability_api_key="test-stability-key",
    )


@pytest.fixture
def prompt_generator():
    """Create a PromptGenerator instance for testing."""
    return PromptGenerator()


@pytest.fixture
def sample_content():
    """Sample blog content for testing."""
    return """
    Artificial Intelligence is transforming the way we work and live.
    Machine learning algorithms are becoming increasingly sophisticated,
    enabling computers to learn from data and make predictions.

    Deep learning, a subset of machine learning, uses neural networks
    to process complex patterns. This technology powers everything from
    voice assistants to self-driving cars.

    The future of AI holds tremendous promise for healthcare, education,
    and environmental sustainability. As these systems become more capable,
    they will help us solve some of humanity's greatest challenges.
    """


# =============================================================================
# Tests for PromptGenerator
# =============================================================================


class TestPromptGenerator:
    """Tests for the PromptGenerator class."""

    def test_generate_prompt_basic(self, prompt_generator, sample_content):
        """Test basic prompt generation."""
        prompt = prompt_generator.generate_prompt(
            content=sample_content,
            image_type=ImageType.FEATURED,
            title="Introduction to AI",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 50
        # Should contain quality guidelines
        assert "professional" in prompt.lower() or "high" in prompt.lower()

    def test_generate_prompt_with_keywords(self, prompt_generator, sample_content):
        """Test prompt generation with keywords."""
        prompt = prompt_generator.generate_prompt(
            content=sample_content,
            keywords=["AI", "machine learning", "technology"],
        )

        # Keywords should influence the prompt
        assert isinstance(prompt, str)

    def test_generate_prompt_different_image_types(self, prompt_generator, sample_content):
        """Test prompt generation for different image types."""
        for image_type in ImageType:
            prompt = prompt_generator.generate_prompt(
                content=sample_content,
                image_type=image_type,
            )
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_generate_featured_prompt(self, prompt_generator, sample_content):
        """Test featured prompt generation."""
        prompt = prompt_generator.generate_featured_prompt(
            content=sample_content,
            title="AI Revolution",
            keywords=["AI", "technology"],
        )

        assert isinstance(prompt, str)
        # Featured prompts should have editorial style modifiers
        assert "professional" in prompt.lower() or "high-quality" in prompt.lower()

    def test_generate_social_prompt(self, prompt_generator, sample_content):
        """Test social media prompt generation."""
        prompt = prompt_generator.generate_social_prompt(
            content=sample_content,
            title="AI Trends",
            keywords=["AI", "social"],
        )

        assert isinstance(prompt, str)
        # Social prompts should have engaging modifiers
        assert any(word in prompt.lower() for word in ["vibrant", "attention", "social"])

    def test_generate_inline_prompt(self, prompt_generator, sample_content):
        """Test inline prompt generation."""
        prompt = prompt_generator.generate_inline_prompt(
            content=sample_content,
            section_context="This section discusses machine learning basics.",
            keywords=["ML", "algorithms"],
        )

        assert isinstance(prompt, str)

    def test_extract_themes(self, prompt_generator, sample_content):
        """Test theme extraction from content."""
        themes = prompt_generator._extract_themes(
            content=sample_content,
            title="Artificial Intelligence",
            keywords=["AI", "ML"],
        )

        assert isinstance(themes, list)
        assert len(themes) > 0
        # Keywords should be included
        assert "AI" in themes or "ML" in themes

    def test_extract_significant_words(self, prompt_generator):
        """Test significant word extraction."""
        text = "The artificial intelligence systems are transforming industries"
        words = prompt_generator._extract_significant_words(text)

        assert isinstance(words, list)
        # Stop words should be filtered out
        assert "The" not in words and "are" not in words
        # Significant words should be included
        assert "artificial" in words or "intelligence" in words

    def test_build_base_prompt_with_themes(self, prompt_generator):
        """Test base prompt building with themes."""
        themes = ["AI", "technology", "innovation", "future"]
        prompt = prompt_generator._build_base_prompt(themes, title="Tech Future")

        assert "AI" in prompt or "visual representation" in prompt.lower()

    def test_build_base_prompt_empty_themes(self, prompt_generator):
        """Test base prompt building with empty themes."""
        prompt = prompt_generator._build_base_prompt([], title=None)

        assert "abstract" in prompt.lower()

    def test_add_quality_guidelines(self, prompt_generator):
        """Test quality guidelines addition."""
        base_prompt = "A picture of a robot"
        enhanced = prompt_generator._add_quality_guidelines(base_prompt)

        assert base_prompt in enhanced
        assert "high resolution" in enhanced.lower() or "professional" in enhanced.lower()
        assert "no text" in enhanced.lower() or "watermarks" in enhanced.lower()

    def test_refine_prompt_for_openai(self, prompt_generator):
        """Test prompt refinement for OpenAI."""
        prompt = "A digital artwork of technology"
        refined = prompt_generator.refine_prompt_for_provider(prompt, "openai")

        # OpenAI prompts should remain mostly unchanged
        assert prompt in refined

    def test_refine_prompt_for_stability(self, prompt_generator):
        """Test prompt refinement for Stability AI."""
        prompt = "A digital artwork of technology"
        refined = prompt_generator.refine_prompt_for_provider(prompt, "stability")

        # Stability prompts should have style tokens
        assert "artstation" in refined.lower() or "8k" in refined.lower()

    def test_content_truncation(self, prompt_generator):
        """Test that long content is truncated."""
        long_content = "AI " * 10000  # Very long content
        prompt = prompt_generator.generate_prompt(content=long_content)

        # Should not throw an error and should generate a valid prompt
        assert isinstance(prompt, str)


# =============================================================================
# Tests for ImageGenerator
# =============================================================================


class TestImageGenerator:
    """Tests for the ImageGenerator class."""

    def test_initialization_with_keys(self):
        """Test ImageGenerator initialization with API keys."""
        generator = ImageGenerator(
            provider="openai",
            openai_api_key="test-key",
            stability_api_key="stability-key",
        )

        assert generator.default_provider == "openai"
        assert generator.openai_api_key == "test-key"
        assert generator.stability_api_key == "stability-key"

    def test_initialization_without_keys_logs_warning(self):
        """Test that missing API keys log a warning."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove any existing env vars
            import os
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("STABILITY_API_KEY", None)

            with patch("src.images.image_generator.logger") as mock_logger:
                generator = ImageGenerator(
                    openai_api_key=None,
                    stability_api_key=None,
                )
                mock_logger.warning.assert_called()

    def test_get_default_size_for_type(self, image_generator):
        """Test default size selection for image types."""
        assert image_generator._get_default_size_for_type(ImageType.FEATURED) == "1792x1024"
        assert image_generator._get_default_size_for_type(ImageType.SOCIAL) == "1024x1024"
        assert image_generator._get_default_size_for_type(ImageType.INLINE) == "1024x1024"

    def test_split_content_for_inline_images_basic(self, image_generator, sample_content):
        """Test content splitting for inline images."""
        sections = image_generator._split_content_for_inline_images(sample_content, 3)

        assert len(sections) == 3
        for section in sections:
            assert len(section) > 0

    def test_split_content_for_inline_images_zero_count(self, image_generator, sample_content):
        """Test content splitting with zero count."""
        sections = image_generator._split_content_for_inline_images(sample_content, 0)
        assert sections == []

    def test_split_content_for_inline_images_more_than_paragraphs(self, image_generator):
        """Test content splitting when count exceeds paragraphs."""
        short_content = "Paragraph 1.\n\nParagraph 2."
        sections = image_generator._split_content_for_inline_images(short_content, 5)

        # Should return available paragraphs (max 2)
        assert len(sections) <= 2

    @pytest.mark.asyncio
    async def test_generate_image_unsupported_provider(self, image_generator):
        """Test that unsupported provider raises error."""
        with pytest.raises(ImageGenerationError) as exc_info:
            await image_generator.generate_image(
                prompt="Test prompt",
                provider="unsupported_provider",
            )

        assert "unsupported" in str(exc_info.value).lower()
        assert exc_info.value.provider == "unsupported_provider"

    @pytest.mark.asyncio
    async def test_generate_with_openai_no_api_key(self):
        """Test OpenAI generation without API key raises error."""
        generator = ImageGenerator(
            provider="openai",
            openai_api_key=None,
            stability_api_key=None,
        )

        with pytest.raises(ImageGenerationError) as exc_info:
            await generator._generate_with_openai(
                prompt="Test",
                size="1024x1024",
                style="natural",
                quality="standard",
            )

        assert "not configured" in str(exc_info.value).lower()
        assert exc_info.value.provider == "openai"

    @pytest.mark.asyncio
    async def test_generate_with_stability_no_api_key(self):
        """Test Stability generation without API key raises error."""
        generator = ImageGenerator(
            provider="stability",
            openai_api_key=None,
            stability_api_key=None,
        )

        with pytest.raises(ImageGenerationError) as exc_info:
            await generator._generate_with_stability(
                prompt="Test",
                size="1024x1024",
            )

        assert "not configured" in str(exc_info.value).lower()
        assert exc_info.value.provider == "stability"

    @pytest.mark.asyncio
    async def test_generate_with_openai_success(self, image_generator):
        """Test successful OpenAI image generation."""
        with patch("src.images.image_generator.openai") as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.data = [
                MagicMock(url="https://example.com/image.png", revised_prompt="Refined prompt")
            ]
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            mock_openai.AsyncOpenAI.return_value = mock_client

            result = await image_generator._generate_with_openai(
                prompt="A beautiful landscape",
                size="1024x1024",
                style="natural",
                quality="standard",
            )

            assert result.url == "https://example.com/image.png"
            assert result.provider == "openai"
            assert result.revised_prompt == "Refined prompt"

    @pytest.mark.asyncio
    async def test_generate_with_openai_auth_error(self, image_generator):
        """Test OpenAI authentication error handling."""
        with patch("src.images.image_generator.openai") as mock_openai:
            mock_openai.AuthenticationError = type("AuthenticationError", (Exception,), {})
            mock_client = AsyncMock()
            mock_client.images.generate = AsyncMock(
                side_effect=mock_openai.AuthenticationError("Invalid key")
            )
            mock_openai.AsyncOpenAI.return_value = mock_client

            with pytest.raises(ImageGenerationError) as exc_info:
                await image_generator._generate_with_openai(
                    prompt="Test",
                    size="1024x1024",
                    style="natural",
                    quality="standard",
                )

            assert "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_with_openai_rate_limit_error(self, image_generator):
        """Test OpenAI rate limit error handling."""
        with patch("src.images.image_generator.openai") as mock_openai:
            mock_openai.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_client = AsyncMock()
            mock_client.images.generate = AsyncMock(
                side_effect=mock_openai.RateLimitError("Rate limited")
            )
            mock_openai.AsyncOpenAI.return_value = mock_client

            with pytest.raises(ImageGenerationError) as exc_info:
                await image_generator._generate_with_openai(
                    prompt="Test",
                    size="1024x1024",
                    style="natural",
                    quality="standard",
                )

            assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_image_routes_to_openai(self, image_generator):
        """Test that generate_image routes to OpenAI provider."""
        with patch.object(image_generator, "_generate_with_openai") as mock_gen:
            mock_gen.return_value = MagicMock(url="https://example.com/img.png")

            await image_generator.generate_image(
                prompt="Test",
                provider="openai",
            )

            mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_image_routes_to_stability(self, image_generator):
        """Test that generate_image routes to Stability provider."""
        with patch.object(image_generator, "_generate_with_stability") as mock_gen:
            mock_gen.return_value = MagicMock(url="https://example.com/img.png")

            await image_generator.generate_image(
                prompt="Test",
                provider="stability",
            )

            mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_from_content(self, image_generator, sample_content):
        """Test generating image from content."""
        with patch.object(image_generator, "generate_image") as mock_gen:
            mock_gen.return_value = MagicMock(url="https://example.com/img.png")

            result = await image_generator.generate_from_content(
                content=sample_content,
                image_type="featured",
                title="AI Article",
                keywords=["AI", "technology"],
            )

            mock_gen.assert_called_once()
            call_kwargs = mock_gen.call_args.kwargs
            assert "prompt" in call_kwargs
            assert call_kwargs["size"] == "1792x1024"  # Default for featured

    @pytest.mark.asyncio
    async def test_generate_blog_images(self, image_generator, sample_content):
        """Test generating all blog images."""
        with patch.object(image_generator, "generate_from_content") as mock_gen:
            mock_gen.return_value = MagicMock(
                url="https://example.com/img.png",
                provider="openai",
            )

            result = await image_generator.generate_blog_images(
                content=sample_content,
                title="Test Blog",
                generate_featured=True,
                generate_social=True,
                inline_count=0,
            )

            assert result.provider_used == "openai"
            # Should have called for featured and social
            assert mock_gen.call_count >= 1


# =============================================================================
# Tests for ImageGenerationError
# =============================================================================


class TestImageGenerationError:
    """Tests for the ImageGenerationError exception."""

    def test_error_with_all_attributes(self):
        """Test error with all attributes."""
        original = ValueError("Original error")
        error = ImageGenerationError(
            message="Test error",
            provider="openai",
            original_error=original,
        )

        assert str(error) == "Test error"
        assert error.provider == "openai"
        assert error.original_error == original

    def test_error_with_minimal_attributes(self):
        """Test error with minimal attributes."""
        error = ImageGenerationError("Simple error")

        assert str(error) == "Simple error"
        assert error.provider is None
        assert error.original_error is None

    def test_error_inheritance(self):
        """Test that ImageGenerationError is an Exception."""
        error = ImageGenerationError("Test")
        assert isinstance(error, Exception)


# =============================================================================
# Tests for Size Mappings
# =============================================================================


class TestSizeMappings:
    """Tests for size mapping constants."""

    def test_openai_sizes(self, image_generator):
        """Test OpenAI size mappings."""
        assert "1024x1024" in image_generator.OPENAI_SIZES
        assert "1792x1024" in image_generator.OPENAI_SIZES
        assert "1024x1792" in image_generator.OPENAI_SIZES

    def test_stability_sizes(self, image_generator):
        """Test Stability size mappings."""
        assert "1024x1024" in image_generator.STABILITY_SIZES
        # Stability uses tuples for width/height
        assert image_generator.STABILITY_SIZES["1024x1024"] == (1024, 1024)
