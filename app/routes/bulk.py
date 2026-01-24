"""
Bulk generation endpoints for processing multiple content items.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.blog.make_blog import (
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
)
from src.text_generation.core import GenerationOptions, create_provider_from_env
from src.usage import (
    UsageLimitExceeded,
    check_usage_limit,
    get_usage_stats,
    increment_usage,
)

from ..auth import verify_api_key
from ..models import (
    BulkGenerationItemResult,
    BulkGenerationRequest,
    BulkGenerationResponse,
    BulkGenerationStatus,
)
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bulk", tags=["bulk"])

# In-memory job storage (in production, use Redis or database)
_jobs: Dict[str, BulkGenerationStatus] = {}
_job_results: Dict[str, List[BulkGenerationItemResult]] = {}
_cancel_flags: Dict[str, bool] = {}


def _get_job(job_id: str) -> Optional[BulkGenerationStatus]:
    """Get a job by ID."""
    return _jobs.get(job_id)


def _update_job(job_id: str, **kwargs) -> None:
    """Update job status."""
    if job_id in _jobs:
        for key, value in kwargs.items():
            setattr(_jobs[job_id], key, value)


async def _generate_single_item(
    index: int,
    topic: str,
    keywords: List[str],
    tone: str,
    research: bool,
    proofread: bool,
    humanize: bool,
    user_id: str,
) -> BulkGenerationItemResult:
    """Generate a single content item."""
    start_time = time.time()

    try:
        # Check usage limit before generation
        try:
            check_usage_limit(user_id)
        except UsageLimitExceeded as e:
            return BulkGenerationItemResult(
                index=index,
                success=False,
                topic=topic,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Generate blog post
        if research:
            blog_post = generate_blog_post_with_research(
                title=topic,
                keywords=keywords,
                tone=tone,
                provider_type="openai",
                options=options,
            )
        else:
            blog_post = generate_blog_post(
                title=topic,
                keywords=keywords,
                tone=tone,
                provider_type="openai",
                options=options,
            )

        # Post-process if needed
        if proofread or humanize:
            provider = create_provider_from_env("openai")
            blog_post = post_process_blog_post(
                blog_post=blog_post,
                proofread=proofread,
                humanize=humanize,
                provider=provider,
                options=options,
            )

        # Convert to serializable format
        blog_post_data = {
            "title": blog_post.title,
            "description": blog_post.description,
            "date": blog_post.date,
            "image": blog_post.image,
            "tags": blog_post.tags,
            "sections": [],
        }

        for section in blog_post.sections:
            section_data = {"title": section.title, "subtopics": []}
            for subtopic in section.subtopics:
                subtopic_data = {"title": subtopic.title, "content": subtopic.content}
                section_data["subtopics"].append(subtopic_data)
            blog_post_data["sections"].append(section_data)

        # Increment usage after successful generation
        increment_usage(user_id, tokens_used=4000, tool_id="bulk-blog-generation")

        execution_time_ms = int((time.time() - start_time) * 1000)

        return BulkGenerationItemResult(
            index=index,
            success=True,
            topic=topic,
            content=blog_post_data,
            execution_time_ms=execution_time_ms,
        )

    except Exception as e:
        logger.error(f"Error generating item {index}: {str(e)}", exc_info=True)
        return BulkGenerationItemResult(
            index=index,
            success=False,
            topic=topic,
            error=str(e),
            execution_time_ms=int((time.time() - start_time) * 1000),
        )


async def _process_bulk_generation(
    job_id: str,
    request: BulkGenerationRequest,
    user_id: str,
) -> None:
    """Process bulk generation in background."""
    try:
        _update_job(
            job_id,
            status="processing",
            started_at=datetime.now().isoformat(),
        )

        results: List[BulkGenerationItemResult] = []
        semaphore = asyncio.Semaphore(request.parallel_limit)

        async def process_with_semaphore(index: int, item) -> BulkGenerationItemResult:
            async with semaphore:
                # Check for cancellation
                if _cancel_flags.get(job_id, False):
                    return BulkGenerationItemResult(
                        index=index,
                        success=False,
                        topic=item.topic,
                        error="Job cancelled",
                        execution_time_ms=0,
                    )
                return await _generate_single_item(
                    index=index,
                    topic=item.topic,
                    keywords=item.keywords,
                    tone=item.tone,
                    research=request.research,
                    proofread=request.proofread,
                    humanize=request.humanize,
                    user_id=user_id,
                )

        # Process items with controlled parallelism
        tasks = [
            process_with_semaphore(i, item)
            for i, item in enumerate(request.items)
        ]

        # Process and update progress
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

            # Update job progress
            completed = len([r for r in results if r.success])
            failed = len([r for r in results if not r.success])
            _update_job(
                job_id,
                completed_items=completed,
                failed_items=failed,
                progress_percentage=round(len(results) / len(request.items) * 100, 1),
            )

            # Send progress via WebSocket
            await manager.send_message(
                {
                    "type": "bulk_progress",
                    "job_id": job_id,
                    "completed": len(results),
                    "total": len(request.items),
                    "latest_result": {
                        "index": result.index,
                        "success": result.success,
                        "topic": result.topic,
                    },
                },
                request.conversation_id,
            )

        # Sort results by index
        results.sort(key=lambda r: r.index)
        _job_results[job_id] = results

        # Update final status
        completed = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])
        _update_job(
            job_id,
            status="completed",
            completed_items=completed,
            failed_items=failed,
            progress_percentage=100.0,
            completed_at=datetime.now().isoformat(),
            can_cancel=False,
        )

        # Send completion message
        await manager.send_message(
            {
                "type": "bulk_completed",
                "job_id": job_id,
                "completed": completed,
                "failed": failed,
                "total": len(request.items),
            },
            request.conversation_id,
        )

        logger.info(f"Bulk generation job {job_id} completed: {completed} success, {failed} failed")

    except Exception as e:
        logger.error(f"Bulk generation job {job_id} failed: {str(e)}", exc_info=True)
        _update_job(
            job_id,
            status="failed",
            completed_at=datetime.now().isoformat(),
            can_cancel=False,
        )


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def start_bulk_generation(
    request: BulkGenerationRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Start a bulk generation job.

    This endpoint accepts multiple items and processes them in parallel
    with rate limiting. Progress updates are sent via WebSocket.

    Args:
        request: Bulk generation request with items and settings.
        background_tasks: FastAPI background tasks.
        user_id: The authenticated user ID.

    Returns:
        Job ID and initial status for tracking progress.
    """
    logger.info(
        f"Bulk generation requested by user: {user_id}, items: {len(request.items)}"
    )

    # Check if user has enough usage remaining
    try:
        remaining = check_usage_limit(user_id)
        if remaining != -1 and remaining < len(request.items):
            # User doesn't have enough remaining, but allow partial processing
            logger.warning(
                f"User {user_id} has {remaining} generations remaining, "
                f"but requested {len(request.items)}"
            )
    except UsageLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": str(e),
                "tier": e.tier.value,
                "limit_type": e.limit_type,
                "upgrade_url": "/pricing",
            },
        )

    # Create job
    job_id = str(uuid.uuid4())
    _jobs[job_id] = BulkGenerationStatus(
        job_id=job_id,
        status="pending",
        total_items=len(request.items),
        completed_items=0,
        failed_items=0,
        progress_percentage=0.0,
        can_cancel=True,
    )
    _cancel_flags[job_id] = False

    # Add conversation message
    user_message = {
        "role": "user",
        "content": f"Started bulk generation of {len(request.items)} items",
        "timestamp": datetime.now().isoformat(),
    }
    conversations.append(request.conversation_id, user_message)

    # Start background processing
    background_tasks.add_task(
        _process_bulk_generation,
        job_id,
        request,
        user_id,
    )

    return {
        "success": True,
        "job_id": job_id,
        "status": "pending",
        "total_items": len(request.items),
        "message": f"Bulk generation started. Track progress via WebSocket or GET /bulk/status/{job_id}",
    }


