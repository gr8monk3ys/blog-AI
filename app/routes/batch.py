"""
Enhanced batch generation endpoints with Tier 1 features.

This module extends the existing bulk generation with:
- CSV import for bulk topics
- Export in multiple formats (CSV, JSON, Markdown)
- Multi-provider support with strategies
- Cost estimation
- Retry failed items

Uses Redis-backed job storage with in-memory fallback for horizontal scaling.
"""

import asyncio
import csv
import io
import json
import logging
import time
import uuid
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response, StreamingResponse

from src.blog.make_blog import (
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
)
from src.storage import get_batch_job_store
from src.text_generation.core import GenerationOptions, create_provider_from_env
from src.types.batch import (
    BatchItemInput,
    CostEstimate,
    CSVExportRow,
    CSVImportRow,
    EnhancedBatchItemResult,
    EnhancedBatchRequest,
    EnhancedBatchStatus,
    ExportFormat,
    JobPriority,
    JobStatus,
    ProviderStrategy,
    RetryRequest,
    estimate_batch_cost,
)
from src.usage import (
    UsageLimitExceeded,
    check_usage_limit,
    increment_usage,
)
from src.usage.quota_service import (
    QuotaExceeded,
    check_quota as async_check_quota,
    increment_usage as async_increment_usage,
)

from ..auth import verify_api_key
from ..middleware import require_pro_tier
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["batch"])

# Get the typed job store for enhanced batch generation
_job_store = get_batch_job_store()

# Provider rotation state for round-robin (this can stay in-memory as it's stateless)
_provider_index: Dict[str, int] = {}


def _get_next_provider(job_id: str, strategy: ProviderStrategy, preferred: str, fallbacks: List[str]) -> str:
    """Get the next provider based on strategy."""
    all_providers = [preferred] + [p for p in fallbacks if p != preferred]

    if strategy == ProviderStrategy.SINGLE:
        return preferred
    elif strategy == ProviderStrategy.ROUND_ROBIN:
        if job_id not in _provider_index:
            _provider_index[job_id] = 0
        idx = _provider_index[job_id] % len(all_providers)
        _provider_index[job_id] += 1
        return all_providers[idx]
    elif strategy == ProviderStrategy.COST_OPTIMIZED:
        # Prefer Gemini (cheapest), then Anthropic, then OpenAI
        cost_order = ["gemini", "anthropic", "openai"]
        for p in cost_order:
            if p in all_providers:
                return p
        return preferred
    elif strategy == ProviderStrategy.QUALITY_OPTIMIZED:
        # Prefer OpenAI (GPT-4), then Anthropic, then Gemini
        quality_order = ["openai", "anthropic", "gemini"]
        for p in quality_order:
            if p in all_providers:
                return p
        return preferred
    else:
        return preferred


