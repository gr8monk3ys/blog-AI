"""
Tests for the text generation core module.

Tests cover:
- generate_text() with different providers
- generate_text_async() with rate limiting
- create_provider_from_env() provider creation
- Error handling for all providers
- Rate limit behavior
"""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest

from src.text_generation.core import (
    LLM_API_TIMEOUT,
    RateLimitError,
    TextGenerationError,
    create_provider_from_env,
    generate_text,
    generate_text_async,
    generate_with_anthropic,
    generate_with_gemini,
    generate_with_openai,
)
from src.text_generation.rate_limiter import OperationType
from src.types.providers import (
    AnthropicConfig,
    GeminiConfig,
    GenerationOptions,
    LLMProvider,
    OpenAIConfig,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def openai_provider():
    """Create an OpenAI provider for testing."""
    config = OpenAIConfig(api_key="test-key", model="gpt-4")
    return LLMProvider(type="openai", config=config)


@pytest.fixture
def anthropic_provider():
    """Create an Anthropic provider for testing."""
    config = AnthropicConfig(api_key="test-key", model="claude-3-opus-20240229")
    return LLMProvider(type="anthropic", config=config)


@pytest.fixture
def gemini_provider():
    """Create a Gemini provider for testing."""
    config = GeminiConfig(api_key="test-key", model="gemini-1.5-flash")
    return LLMProvider(type="gemini", config=config)


@pytest.fixture
def generation_options():
    """Create default generation options for testing."""
    return GenerationOptions(
        temperature=0.7,
        max_tokens=1000,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with successful response."""
    with patch("src.text_generation.core.openai") as mock_module:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Generated OpenAI content"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_module.OpenAI.return_value = mock_client
        yield mock_module


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client with successful response."""
    with patch("src.text_generation.core.anthropic") as mock_module:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated Anthropic content")]
        mock_client.messages.create.return_value = mock_response
        mock_module.Anthropic.return_value = mock_client
        yield mock_module


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client with successful response."""
    with patch("src.text_generation.core.genai") as mock_module:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated Gemini content"
        mock_model.generate_content.return_value = mock_response
        mock_module.GenerativeModel.return_value = mock_model
        yield mock_module


@pytest.fixture
def disable_rate_limit():
    """Disable rate limiting for tests."""
    with patch("src.text_generation.core.get_rate_limiter") as mock:
        mock_limiter = MagicMock()
        mock_limiter.check_limit.return_value = True
        mock_bucket = MagicMock()
        mock_bucket.tokens = 10.0
        mock_bucket.get_wait_time.return_value = 0.0
        mock_limiter._buckets = {OperationType.DEFAULT: mock_bucket}
        mock.return_value = mock_limiter
        yield mock


# =============================================================================
# Tests for generate_with_openai
# =============================================================================


class TestGenerateWithOpenAI:
    """Tests for OpenAI text generation."""

    def test_successful_generation(self, mock_openai_client):
        """Test successful text generation with OpenAI."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        options = GenerationOptions()

        result = generate_with_openai("Test prompt", config, options)

        assert result == "Generated OpenAI content"
        mock_openai_client.OpenAI.assert_called_once_with(
            api_key="test-key", timeout=LLM_API_TIMEOUT
        )

    def test_empty_response_raises_error(self, mock_openai_client):
        """Test that empty response raises TextGenerationError."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        options = GenerationOptions()

        # Mock empty choices
        mock_client = mock_openai_client.OpenAI.return_value
        mock_client.chat.completions.create.return_value.choices = []

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_openai("Test prompt", config, options)

        assert "empty response" in str(exc_info.value).lower()

    def test_empty_message_content_raises_error(self, mock_openai_client):
        """Test that empty message content raises TextGenerationError."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        options = GenerationOptions()

        # Mock empty message content
        mock_client = mock_openai_client.OpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_openai("Test prompt", config, options)

        assert "empty" in str(exc_info.value).lower()

    def test_authentication_error(self, mock_openai_client):
        """Test handling of authentication errors."""
        config = OpenAIConfig(api_key="invalid-key", model="gpt-4")
        options = GenerationOptions()

        mock_client = mock_openai_client.OpenAI.return_value
        mock_openai_client.AuthenticationError = type(
            "AuthenticationError", (Exception,), {}
        )
        mock_client.chat.completions.create.side_effect = (
            mock_openai_client.AuthenticationError("Invalid API key")
        )

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_openai("Test prompt", config, options)

        assert "authentication" in str(exc_info.value).lower()

    def test_rate_limit_error(self, mock_openai_client):
        """Test handling of rate limit errors from OpenAI."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        options = GenerationOptions()

        mock_client = mock_openai_client.OpenAI.return_value
        mock_openai_client.RateLimitError = type("RateLimitError", (Exception,), {})
        mock_client.chat.completions.create.side_effect = (
            mock_openai_client.RateLimitError("Rate limit exceeded")
        )

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_openai("Test prompt", config, options)

        assert "rate limit" in str(exc_info.value).lower()

    def test_connection_error(self, mock_openai_client):
        """Test handling of connection errors."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        options = GenerationOptions()

        mock_client = mock_openai_client.OpenAI.return_value
        mock_openai_client.APIConnectionError = type(
            "APIConnectionError", (Exception,), {}
        )
        mock_client.chat.completions.create.side_effect = (
            mock_openai_client.APIConnectionError("Connection failed")
        )

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_openai("Test prompt", config, options)

        assert "connection" in str(exc_info.value).lower()

    def test_generation_options_passed_correctly(self, mock_openai_client):
        """Test that generation options are passed to the API."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        options = GenerationOptions(
            temperature=0.5,
            max_tokens=500,
            top_p=0.8,
            frequency_penalty=0.2,
            presence_penalty=0.3,
        )

        generate_with_openai("Test prompt", config, options)

        mock_client = mock_openai_client.OpenAI.return_value
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["top_p"] == 0.8
        assert call_kwargs["frequency_penalty"] == 0.2
        assert call_kwargs["presence_penalty"] == 0.3


# =============================================================================
# Tests for generate_with_anthropic
# =============================================================================


class TestGenerateWithAnthropic:
    """Tests for Anthropic text generation."""

    def test_successful_generation(self, mock_anthropic_client):
        """Test successful text generation with Anthropic."""
        config = AnthropicConfig(api_key="test-key", model="claude-3-opus-20240229")
        options = GenerationOptions()

        result = generate_with_anthropic("Test prompt", config, options)

        assert result == "Generated Anthropic content"

    def test_empty_response_raises_error(self, mock_anthropic_client):
        """Test that empty response raises TextGenerationError."""
        config = AnthropicConfig(api_key="test-key", model="claude-3-opus-20240229")
        options = GenerationOptions()

        mock_client = mock_anthropic_client.Anthropic.return_value
        mock_client.messages.create.return_value.content = []

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_anthropic("Test prompt", config, options)

        assert "empty" in str(exc_info.value).lower()

    def test_authentication_error(self, mock_anthropic_client):
        """Test handling of authentication errors."""
        config = AnthropicConfig(api_key="invalid-key", model="claude-3-opus-20240229")
        options = GenerationOptions()

        mock_client = mock_anthropic_client.Anthropic.return_value
        mock_anthropic_client.AuthenticationError = type(
            "AuthenticationError", (Exception,), {}
        )
        mock_client.messages.create.side_effect = (
            mock_anthropic_client.AuthenticationError("Invalid API key")
        )

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_anthropic("Test prompt", config, options)

        assert "authentication" in str(exc_info.value).lower()


# =============================================================================
# Tests for generate_with_gemini
# =============================================================================


class TestGenerateWithGemini:
    """Tests for Gemini text generation."""

    def test_successful_generation(self, mock_gemini_client):
        """Test successful text generation with Gemini."""
        config = GeminiConfig(api_key="test-key", model="gemini-1.5-flash")
        options = GenerationOptions()

        result = generate_with_gemini("Test prompt", config, options)

        assert result == "Generated Gemini content"
        mock_gemini_client.configure.assert_called_once_with(api_key="test-key")

    def test_empty_response_raises_error(self, mock_gemini_client):
        """Test that empty response raises TextGenerationError."""
        config = GeminiConfig(api_key="test-key", model="gemini-1.5-flash")
        options = GenerationOptions()

        mock_model = mock_gemini_client.GenerativeModel.return_value
        mock_model.generate_content.return_value.text = None

        with pytest.raises(TextGenerationError) as exc_info:
            generate_with_gemini("Test prompt", config, options)

        assert "empty" in str(exc_info.value).lower()

    def test_generation_config_passed_correctly(self, mock_gemini_client):
        """Test that generation config is passed to Gemini."""
        config = GeminiConfig(api_key="test-key", model="gemini-1.5-flash")
        options = GenerationOptions(temperature=0.5, max_tokens=500, top_p=0.8)

        generate_with_gemini("Test prompt", config, options)

        call_kwargs = mock_gemini_client.GenerativeModel.call_args.kwargs
        assert call_kwargs["generation_config"]["temperature"] == 0.5
        assert call_kwargs["generation_config"]["max_output_tokens"] == 500
        assert call_kwargs["generation_config"]["top_p"] == 0.8


# =============================================================================
# Tests for generate_text (main entry point)
# =============================================================================


class TestGenerateText:
    """Tests for the main generate_text function."""

    def test_routes_to_openai(
        self, openai_provider, mock_openai_client, disable_rate_limit
    ):
        """Test that OpenAI provider routes correctly."""
        result = generate_text(
            "Test prompt", openai_provider, check_rate_limit=False
        )
        assert result == "Generated OpenAI content"

    def test_routes_to_anthropic(
        self, anthropic_provider, mock_anthropic_client, disable_rate_limit
    ):
        """Test that Anthropic provider routes correctly."""
        result = generate_text(
            "Test prompt", anthropic_provider, check_rate_limit=False
        )
        assert result == "Generated Anthropic content"

    def test_routes_to_gemini(
        self, gemini_provider, mock_gemini_client, disable_rate_limit
    ):
        """Test that Gemini provider routes correctly."""
        result = generate_text(
            "Test prompt", gemini_provider, check_rate_limit=False
        )
        assert result == "Generated Gemini content"

    def test_unsupported_provider_raises_error(self, disable_rate_limit):
        """Test that unsupported provider raises TextGenerationError."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        invalid_provider = LLMProvider(type="invalid", config=config)

        with pytest.raises(TextGenerationError) as exc_info:
            generate_text("Test prompt", invalid_provider, check_rate_limit=False)

        assert "unsupported" in str(exc_info.value).lower()

    def test_default_options_used_when_none_provided(
        self, openai_provider, mock_openai_client, disable_rate_limit
    ):
        """Test that default options are used when none provided."""
        generate_text("Test prompt", openai_provider, options=None, check_rate_limit=False)

        mock_client = mock_openai_client.OpenAI.return_value
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        # Should use default GenerationOptions values
        assert "temperature" in call_kwargs
        assert "max_tokens" in call_kwargs


# =============================================================================
# Tests for generate_text_async
# =============================================================================


class TestGenerateTextAsync:
    """Tests for async text generation."""

    @pytest.mark.asyncio
    async def test_successful_async_generation(
        self, openai_provider, mock_openai_client
    ):
        """Test successful async text generation."""
        with patch("src.text_generation.core.get_rate_limiter") as mock_limiter:
            mock_limiter.return_value.acquire = MagicMock(return_value=asyncio.sleep(0))

            result = await generate_text_async(
                "Test prompt", openai_provider, check_rate_limit=False
            )

            assert result == "Generated OpenAI content"

    @pytest.mark.asyncio
    async def test_rate_limit_wait(self, openai_provider, mock_openai_client):
        """Test that async generation waits for rate limit."""
        with patch("src.text_generation.core.get_rate_limiter") as mock_limiter:
            mock_rl = MagicMock()
            mock_rl.acquire = MagicMock(return_value=asyncio.sleep(0))
            mock_limiter.return_value = mock_rl

            await generate_text_async(
                "Test prompt",
                openai_provider,
                check_rate_limit=True,
                wait_for_rate_limit=True,
            )

            mock_rl.acquire.assert_called_once()


# =============================================================================
# Tests for create_provider_from_env
# =============================================================================


class TestCreateProviderFromEnv:
    """Tests for provider creation from environment variables."""

    def test_create_openai_provider(self):
        """Test creating OpenAI provider from environment."""
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-openai-key", "OPENAI_MODEL": "gpt-4-turbo"},
        ):
            provider = create_provider_from_env("openai")

            assert provider.type == "openai"
            assert provider.config.api_key == "test-openai-key"
            assert provider.config.model == "gpt-4-turbo"

    def test_create_openai_provider_default_model(self):
        """Test creating OpenAI provider with default model."""
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False
        ):
            # Remove OPENAI_MODEL if it exists
            os.environ.pop("OPENAI_MODEL", None)
            provider = create_provider_from_env("openai")

            assert provider.config.model == "gpt-4"

    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider from environment."""
        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "ANTHROPIC_MODEL": "claude-3-sonnet-20240229",
            },
        ):
            provider = create_provider_from_env("anthropic")

            assert provider.type == "anthropic"
            assert provider.config.api_key == "test-anthropic-key"
            assert provider.config.model == "claude-3-sonnet-20240229"

    def test_create_gemini_provider(self):
        """Test creating Gemini provider from environment."""
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-gemini-key", "GEMINI_MODEL": "gemini-pro"},
        ):
            provider = create_provider_from_env("gemini")

            assert provider.type == "gemini"
            assert provider.config.api_key == "test-gemini-key"
            assert provider.config.model == "gemini-pro"

    def test_missing_openai_api_key_raises_error(self):
        """Test that missing OpenAI API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)

            with pytest.raises(TextGenerationError) as exc_info:
                create_provider_from_env("openai")

            assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_missing_anthropic_api_key_raises_error(self):
        """Test that missing Anthropic API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)

            with pytest.raises(TextGenerationError) as exc_info:
                create_provider_from_env("anthropic")

            assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_missing_gemini_api_key_raises_error(self):
        """Test that missing Gemini API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)

            with pytest.raises(TextGenerationError) as exc_info:
                create_provider_from_env("gemini")

            assert "GEMINI_API_KEY" in str(exc_info.value)

    def test_unsupported_provider_type_raises_error(self):
        """Test that unsupported provider type raises error."""
        with pytest.raises(TextGenerationError) as exc_info:
            create_provider_from_env("invalid_provider")

        assert "unsupported" in str(exc_info.value).lower()


# =============================================================================
# Tests for RateLimitError
# =============================================================================


class TestRateLimitError:
    """Tests for the RateLimitError exception."""

    def test_rate_limit_error_attributes(self):
        """Test RateLimitError stores attributes correctly."""
        error = RateLimitError(
            "Rate limit exceeded",
            operation_type=OperationType.GENERATION,
            wait_time=5.0,
        )

        assert str(error) == "Rate limit exceeded"
        assert error.operation_type == OperationType.GENERATION
        assert error.wait_time == 5.0

    def test_rate_limit_error_optional_attributes(self):
        """Test RateLimitError with optional attributes."""
        error = RateLimitError("Rate limit exceeded")

        assert error.operation_type is None
        assert error.wait_time is None


# =============================================================================
# Tests for TextGenerationError
# =============================================================================


class TestTextGenerationError:
    """Tests for the TextGenerationError exception."""

    def test_text_generation_error_message(self):
        """Test TextGenerationError stores message correctly."""
        error = TextGenerationError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_text_generation_error_inheritance(self):
        """Test TextGenerationError is an Exception."""
        error = TextGenerationError("Test error")
        assert isinstance(error, Exception)
