"""
Export endpoints for multi-format content export.

Supports exporting content to:
- Markdown (.md)
- HTML (styled)
- Plain Text (.txt)
- PDF
- WordPress block format
- Medium-compatible HTML
"""

import logging
import re
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    """Request model for export endpoints."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    content_type: str = Field(default="blog", pattern=r"^(blog|book|tool)$")
    metadata: Optional[Dict] = Field(default=None)


class PublishResponse(BaseModel):
    """Response model for publishing format exports."""

    success: bool
    content: str
    format: str


def sanitize_filename(title: str) -> str:
    """Sanitize title for use as filename."""
    sanitized = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
    sanitized = re.sub(r"\s+", "-", sanitized).strip("-")
    return sanitized[:50] or "export"


def markdown_to_plain_text(content: str) -> str:
    """Convert markdown content to plain text."""
    text = content
    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # Remove code blocks
    text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove blockquotes
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*{3,}$", "", text, flags=re.MULTILINE)
    # Clean up list markers
    text = re.sub(r"^[\*\-\+]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def markdown_to_html(content: str, title: str, metadata: Optional[Dict] = None) -> str:
    """Convert markdown content to styled HTML."""
    html_content = content

    # Convert headers
    html_content = re.sub(r"^######\s+(.+)$", r"<h6>\1</h6>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^#####\s+(.+)$", r"<h5>\1</h5>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^####\s+(.+)$", r"<h4>\1</h4>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^###\s+(.+)$", r"<h3>\1</h3>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^##\s+(.+)$", r"<h2>\1</h2>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^#\s+(.+)$", r"<h1>\1</h1>", html_content, flags=re.MULTILINE)

    # Convert bold and italic
    html_content = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", html_content)
    html_content = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html_content)
    html_content = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", html_content)
    html_content = re.sub(r"_([^_]+)_", r"<em>\1</em>", html_content)

    # Convert links
    html_content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html_content)

    # Convert images
    html_content = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" />', html_content)

    # Convert code blocks
    def replace_code_block(match):
        lang = match.group(1) or ""
        code = match.group(2)
        return f'<pre><code class="language-{lang}">{code}</code></pre>'
    html_content = re.sub(r"```(\w*)\n(.*?)```", replace_code_block, html_content, flags=re.DOTALL)

    # Convert inline code
    html_content = re.sub(r"`([^`]+)`", r"<code>\1</code>", html_content)

    # Convert blockquotes
    html_content = re.sub(r"^>\s+(.+)$", r"<blockquote>\1</blockquote>", html_content, flags=re.MULTILINE)

    # Convert unordered lists
    def process_lists(text):
        lines = text.split("\n")
        result = []
        in_list = False
        for line in lines:
            if re.match(r"^[\*\-\+]\s+", line):
                if not in_list:
                    result.append("<ul>")
                    in_list = True
                item = re.sub(r"^[\*\-\+]\s+", "", line)
                result.append(f"<li>{item}</li>")
            else:
                if in_list:
                    result.append("</ul>")
                    in_list = False
                result.append(line)
        if in_list:
            result.append("</ul>")
        return "\n".join(result)

    html_content = process_lists(html_content)

    # Convert paragraphs
    paragraphs = html_content.split("\n\n")
    processed_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not re.match(r"^<(h[1-6]|ul|ol|li|blockquote|pre|div)", p):
            processed_paragraphs.append(f"<p>{p}</p>")
        elif p:
            processed_paragraphs.append(p)
    html_content = "\n".join(processed_paragraphs)

    # Build metadata section
    meta_html = ""
    if metadata:
        meta_parts = []
        if metadata.get("date"):
            meta_parts.append(f'<span class="date">{metadata["date"]}</span>')
        if metadata.get("description"):
            meta_parts.append(f'<p class="description">{metadata["description"]}</p>')
        if metadata.get("tags"):
            tags = ", ".join(metadata["tags"])
            meta_parts.append(f'<p class="tags">Tags: {tags}</p>')
        if metadata.get("toolName"):
            meta_parts.append(f'<p class="tool">Generated with: {metadata["toolName"]}</p>')
        if meta_parts:
            meta_html = f'<div class="metadata">{"".join(meta_parts)}</div>'

    # Build full HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary-color: #4f46e5;
            --text-color: #1f2937;
            --light-text: #6b7280;
            --bg-color: #ffffff;
            --code-bg: #f3f4f6;
            --border-color: #e5e7eb;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.7;
            color: var(--text-color);
            background-color: var(--bg-color);
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            line-height: 1.2;
        }}

        h2 {{
            font-size: 1.875rem;
            font-weight: 600;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
        }}

        h3 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 0.75rem;
        }}

        h4, h5, h6 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }}

        p {{
            margin-bottom: 1.25rem;
        }}

        a {{
            color: var(--primary-color);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        ul, ol {{
            margin-bottom: 1.25rem;
            padding-left: 1.5rem;
        }}

        li {{
            margin-bottom: 0.5rem;
        }}

        blockquote {{
            border-left: 4px solid var(--primary-color);
            padding-left: 1rem;
            margin: 1.5rem 0;
            color: var(--light-text);
            font-style: italic;
        }}

        code {{
            background-color: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.875rem;
        }}

        pre {{
            background-color: var(--code-bg);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1.5rem 0;
        }}

        pre code {{
            background: none;
            padding: 0;
        }}

        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1.5rem 0;
        }}

        .metadata {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
            color: var(--light-text);
            font-size: 0.875rem;
        }}

        .metadata .date {{
            display: block;
            margin-bottom: 0.5rem;
        }}

        .metadata .description {{
            margin-bottom: 0.5rem;
        }}

        .metadata .tags, .metadata .tool {{
            font-size: 0.8rem;
            margin-bottom: 0.25rem;
        }}

        .footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
            color: var(--light-text);
            font-size: 0.8rem;
            text-align: center;
        }}

        @media (max-width: 640px) {{
            body {{
                padding: 1rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            h2 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <article>
        <header>
            <h1>{title}</h1>
            {meta_html}
        </header>
        <main>
            {html_content}
        </main>
        <footer class="footer">
            <p>Generated with Blog AI on {datetime.now().strftime("%B %d, %Y")}</p>
        </footer>
    </article>
</body>
</html>"""

    return html


