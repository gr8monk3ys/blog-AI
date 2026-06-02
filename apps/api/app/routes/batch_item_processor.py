"""
Batch item processor.

Generates a single content item within an enhanced batch run (quota check,
provider selection, generation, optional research/post-processing, usage
accounting, and cost estimation). Extracted from app/routes/batch.py so the
router stays focused on HTTP handlers (see docs/REMEDIATION_PLAN.md P2.3).
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from src.blog.make_blog import (
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
)
from src.text_generation.core import GenerationOptions, create_provider_from_env
from src.types.batch import (
    BatchItemInput,
    EnhancedBatchItemResult,
    EnhancedBatchRequest,
    JobStatus,
)
from src.usage.quota_service import QuotaExceeded
from src.usage.quota_service import check_quota as async_check_quota

from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation
from .batch_providers import _get_next_provider

logger = logging.getLogger(__name__)


async def _generate_single_item_enhanced(
    index: int,
    item: BatchItemInput,
    job_id: str,
    request: EnhancedBatchRequest,
    user_id: str,
    brand_voice: Optional[str],
) -> EnhancedBatchItemResult:
    """Generate a single content item with enhanced features."""
    start_time = time.time()
    item_id = str(uuid.uuid4())

    try:
        try:
            await async_check_quota(user_id)
        except QuotaExceeded as e:
            return EnhancedBatchItemResult(
                index=index,
                item_id=item_id,
                status=JobStatus.FAILED,
                topic=item.topic,
                error=f"Quota exceeded: {sanitize_error_message(str(e))}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Get provider based on strategy
        provider_type = _get_next_provider(
            job_id,
            request.provider_strategy,
            request.preferred_provider,
            request.fallback_providers,
        )

        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        def _generate() -> Any:
            if request.research_enabled:
                blog_post = generate_blog_post_with_research(
                    title=item.topic,
                    keywords=item.keywords,
                    tone=item.tone,
                    brand_voice=brand_voice,
                    provider_type=provider_type,
                    options=options,
                )
            else:
                blog_post = generate_blog_post(
                    title=item.topic,
                    keywords=item.keywords,
                    tone=item.tone,
                    brand_voice=brand_voice,
                    provider_type=provider_type,
                    options=options,
                )

            if request.proofread_enabled or request.humanize_enabled:
                provider = create_provider_from_env(provider_type)
                blog_post = post_process_blog_post(
                    blog_post=blog_post,
                    proofread=request.proofread_enabled,
                    humanize=request.humanize_enabled,
                    provider=provider,
                    options=options,
                )
            return blog_post

        # Run potentially-blocking LLM calls off the event loop.
        blog_post = await asyncio.to_thread(_generate)

        # Convert to serializable format
        blog_post_data = {
            "title": blog_post.title,
            "description": blog_post.description,
            "date": blog_post.date,
            "image": blog_post.image,
            "tags": blog_post.tags,
            "sections": [],
        }

        word_count = 0
        for section in blog_post.sections:
            section_data = {"title": section.title, "subtopics": []}
            for subtopic in section.subtopics:
                subtopic_data = {"title": subtopic.title, "content": subtopic.content}
                section_data["subtopics"].append(subtopic_data)
                word_count += len(subtopic.content.split())
            blog_post_data["sections"].append(section_data)

        blog_post_data["word_count"] = word_count

        sources = []
        for s in getattr(blog_post, "sources", []) or []:
            try:
                sources.append(
                    {
                        "id": int(getattr(s, "id", 0) or 0),
                        "title": str(getattr(s, "title", "") or ""),
                        "url": str(getattr(s, "url", "") or ""),
                        "snippet": str(getattr(s, "snippet", "") or ""),
                        "provider": str(getattr(s, "provider", "") or ""),
                    }
                )
            except Exception:
                continue
        if sources:
            blog_post_data["sources"] = sources

        estimated_tokens = 4000  # Rough estimate
        await increment_usage_for_operation(
            user_id=user_id,
            operation_type="batch",
            tokens_used=estimated_tokens,
            metadata={
                "job_id": job_id,
                "topic": item.topic[:50],
                "research": request.research_enabled,
            },
        )

        # Estimate cost
        from src.types.batch import PROVIDER_COSTS

        costs = PROVIDER_COSTS.get(provider_type, PROVIDER_COSTS["openai"])
        cost_usd = (estimated_tokens / 1000) * (costs["input"] + costs["output"]) / 2

        execution_time_ms = int((time.time() - start_time) * 1000)

        return EnhancedBatchItemResult(
            index=index,
            item_id=item_id,
            status=JobStatus.COMPLETED,
            topic=item.topic,
            content=blog_post_data,
            provider_used=provider_type,
            execution_time_ms=execution_time_ms,
            token_count=estimated_tokens,
            cost_usd=round(cost_usd, 4),
            started_at=datetime.fromtimestamp(start_time).isoformat(),
            completed_at=datetime.now().isoformat(),
        )

    except QuotaExceeded as e:
        logger.warning("Quota exceeded for batch item %s: %s", index, e)
        return EnhancedBatchItemResult(
            index=index,
            item_id=item_id,
            status=JobStatus.FAILED,
            topic=item.topic,
            error=f"Quota exceeded: {sanitize_error_message(str(e))}",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )
    except ValueError as e:
        logger.warning(f"Validation error for item {index}: {str(e)}")
        return EnhancedBatchItemResult(
            index=index,
            item_id=item_id,
            status=JobStatus.FAILED,
            topic=item.topic,
            error=f"Invalid input: {sanitize_error_message(str(e))}",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )
    except Exception as e:
        logger.error(
            f"Unexpected error generating item {index}: {str(e)}", exc_info=True
        )
        return EnhancedBatchItemResult(
            index=index,
            item_id=item_id,
            status=JobStatus.FAILED,
            topic=item.topic,
            error="Generation failed unexpectedly",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )
