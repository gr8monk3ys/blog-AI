"""
Plagiarism detection module with multi-provider support.

This module provides plagiarism checking functionality with:
- Copyscape API integration (primary)
- Originality.ai API integration (alternative)
- Embedding-based similarity fallback (local)

Features:
- Result caching to minimize API costs
- Rate limiting awareness
- Graceful fallback between providers
- Cost optimization through smart provider selection
"""

import asyncio
import hashlib
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
import uuid

import httpx

from ..types.plagiarism import (
    MatchingSource,
    PlagiarismCheckRequest,
    PlagiarismCheckResult,
    PlagiarismCheckStatus,
    PlagiarismProvider,
    PlagiarismRiskLevel,
    ProviderQuota,
)

logger = logging.getLogger(__name__)


class PlagiarismCheckError(Exception):
    """Exception raised for plagiarism check errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[PlagiarismProvider] = None,
        is_retryable: bool = False,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.is_retryable = is_retryable
        self.original_error = original_error


class CacheEntry:
    """Cache entry for plagiarism check results."""

    def __init__(
        self,
        result: PlagiarismCheckResult,
        expires_at: datetime,
    ):
        self.result = result
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.utcnow() > self.expires_at


class InMemoryCache:
    """
    Simple in-memory cache for plagiarism results.

    In production, this should be replaced with Redis for
    distributed caching across multiple instances.
    """

    def __init__(self, default_ttl_hours: int = 24, max_entries: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = timedelta(hours=default_ttl_hours)
        self._max_entries = max_entries

    def _generate_key(self, content: str) -> str:
        """Generate cache key from content hash."""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return f"plagiarism:{content_hash[:32]}"

    def get(self, content: str) -> Optional[PlagiarismCheckResult]:
        """Get cached result if available and not expired."""
        key = self._generate_key(content)
        entry = self._cache.get(key)

        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        # Return a copy with cached flag set
        result = entry.result.model_copy()
        result.cached = True
        result.cache_key = key
        result.status = PlagiarismCheckStatus.CACHED
        return result

    def set(
        self,
        content: str,
        result: PlagiarismCheckResult,
        ttl: Optional[timedelta] = None,
    ) -> str:
        """Cache a result. Returns cache key."""
        # Evict oldest entries if at capacity
        if len(self._cache) >= self._max_entries:
            self._evict_oldest()

        key = self._generate_key(content)
        expires_at = datetime.utcnow() + (ttl or self._default_ttl)
        self._cache[key] = CacheEntry(result, expires_at)
        return key

    def _evict_oldest(self) -> None:
        """Evict oldest entries to make room."""
        # Sort by expiration and remove oldest 10%
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].expires_at
        )
        to_remove = max(1, len(sorted_entries) // 10)
        for key, _ in sorted_entries[:to_remove]:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()


# Global cache instance
_cache = InMemoryCache()


def get_cache() -> InMemoryCache:
    """Get the global cache instance."""
    return _cache


class BasePlagiarismChecker(ABC):
    """
    Abstract base class for plagiarism checkers.

    All plagiarism checking providers must implement this interface
    to ensure consistent behavior and easy provider switching.
    """

    def __init__(self):
        self._last_check_time: Optional[datetime] = None
        self._checks_today: int = 0
        self._daily_reset_time: Optional[datetime] = None

    @property
    @abstractmethod
    def provider(self) -> PlagiarismProvider:
        """Return the provider type."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        pass

    @abstractmethod
    async def check(
        self,
        request: PlagiarismCheckRequest,
    ) -> PlagiarismCheckResult:
        """
        Perform plagiarism check on the provided content.

        Args:
            request: The plagiarism check request.

        Returns:
            PlagiarismCheckResult with score and matching sources.

        Raises:
            PlagiarismCheckError: If check fails.
        """
        pass

    @abstractmethod
    async def get_quota(self) -> ProviderQuota:
        """Get current quota/credit information."""
        pass

    def _calculate_risk_level(self, score: float) -> PlagiarismRiskLevel:
        """Calculate risk level from plagiarism score."""
        if score <= 5:
            return PlagiarismRiskLevel.NONE
        elif score <= 15:
            return PlagiarismRiskLevel.LOW
        elif score <= 30:
            return PlagiarismRiskLevel.MODERATE
        elif score <= 50:
            return PlagiarismRiskLevel.HIGH
        else:
            return PlagiarismRiskLevel.CRITICAL

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())


