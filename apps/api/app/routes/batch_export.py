"""
Batch results export endpoints.

Serves completed batch results in JSON / CSV / Markdown / ZIP formats.
Split out of app/routes/batch.py so the lifecycle router stays focused
(docs/REMEDIATION_PLAN.md Phase 3.2 / P2.3). Same /batch prefix; route paths
are unchanged.
"""

import csv
import io
import json
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from src.organizations import AuthorizationContext
from src.storage import get_batch_job_store
from src.types.batch import ExportFormat, JobStatus

from ..dependencies import require_content_access

router = APIRouter(prefix="/batch", tags=["batch"])

_job_store = get_batch_job_store()


@router.get("/export/{job_id}")
async def export_batch_results(
    job_id: str,
    format: ExportFormat = Query(default=ExportFormat.JSON),
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> Response:
    """
    Export batch results in various formats.

    Formats:
    - json: Full JSON with all metadata
    - csv: Tabular format with key fields
    - markdown: Human-readable markdown
    - zip: All content as individual files

    **Authorization:** Requires content.view permission in the organization.
    """
    # Use organization_id for scoping if available, fallback to user_id
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    job = await _job_store.get_job_if_owned(job_id, scope_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or access denied",
        )
    if job.status not in [JobStatus.COMPLETED, JobStatus.PARTIAL, JobStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is still processing",
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
            headers={
                "Content-Disposition": f"attachment; filename=batch_{job_id}.json"
            },
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
        writer.writerow(
            [
                "index",
                "topic",
                "status",
                "title",
                "word_count",
                "provider",
                "execution_time_ms",
                "cost_usd",
                "error",
            ]
        )

        for result in results:
            title = ""
            word_count = 0
            if result.content:
                title = result.content.get("title", "")
                word_count = result.content.get("word_count", 0)

            # Sanitize string fields to prevent CSV formula injection
            writer.writerow(
                [
                    result.index,
                    sanitize_csv_field(result.topic),
                    result.status.value,
                    sanitize_csv_field(title),
                    word_count,
                    result.provider_used or "",
                    result.execution_time_ms,
                    result.cost_usd,
                    sanitize_csv_field(result.error or ""),
                ]
            )

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.csv"},
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
                        for subtopic in section.get("subtopics", [])[
                            :1
                        ]:  # First subtopic
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
            headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.md"},
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
                    safe_topic = "".join(
                        c if c.isalnum() or c in " -_" else "_" for c in result.topic
                    )
                    filename = f"{result.index + 1:03d}_{safe_topic[:50]}.md"
                    zf.writestr(f"content/{filename}", "\n".join(content_lines))

                elif result.error:
                    error_content = f"# Error: {result.topic}\n\n{result.error}"
                    safe_topic = "".join(
                        c if c.isalnum() or c in " -_" else "_" for c in result.topic
                    )
                    filename = f"{result.index + 1:03d}_{safe_topic[:50]}_ERROR.txt"
                    zf.writestr(f"errors/{filename}", error_content)

        zip_buffer.seek(0)
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.zip"},
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown export format: {format}",
    )
