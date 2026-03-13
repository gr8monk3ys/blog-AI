"""
Unit tests for streaming text generation functionality.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.text_generation.streaming import (
    StreamEvent,
    StreamEventType,
    StreamingError,
    collect_stream,
    stream_text,
)
from src.types.providers import (
    GenerationOptions,
    LLMProvider,
    OpenAIConfig,
    AnthropicConfig,
    GeminiConfig,
)


class TestStreamEvent(unittest.TestCase):
    """Tests for StreamEvent dataclass."""

    def test_token_event(self):
        """Test creating a token event."""
        event = StreamEvent(type=StreamEventType.TOKEN, content="Hello")
        self.assertEqual(event.type, StreamEventType.TOKEN)
        self.assertEqual(event.content, "Hello")
        self.assertIsNone(event.error)

    def test_error_event(self):
        """Test creating an error event."""
        event = StreamEvent(
            type=StreamEventType.ERROR,
            error="Connection failed",
        )
        self.assertEqual(event.type, StreamEventType.ERROR)
        self.assertEqual(event.error, "Connection failed")

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = StreamEvent(
            type=StreamEventType.TOKEN,
            content="test",
            metadata={"key": "value"},
        )
        result = event.to_dict()
        self.assertEqual(result["type"], "token")
        self.assertEqual(result["content"], "test")
        self.assertEqual(result["metadata"], {"key": "value"})

    def test_end_event_with_metadata(self):
        """Test end event with metadata."""
        event = StreamEvent(
            type=StreamEventType.END,
            metadata={"finish_reason": "stop", "tokens": 100},
        )
        result = event.to_dict()
        self.assertEqual(result["type"], "end")
        self.assertEqual(result["metadata"]["finish_reason"], "stop")


class TestStreamingError(unittest.TestCase):
    """Tests for StreamingError exception."""

    def test_basic_error(self):
        """Test basic streaming error."""
        error = StreamingError("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.partial_content, "")
        self.assertFalse(error.is_recoverable)

    def test_error_with_partial_content(self):
        """Test streaming error with partial content."""
        error = StreamingError(
            "Connection lost",
            partial_content="Hello world",
            is_recoverable=True,
        )
        self.assertEqual(error.partial_content, "Hello world")
        self.assertTrue(error.is_recoverable)


class TestStreamText(unittest.IsolatedAsyncioTestCase):
    """Tests for the stream_text function."""

    async def test_stream_text_yields_start_event(self):
        """Test that stream_text yields a start event first."""
        mock_config = OpenAIConfig(api_key="test-key", model="gpt-4")
        provider = LLMProvider(type="openai", config=mock_config)

        with patch(
            "src.text_generation.streaming._stream_openai"
        ) as mock_stream:
            # Mock the async generator
            async def mock_gen():
                yield StreamEvent(type=StreamEventType.TOKEN, content="test")
                yield StreamEvent(type=StreamEventType.END)

            mock_stream.return_value = mock_gen()

            events = []
            async for event in stream_text(
                "test prompt",
                provider,
                check_rate_limit=False,
            ):
                events.append(event)

            # First event should be START
            self.assertEqual(events[0].type, StreamEventType.START)
            self.assertEqual(events[0].metadata["provider"], "openai")

    async def test_stream_text_unsupported_provider(self):
        """Test that stream_text handles unsupported providers."""
        mock_config = MagicMock()
        mock_config.model = "test-model"
        provider = LLMProvider(type="unsupported", config=mock_config)

        events = []
        async for event in stream_text(
            "test prompt",
            provider,
            check_rate_limit=False,
        ):
            events.append(event)

        # Should have start and error events
        self.assertEqual(events[0].type, StreamEventType.START)
        self.assertEqual(events[1].type, StreamEventType.ERROR)
        self.assertIn("Unsupported provider", events[1].error)


class TestCollectStream(unittest.IsolatedAsyncioTestCase):
    """Tests for the collect_stream function."""

    async def test_collect_stream_accumulates_tokens(self):
        """Test that collect_stream accumulates all tokens."""
        mock_config = OpenAIConfig(api_key="test-key", model="gpt-4")
        provider = LLMProvider(type="openai", config=mock_config)

        with patch("src.text_generation.streaming.stream_text") as mock_stream:
            # Mock the async generator
            async def mock_gen(*args, **kwargs):
                yield StreamEvent(type=StreamEventType.START)
                yield StreamEvent(type=StreamEventType.TOKEN, content="Hello")
                yield StreamEvent(type=StreamEventType.TOKEN, content=" ")
                yield StreamEvent(type=StreamEventType.TOKEN, content="World")
                yield StreamEvent(
                    type=StreamEventType.END,
                    metadata={"finish_reason": "stop"},
                )

            mock_stream.return_value = mock_gen()

            content, metadata = await collect_stream("test", provider)

            self.assertEqual(content, "Hello World")
            self.assertEqual(metadata["finish_reason"], "stop")

    async def test_collect_stream_raises_on_error(self):
        """Test that collect_stream raises on error event."""
        mock_config = OpenAIConfig(api_key="test-key", model="gpt-4")
        provider = LLMProvider(type="openai", config=mock_config)

        with patch("src.text_generation.streaming.stream_text") as mock_stream:
            # Mock the async generator with an error
            async def mock_gen(*args, **kwargs):
                yield StreamEvent(type=StreamEventType.START)
                yield StreamEvent(type=StreamEventType.TOKEN, content="Hello")
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    error="Connection lost",
                )

            mock_stream.return_value = mock_gen()

            with self.assertRaises(StreamingError) as ctx:
                await collect_stream("test", provider)

            self.assertEqual(ctx.exception.partial_content, "Hello")


class TestOpenAIStreaming(unittest.IsolatedAsyncioTestCase):
    """Tests for OpenAI streaming integration."""

    async def test_openai_streaming_mock(self):
        """Test OpenAI streaming with mocked client."""
        from src.text_generation.streaming import _stream_openai

        mock_config = OpenAIConfig(api_key="test-key", model="gpt-4")
        options = GenerationOptions()

        # Create mock stream chunks
        mock_chunks = [
            MagicMock(
                choices=[
                    MagicMock(delta=MagicMock(content="Hello"), finish_reason=None)
                ]
            ),
            MagicMock(
                choices=[
                    MagicMock(delta=MagicMock(content=" World"), finish_reason=None)
                ]
            ),
            MagicMock(
                choices=[
                    MagicMock(delta=MagicMock(content=""), finish_reason="stop")
                ]
            ),
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream()
            )

            events = []
            async for event in _stream_openai("test", mock_config, options):
                events.append(event)

            # Should have tokens and end event
            token_events = [e for e in events if e.type == StreamEventType.TOKEN]
            end_events = [e for e in events if e.type == StreamEventType.END]

            self.assertEqual(len(token_events), 2)
            self.assertEqual(token_events[0].content, "Hello")
            self.assertEqual(token_events[1].content, " World")
            self.assertEqual(len(end_events), 1)


class TestAnthropicStreaming(unittest.TestCase):
    """Tests for Anthropic streaming integration."""

    def test_anthropic_error_categorization(self):
        """Test that Anthropic errors are properly categorized."""
        from src.text_generation.streaming import _categorize_anthropic_error

        # Test with a generic exception
        generic_error = Exception("Something went wrong")
        result = _categorize_anthropic_error(generic_error)
        self.assertIn("Anthropic error", result)

    def test_anthropic_config_initialization(self):
        """Test that Anthropic config is properly initialized."""
        config = AnthropicConfig(api_key="test-key", model="claude-3-opus")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "claude-3-opus")


class TestStreamEventType(unittest.TestCase):
    """Tests for StreamEventType enum."""

    def test_event_type_values(self):
        """Test that event types have expected string values."""
        self.assertEqual(StreamEventType.TOKEN.value, "token")
        self.assertEqual(StreamEventType.START.value, "start")
        self.assertEqual(StreamEventType.END.value, "end")
        self.assertEqual(StreamEventType.ERROR.value, "error")
        self.assertEqual(StreamEventType.METADATA.value, "metadata")


if __name__ == "__main__":
    unittest.main()