class CopyscapeChecker(BasePlagiarismChecker):
    """
    Copyscape Premium API integration for plagiarism detection.

    Copyscape is a widely-used plagiarism detection service that checks
    content against billions of web pages.

    API Documentation: https://www.copyscape.com/apiconfigure.php

    Cost: ~$0.03 per search (100 words minimum), scales with content length
    """

    API_BASE_URL = "https://www.copyscape.com/api/"
    MIN_WORDS = 15  # Copyscape minimum
    WORDS_PER_CREDIT = 100  # Approximate words per credit unit

    def __init__(self):
        super().__init__()
        self._username = os.environ.get("COPYSCAPE_USERNAME", "")
        self._api_key = os.environ.get("COPYSCAPE_API_KEY", "")
        self._timeout = float(os.environ.get("PLAGIARISM_API_TIMEOUT", "30"))

    @property
    def provider(self) -> PlagiarismProvider:
        return PlagiarismProvider.COPYSCAPE

    @property
    def is_configured(self) -> bool:
        return bool(self._username and self._api_key)

    async def check(
        self,
        request: PlagiarismCheckRequest,
    ) -> PlagiarismCheckResult:
        """
        Check content using Copyscape Premium API.

        Uses the 'csearch' operation to search for matching content online.
        """
        if not self.is_configured:
            raise PlagiarismCheckError(
                "Copyscape is not configured. Set COPYSCAPE_USERNAME and COPYSCAPE_API_KEY.",
                provider=self.provider,
                is_retryable=False,
            )

        start_time = time.time()
        check_id = f"cs_{uuid.uuid4().hex[:12]}"
        word_count = self._count_words(request.content)

        if word_count < self.MIN_WORDS:
            raise PlagiarismCheckError(
                f"Content too short. Copyscape requires at least {self.MIN_WORDS} words.",
                provider=self.provider,
                is_retryable=False,
            )

        try:
            # Build API request parameters
            params = {
                "u": self._username,
                "o": self._api_key,
                "t": request.content,
                "f": "json",  # JSON response format
                "c": "1",     # Include comparison text
            }

            # Add URL exclusions if provided
            if request.exclude_urls:
                params["x"] = "\n".join(request.exclude_urls[:3])  # Max 3 URLs

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self.API_BASE_URL,
                    data=params,
                )
                response.raise_for_status()
                data = response.json()

            # Check for API errors
            if "error" in data:
                error_msg = data.get("error", "Unknown Copyscape error")
                raise PlagiarismCheckError(
                    f"Copyscape API error: {error_msg}",
                    provider=self.provider,
                    is_retryable="quota" not in error_msg.lower(),
                )

            # Parse results
            matching_sources = []
            total_matched_words = 0

            if "result" in data:
                for match in data["result"]:
                    similarity = float(match.get("percentmatched", 0))
                    matched_words = int(match.get("wordsmatched", 0))
                    total_matched_words += matched_words

                    source = MatchingSource(
                        url=match.get("url", ""),
                        title=match.get("title", ""),
                        similarity_percentage=similarity,
                        matched_words=matched_words,
                        matched_text=match.get("textsnippet", "")[:1000] if match.get("textsnippet") else None,
                        is_exact_match=similarity > 90,
                    )
                    matching_sources.append(source)

            # Calculate overall score
            # Weight by the highest matching source
            if matching_sources:
                overall_score = max(s.similarity_percentage for s in matching_sources)
            else:
                overall_score = 0.0

            processing_time = int((time.time() - start_time) * 1000)

            # Estimate credits used (approximately 1 credit per 100 words)
            credits_used = max(1, word_count / self.WORDS_PER_CREDIT)

            return PlagiarismCheckResult(
                check_id=check_id,
                status=PlagiarismCheckStatus.COMPLETED,
                provider=self.provider,
                overall_score=overall_score,
                risk_level=self._calculate_risk_level(overall_score),
                original_percentage=100 - overall_score,
                matching_sources=matching_sources[:10],  # Limit to top 10
                total_words_checked=word_count,
                total_matched_words=total_matched_words,
                api_credits_used=credits_used,
                processing_time_ms=processing_time,
                metadata={
                    "query_count": data.get("querywords", 0),
                    "results_count": len(matching_sources),
                },
            )

        except httpx.HTTPStatusError as e:
            raise PlagiarismCheckError(
                f"Copyscape API HTTP error: {e.response.status_code}",
                provider=self.provider,
                is_retryable=e.response.status_code >= 500,
                original_error=e,
            )
        except httpx.TimeoutException as e:
            raise PlagiarismCheckError(
                f"Copyscape API timeout after {self._timeout}s",
                provider=self.provider,
                is_retryable=True,
                original_error=e,
            )
        except Exception as e:
            if isinstance(e, PlagiarismCheckError):
                raise
            raise PlagiarismCheckError(
                f"Unexpected error checking with Copyscape: {str(e)}",
                provider=self.provider,
                is_retryable=False,
                original_error=e,
            )

    async def get_quota(self) -> ProviderQuota:
        """Get Copyscape account balance/credits."""
        if not self.is_configured:
            return ProviderQuota(
                provider=self.provider,
                is_available=False,
                remaining_credits=-1,
            )

        try:
            params = {
                "u": self._username,
                "o": self._api_key,
                "f": "json",
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.API_BASE_URL}?{urlencode(params)}&q=balance"
                )
                response.raise_for_status()
                data = response.json()

            credits = float(data.get("value", 0))

            return ProviderQuota(
                provider=self.provider,
                remaining_credits=credits,
                credits_per_check=0.03,  # Approximate cost per check
                is_available=credits > 0,
            )

        except Exception as e:
            logger.warning(f"Failed to get Copyscape quota: {e}")
            return ProviderQuota(
                provider=self.provider,
                remaining_credits=-1,
                is_available=True,  # Assume available if we can't check
            )


