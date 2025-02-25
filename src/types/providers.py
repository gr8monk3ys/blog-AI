"""
Type definitions for LLM providers.
"""
from typing import Dict, Any, Literal, Optional, Union


class ProviderConfig:
    """Base configuration for LLM providers."""
    api_key: str
    
    def __init__(self, api_key: str):
        self.api_key = api_key


class OpenAIConfig(ProviderConfig):
    """Configuration for OpenAI provider."""
    model: str
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key)
        self.model = model


class AnthropicConfig(ProviderConfig):
    """Configuration for Anthropic provider."""
    model: str
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key)
        self.model = model


class GeminiConfig(ProviderConfig):
    """Configuration for Google's Gemini provider."""
    model: str
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash-latest"):
        super().__init__(api_key)
        self.model = model


ProviderType = Literal["openai", "anthropic", "gemini"]


class LLMProvider:
    """LLM provider configuration."""
    type: ProviderType
    config: Union[OpenAIConfig, AnthropicConfig, GeminiConfig]
    
    def __init__(self, type: ProviderType, config: Union[OpenAIConfig, AnthropicConfig, GeminiConfig]):
        self.type = type
        self.config = config


class GenerationOptions:
    """Options for text generation."""
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    
    def __init__(
        self,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
