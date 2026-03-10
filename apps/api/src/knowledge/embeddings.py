"""
Embedding generation for the Knowledge Base system.

This module handles generating vector embeddings for document chunks using
various providers (OpenAI, Voyage AI, Cohere).

Features:
- Multiple embedding provider support
- Batched embedding generation for cost efficiency
- Automatic retry with exponential backoff
- Dimension validation and normalization
"""

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ..types.knowledge import (
    DocumentChunk,
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingResult,
    EmbeddingVector,
)

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Exception raised when embedding generation fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        retryable: bool = False,
    ):
        self.provider = provider
        self.retryable = retryable
        super().__init__(message)


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    def __init__(self, config: EmbeddingConfig):
        self.config = config

    @abstractmethod
    async def generate_embeddings(
        self, texts: List[str]
    ) -> List[Tuple[EmbeddingVector, int]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of tuples containing (embedding vector, tokens used)
        """
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions for this provider."""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider using text-embedding-3 models."""

    # Model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, config: EmbeddingConfig, api_key: Optional[str] = None):
        super().__init__(config)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise EmbeddingError(
                "OpenAI API key not provided and OPENAI_API_KEY not set",
                provider="openai",
            )

        # Validate model
        if config.model not in self.MODEL_DIMENSIONS:
            logger.warning(
                f"Unknown OpenAI embedding model: {config.model}. "
                f"Using configured dimensions: {config.dimensions}"
            )

    @property
    def dimensions(self) -> int:
        return self.MODEL_DIMENSIONS.get(self.config.model, self.config.dimensions)

    async def generate_embeddings(
        self, texts: List[str]
    ) -> List[Tuple[EmbeddingVector, int]]:
        """Generate embeddings using OpenAI API."""
        try:
            import openai
        except ImportError:
            raise EmbeddingError(
                "openai package not installed. Install with: pip install openai",
                provider="openai",
            )

        client = openai.AsyncOpenAI(api_key=self.api_key)

        try:
            response = await client.embeddings.create(
                model=self.config.model,
                input=texts,
                encoding_format="float",
            )

            results = []
            for i, embedding_obj in enumerate(response.data):
                embedding = embedding_obj.embedding
                # Estimate tokens (OpenAI provides usage but not per-text)
                tokens = len(texts[i]) // 4
                results.append((embedding, tokens))

            logger.debug(
                f"Generated {len(results)} OpenAI embeddings, "
                f"total tokens: {response.usage.total_tokens}"
            )

            return results

        except openai.RateLimitError as e:
            raise EmbeddingError(
                f"OpenAI rate limit exceeded: {e}",
                provider="openai",
                retryable=True,
            )
        except openai.APIError as e:
            raise EmbeddingError(
                f"OpenAI API error: {e}",
                provider="openai",
                retryable=True,
            )
        except Exception as e:
            raise EmbeddingError(
                f"Failed to generate OpenAI embeddings: {e}",
                provider="openai",
            )


class VoyageEmbeddingProvider(BaseEmbeddingProvider):
    """Voyage AI embedding provider for cost-effective embeddings."""

    # Model dimensions
    MODEL_DIMENSIONS = {
        "voyage-large-2": 1536,
        "voyage-code-2": 1536,
        "voyage-2": 1024,
        "voyage-lite-02-instruct": 1024,
    }

    def __init__(self, config: EmbeddingConfig, api_key: Optional[str] = None):
        super().__init__(config)
        self.api_key = api_key or os.environ.get("VOYAGE_API_KEY")
        if not self.api_key:
            raise EmbeddingError(
                "Voyage API key not provided and VOYAGE_API_KEY not set",
                provider="voyage",
            )

    @property
    def dimensions(self) -> int:
        return self.MODEL_DIMENSIONS.get(self.config.model, self.config.dimensions)

    async def generate_embeddings(
        self, texts: List[str]
    ) -> List[Tuple[EmbeddingVector, int]]:
        """Generate embeddings using Voyage AI API."""
        try:
            import voyageai
        except ImportError:
            raise EmbeddingError(
                "voyageai package not installed. Install with: pip install voyageai",
                provider="voyage",
            )

        try:
            client = voyageai.AsyncClient(api_key=self.api_key)

            response = await client.embed(
                texts=texts,
                model=self.config.model,
                input_type="document",
            )

            results = []
            for i, embedding in enumerate(response.embeddings):
                tokens = len(texts[i]) // 4  # Estimate
                results.append((embedding, tokens))

            logger.debug(
                f"Generated {len(results)} Voyage embeddings, "
                f"total tokens: {response.total_tokens}"
            )

            return results

        except Exception as e:
            raise EmbeddingError(
                f"Failed to generate Voyage embeddings: {e}",
                provider="voyage",
            )


class CohereEmbeddingProvider(BaseEmbeddingProvider):
    """Cohere embedding provider."""

    MODEL_DIMENSIONS = {
        "embed-english-v3.0": 1024,
        "embed-multilingual-v3.0": 1024,
        "embed-english-light-v3.0": 384,
        "embed-multilingual-light-v3.0": 384,
    }

    def __init__(self, config: EmbeddingConfig, api_key: Optional[str] = None):
        super().__init__(config)
        self.api_key = api_key or os.environ.get("COHERE_API_KEY")
        if not self.api_key:
            raise EmbeddingError(
                "Cohere API key not provided and COHERE_API_KEY not set",
                provider="cohere",
            )

    @property
    def dimensions(self) -> int:
        return self.MODEL_DIMENSIONS.get(self.config.model, self.config.dimensions)

    async def generate_embeddings(
        self, texts: List[str]
    ) -> List[Tuple[EmbeddingVector, int]]:
        """Generate embeddings using Cohere API."""
        try:
            import cohere
        except ImportError:
            raise EmbeddingError(
                "cohere package not installed. Install with: pip install cohere",
                provider="cohere",
            )

        try:
            client = cohere.AsyncClient(api_key=self.api_key)

            response = await client.embed(
                texts=texts,
                model=self.config.model,
                input_type="search_document",
            )

            results = []
            for i, embedding in enumerate(response.embeddings):
                tokens = len(texts[i]) // 4  # Estimate
                results.append((list(embedding), tokens))

            logger.debug(f"Generated {len(results)} Cohere embeddings")

            return results

        except Exception as e:
            raise EmbeddingError(
                f"Failed to generate Cohere embeddings: {e}",
                provider="cohere",
            )


class EmbeddingGenerator:
    """
    High-level interface for generating embeddings.

    Handles batching, retries, and provider selection.
    """

    # Default models per provider
    DEFAULT_MODELS = {
        EmbeddingProvider.OPENAI: "text-embedding-3-small",
        EmbeddingProvider.VOYAGE: "voyage-large-2",
        EmbeddingProvider.COHERE: "embed-english-v3.0",
    }

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the embedding generator.

        Args:
            config: Embedding configuration. If None, uses OpenAI defaults.
            api_key: API key for the provider. If None, uses environment variable.
        """
        self.config = config or EmbeddingConfig()
        self.api_key = api_key
        self._provider: Optional[BaseEmbeddingProvider] = None

    @classmethod
    def from_env(cls, provider: Optional[EmbeddingProvider] = None) -> "EmbeddingGenerator":
        """
        Create an EmbeddingGenerator from environment variables.

        Args:
            provider: Override the provider. If None, detects from available API keys.

        Returns:
            Configured EmbeddingGenerator
        """
        # Auto-detect provider from available API keys
        if provider is None:
            if os.environ.get("OPENAI_API_KEY"):
                provider = EmbeddingProvider.OPENAI
            elif os.environ.get("VOYAGE_API_KEY"):
                provider = EmbeddingProvider.VOYAGE
            elif os.environ.get("COHERE_API_KEY"):
                provider = EmbeddingProvider.COHERE
            else:
                raise EmbeddingError(
                    "No embedding API key found. Set OPENAI_API_KEY, VOYAGE_API_KEY, or COHERE_API_KEY"
                )

        model = cls.DEFAULT_MODELS.get(provider, "text-embedding-3-small")
        config = EmbeddingConfig(provider=provider, model=model)

        return cls(config=config)

    def _get_provider(self) -> BaseEmbeddingProvider:
        """Get or create the embedding provider."""
        if self._provider is None:
            provider_map = {
                EmbeddingProvider.OPENAI: OpenAIEmbeddingProvider,
                EmbeddingProvider.VOYAGE: VoyageEmbeddingProvider,
                EmbeddingProvider.COHERE: CohereEmbeddingProvider,
            }

            provider_class = provider_map.get(self.config.provider)
            if not provider_class:
                raise EmbeddingError(f"Unsupported provider: {self.config.provider}")

            self._provider = provider_class(self.config, self.api_key)

        return self._provider

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions for the current configuration."""
        return self._get_provider().dimensions

    async def generate_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with the embedding vector
        """
        results = await self.generate_embeddings([text])
        return results[0]

    async def generate_embeddings(
        self,
        texts: List[str],
        show_progress: bool = False,
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts with batching.

        Args:
            texts: List of texts to embed
            show_progress: Whether to log progress

        Returns:
            List of EmbeddingResult objects
        """
        if not texts:
            return []

        provider = self._get_provider()
        batch_size = self.config.batch_size
        results = []
        total_tokens = 0

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size

            if show_progress:
                logger.info(f"Processing embedding batch {batch_num}/{total_batches}")

            # Retry logic
            for attempt in range(self.config.max_retries):
                try:
                    batch_results = await provider.generate_embeddings(batch)

                    for j, (embedding, tokens) in enumerate(batch_results):
                        result = EmbeddingResult(
                            chunk_id=f"text_{i + j}",  # Placeholder ID
                            embedding=embedding,
                            model=self.config.model,
                            dimensions=len(embedding),
                            tokens_used=tokens,
                        )
                        results.append(result)
                        total_tokens += tokens

                    break  # Success, exit retry loop

                except EmbeddingError as e:
                    if e.retryable and attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay * (2**attempt)
                        logger.warning(
                            f"Embedding attempt {attempt + 1} failed, "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise

        logger.info(
            f"Generated {len(results)} embeddings using {self.config.provider.value}, "
            f"total tokens: {total_tokens}"
        )

        return results

    async def embed_chunks(
        self,
        chunks: List[DocumentChunk],
        show_progress: bool = True,
    ) -> List[DocumentChunk]:
        """
        Generate embeddings for document chunks and attach them.

        Args:
            chunks: List of DocumentChunk objects
            show_progress: Whether to log progress

        Returns:
            List of DocumentChunk objects with embeddings attached
        """
        if not chunks:
            return []

        # Extract texts
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings
        results = await self.generate_embeddings(texts, show_progress=show_progress)

        # Attach embeddings to chunks
        for chunk, result in zip(chunks, results):
            chunk.embedding = result.embedding
            result.chunk_id = chunk.id

        return chunks

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Some providers have different behavior for queries vs documents.
        This method handles those differences.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        # For Voyage, we might want to use input_type="query"
        # For now, use standard embedding
        result = await self.generate_embedding(query)
        return result.embedding


def normalize_embedding(embedding: List[float]) -> List[float]:
    """
    Normalize an embedding vector to unit length.

    Args:
        embedding: Input embedding vector

    Returns:
        Normalized embedding vector
    """
    import math

    magnitude = math.sqrt(sum(x * x for x in embedding))
    if magnitude == 0:
        return embedding
    return [x / magnitude for x in embedding]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (-1 to 1)
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same dimensions")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)