class OriginalityChecker(BasePlagiarismChecker):
    """
    Originality.ai API integration for plagiarism and AI detection.

    Originality.ai provides both plagiarism detection and AI content detection,
    making it useful for ensuring content quality.

    API Documentation: https://docs.originality.ai/

    Cost: Credits-based, typically $0.01 per 100 words
    """

    API_BASE_URL = "https://api.originality.ai/api/v1"
    MIN_WORDS = 50  # Minimum for accurate results

    def __init__(self):
        super().__init__()
        self._api_key = os.environ.get("ORIGINALITY_API_KEY", "")
        self._timeout = float(os.environ.get("PLAGIARISM_API_TIMEOUT", "60"))

    @property
    def provider(self) -> PlagiarismProvider:
        return PlagiarismProvider.ORIGINALITY

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def check(
        self,
        request: PlagiarismCheckRequest,
    ) -> PlagiarismCheckResult:
        """
        Check content using Originality.ai API.

        Performs plagiarism scan and optionally AI detection.
        """
        if not self.is_configured:
            raise PlagiarismCheckError(
                "Originality.ai is not configured. Set ORIGINALITY_API_KEY.",
                provider=self.provider,
                is_retryable=False,
            )

        start_time = time.time()
        check_id = f"orig_{uuid.uuid4().hex[:12]}"
        word_count = self._count_words(request.content)

        if word_count < self.MIN_WORDS:
            raise PlagiarismCheckError(
                f"Content too short. Originality.ai requires at least {self.MIN_WORDS} words for accurate results.",
                provider=self.provider,
                is_retryable=False,
            )

        try:
            headers = {
                "X-OAI-API-KEY": self._api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            payload = {
                "content": request.content,
                "title": request.title or "",
                "plagiarism": True,
                "aiDetection": False,  # Focus on plagiarism only
            }

            # Add exclusions if provided
            if request.exclude_urls:
                payload["excludeUrls"] = request.exclude_urls[:5]

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self.API_BASE_URL}/scan/plagiarism",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            # Check for API errors
            if not data.get("success", True):
                error_msg = data.get("error", data.get("message", "Unknown error"))
                raise PlagiarismCheckError(
                    f"Originality.ai API error: {error_msg}",
                    provider=self.provider,
                    is_retryable="rate" in str(error_msg).lower(),
                )

            # Parse plagiarism results
            plagiarism_data = data.get("plagiarism", {})
            overall_score = float(plagiarism_data.get("score", 0)) * 100  # Convert to percentage

            matching_sources = []
            total_matched_words = 0

            for match in plagiarism_data.get("sources", []):
                similarity = float(match.get("score", 0)) * 100
                matched_words = int(match.get("matchedWords", 0))
                total_matched_words += matched_words

                source = MatchingSource(
                    url=match.get("url", ""),
                    title=match.get("title", ""),
                    similarity_percentage=similarity,
                    matched_words=matched_words,
                    matched_text=match.get("matchedText", "")[:1000] if match.get("matchedText") else None,
                    is_exact_match=similarity > 90,
                )
                matching_sources.append(source)

            processing_time = int((time.time() - start_time) * 1000)

            # Credits calculation (approximately 1 credit per 100 words)
            credits_used = max(1, word_count / 100)

            return PlagiarismCheckResult(
                check_id=check_id,
                status=PlagiarismCheckStatus.COMPLETED,
                provider=self.provider,
                overall_score=overall_score,
                risk_level=self._calculate_risk_level(overall_score),
                original_percentage=100 - overall_score,
                matching_sources=matching_sources[:10],
                total_words_checked=word_count,
                total_matched_words=total_matched_words,
                api_credits_used=credits_used,
                processing_time_ms=processing_time,
                metadata={
                    "scan_id": data.get("id", ""),
                    "credits_remaining": data.get("credits", {}).get("remaining", -1),
                },
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                raise PlagiarismCheckError(
                    "Originality.ai: Insufficient credits",
                    provider=self.provider,
                    is_retryable=False,
                    original_error=e,
                )
            raise PlagiarismCheckError(
                f"Originality.ai API HTTP error: {e.response.status_code}",
                provider=self.provider,
                is_retryable=e.response.status_code >= 500,
                original_error=e,
            )
        except httpx.TimeoutException as e:
            raise PlagiarismCheckError(
                f"Originality.ai API timeout after {self._timeout}s",
                provider=self.provider,
                is_retryable=True,
                original_error=e,
            )
        except Exception as e:
            if isinstance(e, PlagiarismCheckError):
                raise
            raise PlagiarismCheckError(
                f"Unexpected error checking with Originality.ai: {str(e)}",
                provider=self.provider,
                is_retryable=False,
                original_error=e,
            )

    async def get_quota(self) -> ProviderQuota:
        """Get Originality.ai account credits."""
        if not self.is_configured:
            return ProviderQuota(
                provider=self.provider,
                is_available=False,
                remaining_credits=-1,
            )

        try:
            headers = {
                "X-OAI-API-KEY": self._api_key,
                "Accept": "application/json",
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.API_BASE_URL}/account/credits",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            credits = float(data.get("credits", {}).get("remaining", 0))

            return ProviderQuota(
                provider=self.provider,
                remaining_credits=credits,
                credits_per_check=0.01,  # Per 100 words
                is_available=credits > 0,
            )

        except Exception as e:
            logger.warning(f"Failed to get Originality.ai quota: {e}")
            return ProviderQuota(
                provider=self.provider,
                remaining_credits=-1,
                is_available=True,
            )


class EmbeddingChecker(BasePlagiarismChecker):
    """
    Fallback plagiarism checker using text embeddings.

    This provides a basic similarity check using OpenAI embeddings
    when external plagiarism APIs are unavailable. It checks content
    against a local database of previously generated content.

    Note: This is less comprehensive than dedicated plagiarism services
    as it only checks against locally stored content, not the web.
    """

    def __init__(self):
        super().__init__()
        self._openai_key = os.environ.get("OPENAI_API_KEY", "")
        self._embedding_model = "text-embedding-3-small"
        self._similarity_threshold = 0.85  # Cosine similarity threshold
        self._local_embeddings: Dict[str, Tuple[str, List[float]]] = {}

    @property
    def provider(self) -> PlagiarismProvider:
        return PlagiarismProvider.EMBEDDING

    @property
    def is_configured(self) -> bool:
        return bool(self._openai_key)

    async def _get_embedding(self, text: str) -> List[float]:
        """Get text embedding from OpenAI."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self._openai_key)

            response = await client.embeddings.create(
                model=self._embedding_model,
                input=text[:8000],  # Limit text length
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            raise PlagiarismCheckError(
                f"Failed to generate embedding: {str(e)}",
                provider=self.provider,
                is_retryable=True,
            )

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    async def check(
        self,
        request: PlagiarismCheckRequest,
    ) -> PlagiarismCheckResult:
        """
        Check content using embedding similarity.

        Compares against locally stored content embeddings.
        """
        if not self.is_configured:
            raise PlagiarismCheckError(
                "Embedding checker requires OPENAI_API_KEY for embeddings.",
                provider=self.provider,
                is_retryable=False,
            )

        start_time = time.time()
        check_id = f"emb_{uuid.uuid4().hex[:12]}"
        word_count = self._count_words(request.content)

        try:
            # Get embedding for the content
            content_embedding = await self._get_embedding(request.content)

            matching_sources = []
            highest_similarity = 0.0

            # Compare against stored embeddings
            for doc_id, (doc_url, doc_embedding) in self._local_embeddings.items():
                similarity = self._cosine_similarity(content_embedding, doc_embedding)

                if similarity > self._similarity_threshold:
                    similarity_pct = similarity * 100
                    highest_similarity = max(highest_similarity, similarity_pct)

                    matching_sources.append(MatchingSource(
                        url=doc_url,
                        title=f"Internal Document {doc_id[:8]}",
                        similarity_percentage=similarity_pct,
                        matched_words=int(word_count * similarity),
                        is_exact_match=similarity > 0.95,
                    ))

            # Sort by similarity
            matching_sources.sort(key=lambda x: x.similarity_percentage, reverse=True)

            processing_time = int((time.time() - start_time) * 1000)

            # Overall score based on highest match
            overall_score = highest_similarity if matching_sources else 0.0

            return PlagiarismCheckResult(
                check_id=check_id,
                status=PlagiarismCheckStatus.COMPLETED,
                provider=self.provider,
                overall_score=overall_score,
                risk_level=self._calculate_risk_level(overall_score),
                original_percentage=100 - overall_score,
                matching_sources=matching_sources[:10],
                total_words_checked=word_count,
                total_matched_words=int(word_count * (overall_score / 100)),
                api_credits_used=0.0001,  # Minimal cost for embedding
                processing_time_ms=processing_time,
                metadata={
                    "method": "embedding_similarity",
                    "model": self._embedding_model,
                    "documents_checked": len(self._local_embeddings),
                    "threshold": self._similarity_threshold,
                    "warning": "Only checks against locally stored content, not web sources",
                },
            )

        except Exception as e:
            if isinstance(e, PlagiarismCheckError):
                raise
            raise PlagiarismCheckError(
                f"Embedding check failed: {str(e)}",
                provider=self.provider,
                is_retryable=False,
                original_error=e,
            )

    async def get_quota(self) -> ProviderQuota:
        """Embedding checker uses OpenAI API credits."""
        return ProviderQuota(
            provider=self.provider,
            remaining_credits=-1,  # Uses OpenAI credits
            credits_per_check=0.0001,
            is_available=self.is_configured,
        )

    async def add_document(self, doc_id: str, content: str, url: str = "") -> None:
        """Add a document to the local embedding database."""
        if not self.is_configured:
            return

        try:
            embedding = await self._get_embedding(content)
            self._local_embeddings[doc_id] = (url or f"internal://{doc_id}", embedding)
            logger.debug(f"Added document {doc_id} to embedding database")
        except Exception as e:
            logger.warning(f"Failed to add document to embedding database: {e}")


class PlagiarismCheckerFactory:
    """
    Factory for creating and managing plagiarism checkers.

    Handles provider selection, fallback logic, and caching.
    """

    def __init__(self):
        self._checkers: Dict[PlagiarismProvider, BasePlagiarismChecker] = {}
        self._initialize_checkers()

    def _initialize_checkers(self) -> None:
        """Initialize all available checkers."""
        self._checkers = {
            PlagiarismProvider.COPYSCAPE: CopyscapeChecker(),
            PlagiarismProvider.ORIGINALITY: OriginalityChecker(),
            PlagiarismProvider.EMBEDDING: EmbeddingChecker(),
        }

    def get_checker(
        self,
        provider: Optional[PlagiarismProvider] = None,
    ) -> BasePlagiarismChecker:
        """
        Get a plagiarism checker, optionally for a specific provider.

        If no provider specified, returns first available in priority order:
        1. Copyscape (if configured)
        2. Originality.ai (if configured)
        3. Embedding fallback
        """
        if provider:
            checker = self._checkers.get(provider)
            if checker and checker.is_configured:
                return checker
            raise PlagiarismCheckError(
                f"Provider {provider.value} is not configured",
                provider=provider,
                is_retryable=False,
            )

        # Return first available in priority order
        priority_order = [
            PlagiarismProvider.COPYSCAPE,
            PlagiarismProvider.ORIGINALITY,
            PlagiarismProvider.EMBEDDING,
        ]

        for prov in priority_order:
            checker = self._checkers.get(prov)
            if checker and checker.is_configured:
                return checker

        raise PlagiarismCheckError(
            "No plagiarism checker is configured. Set COPYSCAPE_API_KEY, "
            "ORIGINALITY_API_KEY, or OPENAI_API_KEY for embedding fallback.",
            is_retryable=False,
        )

    def get_available_providers(self) -> List[PlagiarismProvider]:
        """Get list of configured providers."""
        return [
            prov for prov, checker in self._checkers.items()
            if checker.is_configured
        ]

    async def check_with_fallback(
        self,
        request: PlagiarismCheckRequest,
        skip_cache: bool = False,
    ) -> PlagiarismCheckResult:
        """
        Check content with automatic fallback between providers.

        Tries providers in priority order, falling back on failures.
        Results are cached to avoid redundant API calls.
        """
        cache = get_cache()

        # Check cache first (unless skipped)
        if not skip_cache and not request.skip_cache:
            cached_result = cache.get(request.content)
            if cached_result:
                logger.info(f"Returning cached plagiarism result: {cached_result.check_id}")
                return cached_result

        # Determine provider order
        priority_order = [
            PlagiarismProvider.COPYSCAPE,
            PlagiarismProvider.ORIGINALITY,
            PlagiarismProvider.EMBEDDING,
        ]

        # If preferred provider specified, try it first
        if request.preferred_provider:
            priority_order.remove(request.preferred_provider)
            priority_order.insert(0, request.preferred_provider)

        last_error: Optional[PlagiarismCheckError] = None

        for provider in priority_order:
            checker = self._checkers.get(provider)
            if not checker or not checker.is_configured:
                continue

            try:
                logger.info(f"Attempting plagiarism check with {provider.value}")
                result = await checker.check(request)

                # Cache successful result
                cache.set(request.content, result)

                return result

            except PlagiarismCheckError as e:
                logger.warning(f"Plagiarism check failed with {provider.value}: {e}")
                last_error = e

                # Only continue to fallback if error is retryable or provider-specific
                if not e.is_retryable and e.provider is None:
                    raise

        # All providers failed
        if last_error:
            raise last_error

        raise PlagiarismCheckError(
            "No plagiarism checker available",
            is_retryable=False,
        )

    async def get_all_quotas(self) -> List[ProviderQuota]:
        """Get quota information for all configured providers."""
        quotas = []
        for provider, checker in self._checkers.items():
            if checker.is_configured:
                try:
                    quota = await checker.get_quota()
                    quotas.append(quota)
                except Exception as e:
                    logger.warning(f"Failed to get quota for {provider.value}: {e}")
                    quotas.append(ProviderQuota(
                        provider=provider,
                        is_available=False,
                        remaining_credits=-1,
                    ))
        return quotas


# Singleton factory instance
_factory: Optional[PlagiarismCheckerFactory] = None


def get_plagiarism_checker() -> PlagiarismCheckerFactory:
    """Get the singleton plagiarism checker factory."""
    global _factory
    if _factory is None:
        _factory = PlagiarismCheckerFactory()
    return _factory