async def _generate_single_item_enhanced(
    index: int,
    item: BatchItemInput,
    job_id: str,
    request: EnhancedBatchRequest,
    user_id: str,
) -> EnhancedBatchItemResult:
    """Generate a single content item with enhanced features."""
    start_time = time.time()
    item_id = str(uuid.uuid4())

    try:
        # Check usage limit
        try:
            check_usage_limit(user_id)
        except UsageLimitExceeded as e:
            return EnhancedBatchItemResult(
                index=index,
                item_id=item_id,
                status=JobStatus.FAILED,
                topic=item.topic,
                error=str(e),
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

        # Generate content
        if request.research_enabled:
            blog_post = generate_blog_post_with_research(
                title=item.topic,
                keywords=item.keywords,
                tone=item.tone,
                provider_type=provider_type,
                options=options,
            )
        else:
            blog_post = generate_blog_post(
                title=item.topic,
                keywords=item.keywords,
                tone=item.tone,
                provider_type=provider_type,
                options=options,
            )

        # Post-process if needed
        if request.proofread_enabled or request.humanize_enabled:
            provider = create_provider_from_env(provider_type)
            blog_post = post_process_blog_post(
                blog_post=blog_post,
                proofread=request.proofread_enabled,
                humanize=request.humanize_enabled,
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

        word_count = 0
        for section in blog_post.sections:
            section_data = {"title": section.title, "subtopics": []}
            for subtopic in section.subtopics:
                subtopic_data = {"title": subtopic.title, "content": subtopic.content}
                section_data["subtopics"].append(subtopic_data)
                word_count += len(subtopic.content.split())
            blog_post_data["sections"].append(section_data)

        blog_post_data["word_count"] = word_count

        # Increment usage
        estimated_tokens = 4000  # Rough estimate
        increment_usage(user_id, tokens_used=estimated_tokens, tool_id="batch-generation")

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

    except UsageLimitExceeded as e:
        logger.warning(f"Usage limit exceeded for item {index}: {str(e)}")
        return EnhancedBatchItemResult(
            index=index,
            item_id=item_id,
            status=JobStatus.FAILED,
            topic=item.topic,
            error=f"Usage limit exceeded: {str(e)}",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )
    except ValueError as e:
        logger.warning(f"Validation error for item {index}: {str(e)}")
        return EnhancedBatchItemResult(
            index=index,
            item_id=item_id,
            status=JobStatus.FAILED,
            topic=item.topic,
            error=f"Invalid input: {str(e)}",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating item {index}: {str(e)}", exc_info=True)
        return EnhancedBatchItemResult(
            index=index,
            item_id=item_id,
            status=JobStatus.FAILED,
            topic=item.topic,
            error="Generation failed unexpectedly",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )


async def _process_enhanced_batch(
    job_id: str,
    request: EnhancedBatchRequest,
    user_id: str,
) -> None:
    """Process enhanced batch generation in background."""
    try:
        await _job_store.update_job(
            job_id,
            status=JobStatus.PROCESSING.value,
            started_at=datetime.now().isoformat(),
        )

        results: List[EnhancedBatchItemResult] = []
        semaphore = asyncio.Semaphore(request.parallel_limit)
        providers_used: Dict[str, int] = {}

        async def process_with_semaphore(index: int, item: BatchItemInput) -> EnhancedBatchItemResult:
            async with semaphore:
                if await _job_store.get_cancel_flag(job_id):
                    return EnhancedBatchItemResult(
                        index=index,
                        status=JobStatus.CANCELLED,
                        topic=item.topic,
                        error="Job cancelled",
                        execution_time_ms=0,
                    )
                return await _generate_single_item_enhanced(
                    index=index,
                    item=item,
                    job_id=job_id,
                    request=request,
                    user_id=user_id,
                )

        # Process items with controlled parallelism
        tasks = [
            process_with_semaphore(i, item)
            for i, item in enumerate(request.items)
        ]

        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

            # Track provider usage
            if result.provider_used:
                providers_used[result.provider_used] = providers_used.get(result.provider_used, 0) + 1

            # Update job progress
            completed = len([r for r in results if r.status == JobStatus.COMPLETED])
            failed = len([r for r in results if r.status == JobStatus.FAILED])
            total_cost = sum(r.cost_usd for r in results)
            total_tokens = sum(r.token_count for r in results)

            await _job_store.update_job(
                job_id,
                completed_items=completed,
                failed_items=failed,
                progress_percentage=round(len(results) / len(request.items) * 100, 1),
                actual_cost_usd=round(total_cost, 4),
                total_tokens_used=total_tokens,
                providers_used=providers_used,
            )

            # Send progress via WebSocket
            await manager.send_message(
                {
                    "type": "batch_progress",
                    "job_id": job_id,
                    "completed": len(results),
                    "total": len(request.items),
                    "providers_used": providers_used,
                    "cost_so_far": round(total_cost, 4),
                    "latest_result": {
                        "index": result.index,
                        "success": result.status == JobStatus.COMPLETED,
                        "topic": result.topic,
                        "provider": result.provider_used,
                    },
                },
                request.conversation_id,
            )

        # Sort and store results
        results.sort(key=lambda r: r.index)
        await _job_store.save_results(job_id, results)

        # Update final status
        completed = len([r for r in results if r.status == JobStatus.COMPLETED])
        failed = len([r for r in results if r.status == JobStatus.FAILED])

        final_status = JobStatus.COMPLETED.value if failed == 0 else JobStatus.PARTIAL.value
        await _job_store.update_job(
            job_id,
            status=final_status,
            completed_items=completed,
            failed_items=failed,
            progress_percentage=100.0,
            completed_at=datetime.now().isoformat(),
            can_cancel=False,
            can_retry_failed=failed > 0,
        )

        # Get updated job for final cost
        job = await _job_store.get_job(job_id)
        actual_cost = job.actual_cost_usd if job else 0.0

        # Send completion message
        await manager.send_message(
            {
                "type": "batch_completed",
                "job_id": job_id,
                "completed": completed,
                "failed": failed,
                "total": len(request.items),
                "total_cost": actual_cost,
                "providers_used": providers_used,
            },
            request.conversation_id,
        )

        logger.info(f"Batch job {job_id} completed: {completed} success, {failed} failed")

    except asyncio.CancelledError:
        logger.info(f"Batch job {job_id} was cancelled")
        await _job_store.update_job(
            job_id,
            status=JobStatus.CANCELLED.value,
            completed_at=datetime.now().isoformat(),
            can_cancel=False,
        )
    except Exception as e:
        logger.error(f"Unexpected batch job {job_id} failure: {str(e)}", exc_info=True)
        await _job_store.update_job(
            job_id,
            status=JobStatus.FAILED.value,
            completed_at=datetime.now().isoformat(),
            can_cancel=False,
        )


# ============================================================================
# CSV Import/Export Endpoints
# ============================================================================

@router.post("/import/csv", status_code=status.HTTP_202_ACCEPTED)
async def import_csv_batch(
    file: UploadFile = File(..., description="CSV file with topics"),
    provider_strategy: ProviderStrategy = Query(default=ProviderStrategy.SINGLE),
    preferred_provider: str = Query(default="openai"),
    research_enabled: bool = Query(default=False),
    proofread_enabled: bool = Query(default=True),
    humanize_enabled: bool = Query(default=False),
    parallel_limit: int = Query(default=3, ge=1, le=10),
    conversation_id: str = Query(...),
    background_tasks: BackgroundTasks = None,
    user_id: str = Depends(require_pro_tier),
) -> Dict:
    """
    Import topics from CSV and start batch generation.

    CSV format (header row required):
    topic,keywords,tone,content_type,custom_instructions

    Example:
    topic,keywords,tone,content_type
    "AI in Healthcare","AI,healthcare,diagnosis",professional,blog
    "Sustainable Tech","green,sustainability",informative,blog
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    try:
        # Read CSV content
        content = await file.read()
        content_str = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content_str))

        # Parse rows
        items: List[BatchItemInput] = []
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            if "topic" not in row or not row["topic"].strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Row {row_num}: Missing required 'topic' column"
                )

            # Parse keywords (comma-separated)
            keywords = []
            if row.get("keywords"):
                keywords = [k.strip() for k in row["keywords"].split(",") if k.strip()]

            items.append(BatchItemInput(
                topic=row["topic"].strip(),
                keywords=keywords,
                tone=row.get("tone", "professional").strip(),
                content_type=row.get("content_type", "blog").strip(),
                custom_instructions=row.get("custom_instructions", "").strip() or None,
            ))

        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or has no valid rows"
            )

        if len(items) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum 100 items per batch. Found {len(items)}."
            )

        # Create enhanced request
        request = EnhancedBatchRequest(
            items=items,
            provider_strategy=provider_strategy,
            preferred_provider=preferred_provider,
            fallback_providers=["anthropic", "gemini"],
            parallel_limit=parallel_limit,
            research_enabled=research_enabled,
            proofread_enabled=proofread_enabled,
            humanize_enabled=humanize_enabled,
            conversation_id=conversation_id,
            name=f"CSV Import: {file.filename}",
        )

        # Estimate cost
        cost_estimate = estimate_batch_cost(
            items=items,
            provider=preferred_provider,
            strategy=provider_strategy,
            research_enabled=research_enabled,
        )

        # Create job with ownership
        job_id = str(uuid.uuid4())
        job_status = EnhancedBatchStatus(
            job_id=job_id,
            name=request.name,
            status=JobStatus.PENDING,
            total_items=len(items),
            provider_strategy=provider_strategy,
            estimated_cost_usd=cost_estimate.estimated_cost_usd,
        )

        # Save job to Redis-backed storage with ownership
        await _job_store.save_job(job_id, job_status, user_id)
        await _job_store.set_cancel_flag(job_id, False)

        # Start processing
        background_tasks.add_task(
            _process_enhanced_batch,
            job_id,
            request,
            user_id,
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": "pending",
            "total_items": len(items),
            "estimated_cost_usd": cost_estimate.estimated_cost_usd,
            "cost_breakdown": cost_estimate.cost_breakdown,
            "message": f"Imported {len(items)} topics from CSV. Processing started.",
        }

    except HTTPException:
        raise
    except UnicodeDecodeError as e:
        logger.warning(f"CSV encoding error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file encoding error. Please use UTF-8 encoding."
        )
    except csv.Error as e:
        logger.warning(f"CSV parsing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected CSV import error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process CSV file. Please try again."
        )


@router.get("/template/csv")
async def get_csv_template() -> Response:
    """Get a CSV template for batch import."""
    template = """topic,keywords,tone,content_type,custom_instructions
"AI in Healthcare","AI,healthcare,medical,diagnosis",professional,blog,
"The Future of Remote Work","remote work,productivity,work from home",informative,blog,
"Sustainable Technology Trends","green tech,sustainability,environment",casual,blog,Focus on practical tips
"""
    return Response(
        content=template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=batch_template.csv"}
    )


@router.get("/export/{job_id}")
async def export_batch_results(
    job_id: str,
    format: ExportFormat = Query(default=ExportFormat.JSON),
    user_id: str = Depends(verify_api_key),
) -> Response:
    """
    Export batch results in various formats.

    Formats:
    - json: Full JSON with all metadata
    - csv: Tabular format with key fields
    - markdown: Human-readable markdown
    - zip: All content as individual files
    """
    job = await _job_store.get_job_if_owned(job_id, user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied"
        )
    if job.status not in [JobStatus.COMPLETED, JobStatus.PARTIAL, JobStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is still processing"
        )

    results = await _job_store.get_results(job_id)

    if format == ExportFormat.JSON:
        export_data = {
            "job_id": job_id,
            "job_name": job.name,
            "status": job.status.value,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "total_cost_usd": job.actual_cost_usd,
            "total_tokens": job.total_tokens_used,
            "providers_used": job.providers_used,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "results": [r.model_dump() for r in results],
        }
        return Response(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.json"}
        )

    elif format == ExportFormat.CSV:
        # Import CSV sanitization for formula injection protection
        try:
            from app.validators import sanitize_csv_field
        except ImportError:
            # Fallback sanitization if validators not available
            def sanitize_csv_field(v):
                if not v:
                    return v
                v = str(v)
                if v and v[0] in {"=", "+", "-", "@", "\t", "\r", "\n"}:
                    return f"'{v}"
                return v

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "index", "topic", "status", "title", "word_count",
            "provider", "execution_time_ms", "cost_usd", "error"
        ])

        for result in results:
            title = ""
            word_count = 0
            if result.content:
                title = result.content.get("title", "")
                word_count = result.content.get("word_count", 0)

            # Sanitize string fields to prevent CSV formula injection
            writer.writerow([
                result.index,
                sanitize_csv_field(result.topic),
                result.status.value,
                sanitize_csv_field(title),
                word_count,
                result.provider_used or "",
                result.execution_time_ms,
                result.cost_usd,
                sanitize_csv_field(result.error or ""),
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.csv"}
        )

    elif format == ExportFormat.MARKDOWN:
        lines = [
            f"# Batch Generation Results",
            f"",
            f"**Job ID:** {job_id}",
            f"**Status:** {job.status.value}",
            f"**Total Items:** {job.total_items}",
            f"**Completed:** {job.completed_items}",
            f"**Failed:** {job.failed_items}",
            f"**Total Cost:** ${job.actual_cost_usd:.4f}",
            f"**Completed At:** {job.completed_at}",
            f"",
            f"---",
            f"",
        ]

        for result in results:
            status_icon = "✅" if result.status == JobStatus.COMPLETED else "❌"
            lines.append(f"## {status_icon} {result.index + 1}. {result.topic}")
            lines.append(f"")

            if result.status == JobStatus.COMPLETED and result.content:
                lines.append(f"**Title:** {result.content.get('title', 'N/A')}")
                lines.append(f"**Provider:** {result.provider_used}")
                lines.append(f"**Word Count:** {result.content.get('word_count', 0)}")
                lines.append(f"**Cost:** ${result.cost_usd:.4f}")
                lines.append(f"")

                # Add content preview
                if result.content.get("sections"):
                    lines.append(f"### Content Preview")
                    for section in result.content["sections"][:2]:  # First 2 sections
                        lines.append(f"")
                        lines.append(f"#### {section['title']}")
                        for subtopic in section.get("subtopics", [])[:1]:  # First subtopic
                            preview = subtopic.get("content", "")[:500]
                            if len(subtopic.get("content", "")) > 500:
                                preview += "..."
                            lines.append(f"")
                            lines.append(f"**{subtopic['title']}**")
                            lines.append(f"")
                            lines.append(preview)
            else:
                lines.append(f"**Error:** {result.error}")

            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")

        return Response(
            content="\n".join(lines),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.md"}
        )

    elif format == ExportFormat.ZIP:
        # Create ZIP with individual content files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add summary JSON
            summary = {
                "job_id": job_id,
                "status": job.status.value,
                "total_items": job.total_items,
                "completed_items": job.completed_items,
                "total_cost_usd": job.actual_cost_usd,
            }
            zf.writestr("summary.json", json.dumps(summary, indent=2))

            # Add individual content files
            for result in results:
                if result.status == JobStatus.COMPLETED and result.content:
                    # Create markdown content
                    content_lines = [
                        f"# {result.content.get('title', result.topic)}",
                        f"",
                        f"*{result.content.get('description', '')}*",
                        f"",
                    ]

                    for section in result.content.get("sections", []):
                        content_lines.append(f"## {section['title']}")
                        content_lines.append("")
                        for subtopic in section.get("subtopics", []):
                            content_lines.append(f"### {subtopic['title']}")
                            content_lines.append("")
                            content_lines.append(subtopic.get("content", ""))
                            content_lines.append("")

                    # Safe filename
                    safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in result.topic)
                    filename = f"{result.index + 1:03d}_{safe_topic[:50]}.md"
                    zf.writestr(f"content/{filename}", "\n".join(content_lines))

                elif result.error:
                    error_content = f"# Error: {result.topic}\n\n{result.error}"
                    safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in result.topic)
                    filename = f"{result.index + 1:03d}_{safe_topic[:50]}_ERROR.txt"
                    zf.writestr(f"errors/{filename}", error_content)

        zip_buffer.seek(0)
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.zip"}
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown export format: {format}"
    )


# ============================================================================
# Cost Estimation Endpoint
# ============================================================================

@router.post("/estimate")
async def estimate_cost(
    items: List[BatchItemInput],
    provider_strategy: ProviderStrategy = Query(default=ProviderStrategy.SINGLE),
    preferred_provider: str = Query(default="openai"),
    research_enabled: bool = Query(default=False),
    user_id: str = Depends(verify_api_key),
) -> CostEstimate:
    """
    Estimate cost for a batch job before running it.

    Returns cost breakdown by provider and recommendations.
    """
    if len(items) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 items per batch"
        )

    return estimate_batch_cost(
        items=items,
        provider=preferred_provider,
        strategy=provider_strategy,
        research_enabled=research_enabled,
    )


# ============================================================================
# Retry Failed Items
# ============================================================================

@router.post("/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_failed_items(
    job_id: str,
    retry_request: RetryRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Retry failed items in a batch job.

    Optionally specify item indices or retry all failed items.
    Can also change the provider for retry attempts.
    """
    job = await _job_store.get_job_if_owned(job_id, user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied"
        )
    if not job.can_retry_failed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No failed items to retry or job still processing"
        )

    results = await _job_store.get_results(job_id)
    failed_results = [r for r in results if r.status == JobStatus.FAILED]

    if retry_request.item_indices:
        # Retry specific items
        retry_indices = set(retry_request.item_indices)
        failed_results = [r for r in failed_results if r.index in retry_indices]

    if not failed_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No matching failed items to retry"
        )

    # Create retry job
    retry_job_id = str(uuid.uuid4())

    # Build items for retry
    retry_items = [
        BatchItemInput(topic=r.topic, keywords=[], tone="professional")
        for r in failed_results
    ]

    # Use original job settings with optional provider override
    original_request = EnhancedBatchRequest(
        items=retry_items,
        provider_strategy=ProviderStrategy.SINGLE,
        preferred_provider=retry_request.change_provider or "openai",
        fallback_providers=["anthropic", "gemini"],
        parallel_limit=3,
        research_enabled=False,
        proofread_enabled=True,
        humanize_enabled=False,
        conversation_id=f"retry-{job_id}",
        name=f"Retry of {job.name or job_id}",
    )

    retry_job_status = EnhancedBatchStatus(
        job_id=retry_job_id,
        name=original_request.name,
        status=JobStatus.PENDING,
        total_items=len(retry_items),
        provider_strategy=original_request.provider_strategy,
    )

    # Save job to Redis-backed storage with ownership
    await _job_store.save_job(retry_job_id, retry_job_status, user_id)
    await _job_store.set_cancel_flag(retry_job_id, False)

    # Start retry processing
    background_tasks.add_task(
        _process_enhanced_batch,
        retry_job_id,
        original_request,
        user_id,
    )

    return {
        "success": True,
        "original_job_id": job_id,
        "retry_job_id": retry_job_id,
        "items_retrying": len(retry_items),
        "message": f"Retrying {len(retry_items)} failed items",
    }


# ============================================================================
# Enhanced Status and Results Endpoints
# ============================================================================

@router.get("/jobs")
async def list_batch_jobs(
    status_filter: Optional[JobStatus] = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """List batch jobs with optional status filter (only shows user's own jobs)."""
    # Only show jobs owned by the current user (multi-tenant isolation)
    status_str = status_filter.value if status_filter else None
    jobs = await _job_store.list_jobs(
        user_id=user_id,
        status=status_str,
        limit=limit,
        offset=offset,
    )

    # Note: The job_store.list_jobs already returns paginated results
    # We need to get total count separately for proper pagination info
    all_jobs = await _job_store.list_jobs(user_id=user_id, status=status_str, limit=1000, offset=0)
    total = len(all_jobs)

    return {
        "jobs": [j.model_dump() for j in jobs],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


@router.get("/{job_id}")
async def get_batch_status(
    job_id: str,
    user_id: str = Depends(verify_api_key),
) -> EnhancedBatchStatus:
    """Get enhanced batch job status."""
    job = await _job_store.get_job_if_owned(job_id, user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied"
        )
    return job


@router.get("/{job_id}/results")
async def get_batch_results(
    job_id: str,
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """Get batch results with full content."""
    job = await _job_store.get_job_if_owned(job_id, user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied"
        )
    if job.status not in [JobStatus.COMPLETED, JobStatus.PARTIAL, JobStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is still processing"
        )

    results = await _job_store.get_results(job_id)

    return {
        "success": job.status == JobStatus.COMPLETED,
        "job_id": job_id,
        "status": job.status.value,
        "total_items": job.total_items,
        "completed_items": job.completed_items,
        "failed_items": job.failed_items,
        "total_cost_usd": job.actual_cost_usd,
        "total_tokens": job.total_tokens_used,
        "providers_used": job.providers_used,
        "results": [r.model_dump() for r in results],
    }


@router.post("/{job_id}/cancel")
async def cancel_batch_job(
    job_id: str,
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """Cancel a running batch job."""
    job = await _job_store.get_job_if_owned(job_id, user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied"
        )
    if not job.can_cancel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} cannot be cancelled"
        )

    await _job_store.set_cancel_flag(job_id, True)
    await _job_store.update_job(
        job_id,
        status=JobStatus.CANCELLED.value,
        can_cancel=False,
    )

    return {
        "success": True,
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancellation requested",
    }