@router.get("/status/{job_id}")
async def get_bulk_status(
    job_id: str,
    user_id: str = Depends(verify_api_key),
) -> BulkGenerationStatus:
    """
    Get the status of a bulk generation job.

    Args:
        job_id: The job identifier.
        user_id: The authenticated user ID.

    Returns:
        Current job status and progress.
    """
    job = _get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job


@router.get("/results/{job_id}")
async def get_bulk_results(
    job_id: str,
    user_id: str = Depends(verify_api_key),
) -> BulkGenerationResponse:
    """
    Get the results of a completed bulk generation job.

    Args:
        job_id: The job identifier.
        user_id: The authenticated user ID.

    Returns:
        Complete results including all generated content.
    """
    job = _get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if job.status not in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is still processing. Current status: {job.status}",
        )

    results = _job_results.get(job_id, [])

    # Calculate total execution time
    total_time_ms = sum(r.execution_time_ms for r in results)

    return BulkGenerationResponse(
        success=job.status == "completed" and job.failed_items == 0,
        job_id=job_id,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        results=results,
        total_execution_time_ms=total_time_ms,
        message=f"Completed {job.completed_items} of {job.total_items} items",
    )


@router.post("/cancel/{job_id}")
async def cancel_bulk_job(
    job_id: str,
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Cancel a running bulk generation job.

    Args:
        job_id: The job identifier.
        user_id: The authenticated user ID.

    Returns:
        Cancellation status.
    """
    job = _get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if not job.can_cancel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} cannot be cancelled (status: {job.status})",
        )

    # Set cancel flag
    _cancel_flags[job_id] = True
    _update_job(job_id, status="cancelled", can_cancel=False)

    logger.info(f"Bulk generation job {job_id} cancelled by user {user_id}")

    return {
        "success": True,
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancellation requested. In-progress items will complete.",
    }