def content_to_wordpress_blocks(content: str, title: str) -> str:
    """Convert content to WordPress Gutenberg block format."""
    blocks = []

    # Add title block
    blocks.append(f'<!-- wp:heading {{"level":1}} -->\n<h1 class="wp-block-heading">{title}</h1>\n<!-- /wp:heading -->')

    lines = content.split("\n")
    current_paragraph = []
    in_list = False
    list_items = []

    for line in lines:
        line = line.strip()

        # Handle headers
        if line.startswith("#"):
            # Flush current paragraph
            if current_paragraph:
                text = " ".join(current_paragraph)
                blocks.append(f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->')
                current_paragraph = []

            level = len(re.match(r"^#+", line).group())
            text = re.sub(r"^#+\s*", "", line)
            blocks.append(f'<!-- wp:heading {{"level":{level}}} -->\n<h{level} class="wp-block-heading">{text}</h{level}>\n<!-- /wp:heading -->')

        # Handle list items
        elif re.match(r"^[\*\-\+]\s+", line):
            if current_paragraph:
                text = " ".join(current_paragraph)
                blocks.append(f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->')
                current_paragraph = []

            if not in_list:
                in_list = True
                list_items = []
            item_text = re.sub(r"^[\*\-\+]\s+", "", line)
            list_items.append(f"<li>{item_text}</li>")

        # Handle empty lines
        elif not line:
            if in_list:
                items_html = "\n".join(list_items)
                blocks.append(f'<!-- wp:list -->\n<ul class="wp-block-list">\n{items_html}\n</ul>\n<!-- /wp:list -->')
                in_list = False
                list_items = []
            elif current_paragraph:
                text = " ".join(current_paragraph)
                blocks.append(f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->')
                current_paragraph = []

        # Handle regular text
        else:
            if in_list:
                items_html = "\n".join(list_items)
                blocks.append(f'<!-- wp:list -->\n<ul class="wp-block-list">\n{items_html}\n</ul>\n<!-- /wp:list -->')
                in_list = False
                list_items = []
            current_paragraph.append(line)

    # Flush remaining content
    if in_list:
        items_html = "\n".join(list_items)
        blocks.append(f'<!-- wp:list -->\n<ul class="wp-block-list">\n{items_html}\n</ul>\n<!-- /wp:list -->')
    elif current_paragraph:
        text = " ".join(current_paragraph)
        blocks.append(f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->')

    return "\n\n".join(blocks)


def content_to_medium_html(content: str, title: str) -> str:
    """Convert content to Medium-compatible HTML."""
    html_parts = [f"<h1>{title}</h1>"]

    lines = content.split("\n")
    current_paragraph = []
    in_list = False
    list_items = []

    for line in lines:
        line = line.strip()

        # Handle headers
        if line.startswith("#"):
            if current_paragraph:
                text = " ".join(current_paragraph)
                text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
                html_parts.append(f"<p>{text}</p>")
                current_paragraph = []

            level = min(len(re.match(r"^#+", line).group()), 4)  # Medium supports up to h4
            text = re.sub(r"^#+\s*", "", line)
            html_parts.append(f"<h{level}>{text}</h{level}>")

        # Handle list items
        elif re.match(r"^[\*\-\+]\s+", line):
            if current_paragraph:
                text = " ".join(current_paragraph)
                text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
                html_parts.append(f"<p>{text}</p>")
                current_paragraph = []

            if not in_list:
                in_list = True
                list_items = []
            item_text = re.sub(r"^[\*\-\+]\s+", "", line)
            item_text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", item_text)
            item_text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", item_text)
            list_items.append(f"<li>{item_text}</li>")

        # Handle blockquotes
        elif line.startswith(">"):
            if current_paragraph:
                text = " ".join(current_paragraph)
                text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
                html_parts.append(f"<p>{text}</p>")
                current_paragraph = []
            if in_list:
                html_parts.append(f"<ul>{''.join(list_items)}</ul>")
                in_list = False
                list_items = []
            quote_text = line.lstrip("> ")
            html_parts.append(f"<blockquote>{quote_text}</blockquote>")

        # Handle empty lines
        elif not line:
            if in_list:
                html_parts.append(f"<ul>{''.join(list_items)}</ul>")
                in_list = False
                list_items = []
            elif current_paragraph:
                text = " ".join(current_paragraph)
                text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
                html_parts.append(f"<p>{text}</p>")
                current_paragraph = []

        # Handle regular text
        else:
            if in_list:
                html_parts.append(f"<ul>{''.join(list_items)}</ul>")
                in_list = False
                list_items = []
            current_paragraph.append(line)

    # Flush remaining content
    if in_list:
        html_parts.append(f"<ul>{''.join(list_items)}</ul>")
    elif current_paragraph:
        text = " ".join(current_paragraph)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
        html_parts.append(f"<p>{text}</p>")

    return "\n".join(html_parts)


def generate_pdf_content(content: str, title: str, metadata: Optional[Dict] = None) -> bytes:
    """
    Generate PDF content from markdown.

    Uses a simple HTML-to-PDF approach that works without external dependencies.
    For production, consider using weasyprint, reportlab, or wkhtmltopdf.
    """
    # Convert to HTML first
    html_content = markdown_to_html(content, title, metadata)

    # Add print-specific styles
    html_content = html_content.replace(
        "</style>",
        """
        @media print {
            body {
                max-width: none;
                padding: 0.5in;
            }

            .footer {
                position: fixed;
                bottom: 0.5in;
                left: 0;
                right: 0;
            }
        }
        </style>"""
    )

    # Return HTML as bytes (browser will handle PDF conversion on client)
    # In production, use a proper PDF library
    return html_content.encode("utf-8")


@router.post("/markdown")
async def export_markdown(request: ExportRequest):
    """
    Export content as markdown file.

    Returns a downloadable .md file with proper formatting.
    """
    logger.info(f"Exporting markdown for: {request.title[:50]}")

    try:
        # Build markdown content with metadata header
        md_content = f"# {request.title}\n\n"

        if request.metadata:
            if request.metadata.get("date"):
                md_content += f"*{request.metadata['date']}*\n\n"
            if request.metadata.get("description"):
                md_content += f"> {request.metadata['description']}\n\n"
            if request.metadata.get("tags"):
                tags = ", ".join(request.metadata["tags"])
                md_content += f"**Tags:** {tags}\n\n"
            md_content += "---\n\n"

        md_content += request.content
        md_content += f"\n\n---\n\n*Generated with Blog AI on {datetime.now().strftime('%B %d, %Y')}*"

        filename = sanitize_filename(request.title) + ".md"

        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        logger.error(f"Error exporting markdown: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export markdown",
        )


@router.post("/html")
async def export_html(request: ExportRequest):
    """
    Export content as styled HTML file.

    Returns a downloadable .html file with embedded CSS styling.
    """
    logger.info(f"Exporting HTML for: {request.title[:50]}")

    try:
        html_content = markdown_to_html(
            request.content, request.title, request.metadata
        )
        filename = sanitize_filename(request.title) + ".html"

        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        logger.error(f"Error exporting HTML: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export HTML",
        )


@router.post("/text")
async def export_text(request: ExportRequest):
    """
    Export content as plain text file.

    Strips markdown formatting and returns a .txt file.
    """
    logger.info(f"Exporting plain text for: {request.title[:50]}")

    try:
        text_content = f"{request.title}\n{'=' * len(request.title)}\n\n"

        if request.metadata:
            if request.metadata.get("date"):
                text_content += f"Date: {request.metadata['date']}\n"
            if request.metadata.get("description"):
                text_content += f"Description: {request.metadata['description']}\n"
            if request.metadata.get("tags"):
                tags = ", ".join(request.metadata["tags"])
                text_content += f"Tags: {tags}\n"
            text_content += "\n" + "-" * 40 + "\n\n"

        text_content += markdown_to_plain_text(request.content)
        text_content += f"\n\n" + "-" * 40 + f"\nGenerated with Blog AI on {datetime.now().strftime('%B %d, %Y')}"

        filename = sanitize_filename(request.title) + ".txt"

        return Response(
            content=text_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        logger.error(f"Error exporting text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export text",
        )


@router.post("/pdf")
async def export_pdf(request: ExportRequest):
    """
    Export content as PDF file.

    Generates a styled PDF document from the content.
    """
    logger.info(f"Exporting PDF for: {request.title[:50]}")

    try:
        # Try to use weasyprint if available
        try:
            from weasyprint import HTML

            html_content = markdown_to_html(
                request.content, request.title, request.metadata
            )
            pdf_bytes = HTML(string=html_content).write_pdf()
            filename = sanitize_filename(request.title) + ".pdf"

            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Cache-Control": "no-cache",
                },
            )
        except ImportError:
            # Fall back to HTML with print styles if weasyprint not available
            logger.warning("weasyprint not installed, returning print-ready HTML")
            html_content = generate_pdf_content(
                request.content, request.title, request.metadata
            )
            filename = sanitize_filename(request.title) + ".html"

            return Response(
                content=html_content,
                media_type="text/html",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Cache-Control": "no-cache",
                    "X-PDF-Fallback": "true",
                },
            )
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export PDF",
        )


@router.post("/wordpress", response_model=PublishResponse)
async def export_wordpress(request: ExportRequest):
    """
    Export content as WordPress Gutenberg block format.

    Returns content formatted for pasting into WordPress block editor.
    """
    logger.info(f"Exporting WordPress format for: {request.title[:50]}")

    try:
        wordpress_content = content_to_wordpress_blocks(request.content, request.title)

        return PublishResponse(
            success=True,
            content=wordpress_content,
            format="wordpress",
        )
    except Exception as e:
        logger.error(f"Error exporting WordPress format: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export WordPress format",
        )


@router.post("/medium", response_model=PublishResponse)
async def export_medium(request: ExportRequest):
    """
    Export content as Medium-compatible HTML.

    Returns HTML that can be pasted into Medium's editor.
    """
    logger.info(f"Exporting Medium format for: {request.title[:50]}")

    try:
        medium_content = content_to_medium_html(request.content, request.title)

        return PublishResponse(
            success=True,
            content=medium_content,
            format="medium",
        )
    except Exception as e:
        logger.error(f"Error exporting Medium format: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export Medium format",
        )
