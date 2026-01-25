"""
Content Remix Service.

Main orchestration layer for transforming content across multiple formats.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

from src.remix.analyzer import ContentAnalyzer
from src.remix.adapters import get_adapter, FormatAdapter
from src.types.remix import (
    ContentAnalysis,
    ContentFormat,
    QualityScore,
    RemixedContent,
    RemixRequest,
    RemixResponse,
    RemixPreviewRequest,
    RemixPreviewResponse,
    get_format_info,
)


class RemixService:
    """Orchestrates content remixing across multiple formats."""

    def __init__(self, provider_type: str = "openai"):
        self.provider_type = provider_type
        self.analyzer = ContentAnalyzer(provider_type)
        self._executor = ThreadPoolExecutor(max_workers=5)

    async def remix(self, request: RemixRequest) -> RemixResponse:
        """Transform content into multiple formats."""
        start_time = time.time()

        # Analyze source content
        analysis = self.analyzer.analyze(request.source_content)

        # Get brand voice if profile specified
        brand_voice = None
        if request.brand_profile_id:
            brand_voice = await self._load_brand_voice(request.brand_profile_id)
        elif request.tone_override:
            brand_voice = request.tone_override

        # Transform to each target format
        remixed_content: List[RemixedContent] = []

        # Run transformations in parallel for better performance
        tasks = [
            self._transform_format(analysis, fmt, brand_voice)
            for fmt in request.target_formats
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, RemixedContent):
                remixed_content.append(result)
            elif isinstance(result, Exception):
                # Log error but continue with other formats
                logger.warning("Transform error: %s", result)

        # Calculate average quality
        if remixed_content:
            avg_quality = sum(r.quality_score.overall for r in remixed_content) / len(remixed_content)
        else:
            avg_quality = 0.0

        total_time = int((time.time() - start_time) * 1000)

        return RemixResponse(
            success=len(remixed_content) > 0,
            source_analysis=analysis,
            remixed_content=remixed_content,
            total_generation_time_ms=total_time,
            average_quality_score=avg_quality,
            message=f"Generated {len(remixed_content)} format(s) successfully"
            if remixed_content else "Failed to generate any formats",
        )

    async def _transform_format(
        self,
        analysis: ContentAnalysis,
        format: ContentFormat,
        brand_voice: Optional[str],
    ) -> RemixedContent:
        """Transform content to a specific format."""
        start_time = time.time()

        # Get adapter for this format
        adapter = get_adapter(format, self.provider_type)

        # Run transformation in thread pool (sync LLM calls)
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(
            self._executor,
            lambda: adapter.transform(analysis, brand_voice)
        )

        # Score quality
        quality_score = await loop.run_in_executor(
            self._executor,
            lambda: adapter.score_quality(content, analysis)
        )

        # Calculate metrics
        word_count = self._count_words(content)
        char_count = self._count_chars(content)
        gen_time = int((time.time() - start_time) * 1000)

        return RemixedContent(
            format=format,
            content=content,
            quality_score=quality_score,
            word_count=word_count,
            character_count=char_count,
            generation_time_ms=gen_time,
            provider_used=self.provider_type,
        )

    async def preview(self, request: RemixPreviewRequest) -> RemixPreviewResponse:
        """Generate a quick preview without full transformation."""
        # Quick analysis (cached if possible)
        analysis = self.analyzer.analyze(request.source_content)

        format_info = get_format_info(request.target_format)

        # Generate sample hook using the adapter
        adapter = get_adapter(request.target_format, self.provider_type)

        # Estimate length based on format
        estimated_length = format_info.get("max_length", 1000)

        # Extract key elements that will be emphasized
        key_elements = analysis.key_points[:5]

        # Generate a quick sample hook
        sample_hook = self._generate_sample_hook(analysis, request.target_format)

        # Calculate confidence based on content fit
        confidence = self._calculate_confidence(analysis, request.target_format)

        return RemixPreviewResponse(
            format=request.target_format,
            estimated_length=estimated_length,
            key_elements=key_elements,
            sample_hook=sample_hook,
            confidence=confidence,
        )

    def _generate_sample_hook(
        self,
        analysis: ContentAnalysis,
        format: ContentFormat,
    ) -> str:
        """Generate a sample hook for preview."""
        # Format-specific hook templates
        templates = {
            ContentFormat.TWITTER_THREAD: f"🧵 {analysis.key_points[0] if analysis.key_points else analysis.title}",
            ContentFormat.LINKEDIN_POST: f"I learned something important about {analysis.title.lower()}...",
            ContentFormat.EMAIL_NEWSLETTER: f"This week: {analysis.summary[:100]}...",
            ContentFormat.YOUTUBE_SCRIPT: f"What if I told you {analysis.main_argument[:80]}?",
            ContentFormat.INSTAGRAM_CAROUSEL: f"Save this for later 📌 {analysis.key_points[0] if analysis.key_points else ''}",
            ContentFormat.PODCAST_NOTES: f"In this episode: {analysis.summary[:100]}",
            ContentFormat.TIKTOK_SCRIPT: f"POV: You just learned about {analysis.title.lower()}",
        }

        return templates.get(format, f"Check out: {analysis.title}")

    def _calculate_confidence(
        self,
        analysis: ContentAnalysis,
        format: ContentFormat,
    ) -> float:
        """Calculate confidence score for format transformation."""
        base_confidence = 0.7

        # Boost for matching suggested formats
        if format in analysis.suggested_formats:
            base_confidence += 0.15

        # Adjust based on content length vs format requirements
        format_info = get_format_info(format)
        max_length = format_info.get("max_length", 5000)

        if analysis.word_count < max_length * 0.1:
            # Very short content for this format
            base_confidence -= 0.1
        elif analysis.word_count > max_length * 2:
            # Will need significant condensing
            base_confidence -= 0.05

        # Boost for having enough key points
        if len(analysis.key_points) >= 5:
            base_confidence += 0.05

        return min(1.0, max(0.3, base_confidence))

    async def _load_brand_voice(self, profile_id: str) -> Optional[str]:
        """Load brand voice from profile."""
        # TODO: Integrate with brand profile storage
        # For now, return None to use default voice
        return None

    def _count_words(self, content: Dict[str, Any]) -> int:
        """Count words in content recursively."""
        count = 0
        for value in content.values():
            if isinstance(value, str):
                count += len(value.split())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        count += len(item.split())
                    elif isinstance(item, dict):
                        count += self._count_words(item)
            elif isinstance(value, dict):
                count += self._count_words(value)
        return count

    def _count_chars(self, content: Dict[str, Any]) -> int:
        """Count characters in content recursively."""
        count = 0
        for value in content.values():
            if isinstance(value, str):
                count += len(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        count += len(item)
                    elif isinstance(item, dict):
                        count += self._count_chars(item)
            elif isinstance(value, dict):
                count += self._count_chars(value)
        return count


# Singleton service instance
_service_instance: Optional[RemixService] = None


def get_remix_service(provider_type: str = "openai") -> RemixService:
    """Get or create the remix service singleton."""
    global _service_instance
    if _service_instance is None or _service_instance.provider_type != provider_type:
        _service_instance = RemixService(provider_type)
    return _service_instance


async def remix_content(request: RemixRequest) -> RemixResponse:
    """Convenience function to remix content."""
    service = get_remix_service()
    return await service.remix(request)


async def preview_remix(request: RemixPreviewRequest) -> RemixPreviewResponse:
    """Convenience function to preview remix."""
    service = get_remix_service()
    return await service.preview(request)
