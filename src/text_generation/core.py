"""
Core text generation functionality.
"""
import os
from typing import Dict, Any, Optional

from ..types.providers import (
    LLMProvider,
    GenerationOptions,
    ProviderType,
    OpenAIConfig,
    AnthropicConfig,
    GeminiConfig
)


class TextGenerationError(Exception):
    """Exception raised for errors in the text generation process."""
    pass


def generate_text(
    prompt: str,
    provider: LLMProvider,
    options: Optional[GenerationOptions] = None
) -> str:
    """
    Generate text using the specified LLM provider.
    
    Args:
        prompt: The prompt to generate text from.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated text.
        
    Raises:
        TextGenerationError: If an error occurs during text generation.
    """
    options = options or GenerationOptions()
    
    try:
        if provider.type == "openai":
            return generate_with_openai(prompt, provider.config, options)
        elif provider.type == "anthropic":
            return generate_with_anthropic(prompt, provider.config, options)
        elif provider.type == "gemini":
            return generate_with_gemini(prompt, provider.config, options)
        else:
            raise TextGenerationError(f"Unsupported provider: {provider.type}")
    except Exception as e:
        raise TextGenerationError(f"Error generating text: {str(e)}")


def generate_with_openai(
    prompt: str,
    config: OpenAIConfig,
    options: GenerationOptions
) -> str:
    """
    Generate text using OpenAI.
    
    Args:
        prompt: The prompt to generate text from.
        config: The OpenAI configuration.
        options: Options for text generation.
        
    Returns:
        The generated text.
        
    Raises:
        TextGenerationError: If an error occurs during text generation.
    """
    try:
        import openai
        
        openai.api_key = config.api_key
        
        response = openai.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            top_p=options.top_p,
            frequency_penalty=options.frequency_penalty,
            presence_penalty=options.presence_penalty
        )
        
        return response.choices[0].message.content
    except ImportError:
        raise TextGenerationError("OpenAI package not installed. Install it with 'pip install openai'.")
    except Exception as e:
        raise TextGenerationError(f"Error generating text with OpenAI: {str(e)}")


def generate_with_anthropic(
    prompt: str,
    config: AnthropicConfig,
    options: GenerationOptions
) -> str:
    """
    Generate text using Anthropic.
    
    Args:
        prompt: The prompt to generate text from.
        config: The Anthropic configuration.
        options: Options for text generation.
        
    Returns:
        The generated text.
        
    Raises:
        TextGenerationError: If an error occurs during text generation.
    """
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=config.api_key)
        
        response = client.messages.create(
            model=config.model,
            max_tokens=options.max_tokens,
            temperature=options.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    except ImportError:
        raise TextGenerationError("Anthropic package not installed. Install it with 'pip install anthropic'.")
    except Exception as e:
        raise TextGenerationError(f"Error generating text with Anthropic: {str(e)}")


def generate_with_gemini(
    prompt: str,
    config: GeminiConfig,
    options: GenerationOptions
) -> str:
    """
    Generate text using Google's Gemini.
    
    Args:
        prompt: The prompt to generate text from.
        config: The Gemini configuration.
        options: Options for text generation.
        
    Returns:
        The generated text.
        
    Raises:
        TextGenerationError: If an error occurs during text generation.
    """
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=config.api_key)
        
        generation_config = {
            "temperature": options.temperature,
            "top_p": options.top_p,
            "max_output_tokens": options.max_tokens,
        }
        
        model = genai.GenerativeModel(
            config.model,
            generation_config=generation_config
        )
        
        response = model.generate_content(prompt)
        
        return response.text
    except ImportError:
        raise TextGenerationError("Google Generative AI package not installed. Install it with 'pip install google-generativeai'.")
    except Exception as e:
        raise TextGenerationError(f"Error generating text with Gemini: {str(e)}")


def create_provider_from_env(provider_type: ProviderType) -> LLMProvider:
    """
    Create a provider from environment variables.
    
    Args:
        provider_type: The type of provider to create.
        
    Returns:
        The created provider.
        
    Raises:
        TextGenerationError: If an error occurs during provider creation.
    """
    try:
        if provider_type == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise TextGenerationError("OPENAI_API_KEY environment variable not set")
            
            model = os.environ.get("OPENAI_MODEL", "gpt-4")
            
            config = OpenAIConfig(api_key=api_key, model=model)
            
            return LLMProvider(type=provider_type, config=config)
        elif provider_type == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise TextGenerationError("ANTHROPIC_API_KEY environment variable not set")
            
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")
            
            config = AnthropicConfig(api_key=api_key, model=model)
            
            return LLMProvider(type=provider_type, config=config)
        elif provider_type == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise TextGenerationError("GEMINI_API_KEY environment variable not set")
            
            model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-latest")
            
            config = GeminiConfig(api_key=api_key, model=model)
            
            return LLMProvider(type=provider_type, config=config)
        else:
            raise TextGenerationError(f"Unsupported provider type: {provider_type}")
    except Exception as e:
        raise TextGenerationError(f"Error creating provider: {str(e)}")
