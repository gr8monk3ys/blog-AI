"""
Export endpoints for multi-format content export.

Supports exporting content to:
- Markdown (.md)
- HTML (styled)
- Plain Text (.txt)
- PDF
- WordPress block format
- Medium-compatible HTML

Authorization:
- All export endpoints require content.view permission in the organization
- Publishing exports (WordPress, Medium) require content.publish permission
- Pass the organization ID via X-Organization-ID header for org-scoped access
"""

import html
import logging
import re
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from src.organizations import AuthorizationContext, Permission
from ..dependencies.organization import get_optional_organization_context


def sanitize_html_content(text: str) -> str:
    """
    Sanitize user-provided content for safe HTML embedding.

    Escapes HTML special characters to prevent XSS attacks when
    embedding user content in HTML templates.

    Args:
        text: User-provided text that may contain HTML/JS

    Returns:
        HTML-escaped text safe for embedding
    """
    return html.escape(text, quote=True)


# URL scheme whitelist for safe link/image handling
# Empty string allows relative URLs (e.g., /path/to/page or ../image.png)
ALLOWED_URL_SCHEMES = frozenset({'http', 'https', 'mailto', ''})


def _sanitize_url(url: str) -> str:
    """
    Sanitize URL to prevent XSS via dangerous schemes like javascript:.

    Only allows http, https, mailto, and relative URLs.
    All other schemes (javascript:, data:, vbscript:, etc.) are blocked.

    Args:
        url: The URL to sanitize

    Returns:
        The original URL if safe, or '#' if the scheme is dangerous
    """
    try:
        # Strip whitespace and normalize
        cleaned_url = url.strip()
        parsed = urlparse(cleaned_url)
        # Check if scheme is in whitelist (case-insensitive)
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
            return '#'
        return cleaned_url
    except Exception:
        # If URL parsing fails for any reason, return safe fallback
        return '#'


def _replace_markdown_link(match: re.Match) -> str:
    """
    Replace markdown link with sanitized HTML anchor tag.

    Validates URL scheme before creating anchor to prevent XSS.

    Args:
        match: Regex match object with groups (link_text, url)

    Returns:
        HTML anchor tag with sanitized href
    """
    link_text = match.group(1)
    url = _sanitize_url(match.group(2))
    # Escape link text to prevent XSS via link text content
    safe_text = sanitize_html_content(link_text)
    # Escape URL for safe attribute embedding
    safe_url = html.escape(url, quote=True)
    return f'<a href="{safe_url}">{safe_text}</a>'


def _replace_markdown_image(match: re.Match) -> str:
    """
    Replace markdown image with sanitized HTML img tag.

    Validates URL scheme before creating image to prevent XSS.

    Args:
        match: Regex match object with groups (alt_text, src_url)

    Returns:
        HTML img tag with sanitized src
    """
    alt_text = match.group(1)
    src_url = _sanitize_url(match.group(2))
    # Escape alt text to prevent XSS via alt attribute
    safe_alt = html.escape(alt_text, quote=True)
    # Escape URL for safe attribute embedding
    safe_src = html.escape(src_url, quote=True)
    return f'<img src="{safe_src}" alt="{safe_alt}" />'

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


def _require_permission_if_org(auth_ctx: AuthorizationContext, permission: Permission) -> None:
    """
    Export endpoints transform user-provided content and don't read org-owned
    resources. Only enforce org permissions when an org context is provided.
    """
    if not auth_ctx.organization_id:
        return
    if not auth_ctx.is_org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    if not auth_ctx.has_permission(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission.value}",
        )


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
    """Convert markdown content to plain text.

    Uses non-greedy quantifiers to prevent ReDoS attacks.
    """
    text = content
    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic - using non-greedy quantifiers to prevent ReDoS
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    # Remove links but keep text - using non-greedy quantifiers
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    # Remove images - using non-greedy quantifiers
    text = re.sub(r"!\[(.*?)\]\(.+?\)", r"\1", text)
    # Remove code blocks - using non-greedy quantifiers
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`(.+?)`", r"\1", text)
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
    """Convert markdown content to styled HTML with XSS protection."""
    # Sanitize the title to prevent XSS
    safe_title = sanitize_html_content(title)

    html_content = content

    # Convert headers
    html_content = re.sub(r"^######\s+(.+)$", r"<h6>\1</h6>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^#####\s+(.+)$", r"<h5>\1</h5>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^####\s+(.+)$", r"<h4>\1</h4>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^###\s+(.+)$", r"<h3>\1</h3>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^##\s+(.+)$", r"<h2>\1</h2>", html_content, flags=re.MULTILINE)
    html_content = re.sub(r"^#\s+(.+)$", r"<h1>\1</h1>", html_content, flags=re.MULTILINE)

    # Convert bold and italic - using non-greedy quantifiers to prevent ReDoS
    html_content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html_content)
    html_content = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html_content)
    html_content = re.sub(r"__(.+?)__", r"<strong>\1</strong>", html_content)
    html_content = re.sub(r"_(.+?)_", r"<em>\1</em>", html_content)

    # Convert links (with URL sanitization to prevent XSS via javascript: scheme)
    # Using non-greedy quantifiers to prevent ReDoS
    html_content = re.sub(r"\[(.+?)\]\((.+?)\)", _replace_markdown_link, html_content)

    # Convert images (with URL sanitization to prevent XSS via javascript: scheme)
    # Using non-greedy quantifiers to prevent ReDoS
    html_content = re.sub(r"!\[(.*?)\]\((.+?)\)", _replace_markdown_image, html_content)

    # Convert code blocks - using non-greedy quantifiers to prevent ReDoS
    def replace_code_block(match):
        lang = match.group(1) or ""
        code = match.group(2)
        # Sanitize language identifier to prevent XSS
        safe_lang = re.sub(r"[^a-zA-Z0-9_-]", "", lang)
        return f'<pre><code class="language-{safe_lang}">{html.escape(code)}</code></pre>'
    html_content = re.sub(r"```(\w*)\n(.*?)```", replace_code_block, html_content, flags=re.DOTALL)

    # Convert inline code - using non-greedy quantifier to prevent ReDoS
    html_content = re.sub(r"`(.+?)`", r"<code>\1</code>", html_content)

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

    # Build metadata section (with XSS sanitization)
    meta_html = ""
    if metadata:
        meta_parts = []
        if metadata.get("date"):
            safe_date = sanitize_html_content(str(metadata["date"]))
            meta_parts.append(f'<span class="date">{safe_date}</span>')
        if metadata.get("description"):
            safe_desc = sanitize_html_content(str(metadata["description"]))
            meta_parts.append(f'<p class="description">{safe_desc}</p>')
        if metadata.get("tags"):
            safe_tags = ", ".join(sanitize_html_content(str(t)) for t in metadata["tags"])
            meta_parts.append(f'<p class="tags">Tags: {safe_tags}</p>')
        if metadata.get("toolName"):
            safe_tool = sanitize_html_content(str(metadata["toolName"]))
            meta_parts.append(f'<p class="tool">Generated with: {safe_tool}</p>')
        if meta_parts:
            meta_html = f'<div class="metadata">{"".join(meta_parts)}</div>'

    # Build full HTML document (using sanitized title)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
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
            <h1>{safe_title}</h1>
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
    """Convert content to WordPress Gutenberg block format with XSS protection."""
    # Sanitize title for safe HTML embedding
    safe_title = sanitize_html_content(title)

    blocks = []

    # Add title block
    blocks.append(f'<!-- wp:heading {{"level":1}} -->\n<h1 class="wp-block-heading">{safe_title}</h1>\n<!-- /wp:heading -->')

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
    """Convert content to Medium-compatible HTML with XSS protection."""
    # Sanitize title for safe HTML embedding
    safe_title = sanitize_html_content(title)

    html_parts = [f"<h1>{safe_title}</h1>"]

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
                # Using non-greedy quantifiers to prevent ReDoS
                text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
                html_parts.append(f"<p>{text}</p>")
                current_paragraph = []

            level = min(len(re.match(r"^#+", line).group()), 4)  # Medium supports up to h4
            text = re.sub(r"^#+\s*", "", line)
            html_parts.append(f"<h{level}>{text}</h{level}>")

        # Handle list items
        elif re.match(r"^[\*\-\+]\s+", line):
            if current_paragraph:
                text = " ".join(current_paragraph)
                # Using non-greedy quantifiers to prevent ReDoS
                text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
                html_parts.append(f"<p>{text}</p>")
                current_paragraph = []

            if not in_list:
                in_list = True
                list_items = []
            item_text = re.sub(r"^[\*\-\+]\s+", "", line)
            # Using non-greedy quantifiers to prevent ReDoS
            item_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item_text)
            item_text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", item_text)
            list_items.append(f"<li>{item_text}</li>")

        # Handle blockquotes
        elif line.startswith(">"):
            if current_paragraph:
                text = " ".join(current_paragraph)
                # Using non-greedy quantifiers to prevent ReDoS
                text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
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
                # Using non-greedy quantifiers to prevent ReDoS
                text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
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
        # Using non-greedy quantifiers to prevent ReDoS
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
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
async def export_markdown(
    request: ExportRequest,
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Export content as markdown file.

    Returns a downloadable .md file with proper formatting.

    **Authorization:** Requires content.view permission in the organization.
    """
    logger.info(f"Exporting markdown for: {request.title[:50]}")

    try:
        _require_permission_if_org(auth_ctx, Permission.CONTENT_VIEW)

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
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error in markdown export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains unsupported characters",
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting markdown: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export markdown",
        )


@router.post("/html")
async def export_html(
    request: ExportRequest,
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Export content as styled HTML file.

    Returns a downloadable .html file with embedded CSS styling.

    **Authorization:** Requires content.view permission in the organization.
    """
    logger.info(f"Exporting HTML for: {request.title[:50]}")

    try:
        _require_permission_if_org(auth_ctx, Permission.CONTENT_VIEW)

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
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error in HTML export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains unsupported characters",
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting HTML: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export HTML",
        )


@router.post("/text")
async def export_text(
    request: ExportRequest,
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Export content as plain text file.

    Strips markdown formatting and returns a .txt file.

    **Authorization:** Requires content.view permission in the organization.
    """
    logger.info(f"Exporting plain text for: {request.title[:50]}")

    try:
        _require_permission_if_org(auth_ctx, Permission.CONTENT_VIEW)

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
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error in text export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains unsupported characters",
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export text",
        )


@router.post("/pdf")
async def export_pdf(
    request: ExportRequest,
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Export content as PDF file.

    Generates a styled PDF document from the content.

    **Authorization:** Requires content.view permission in the organization.
    """
    logger.info(f"Exporting PDF for: {request.title[:50]}")

    try:
        _require_permission_if_org(auth_ctx, Permission.CONTENT_VIEW)

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
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error in PDF export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains unsupported characters",
        )
    except MemoryError as e:
        logger.error(f"Memory error generating PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Content too large to generate PDF",
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export PDF",
        )


@router.post("/wordpress", response_model=PublishResponse)
async def export_wordpress(
    request: ExportRequest,
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Export content as WordPress Gutenberg block format.

    Returns content formatted for pasting into WordPress block editor.

    **Authorization:** Requires content.publish permission in the organization.
    """
    logger.info(f"Exporting WordPress format for: {request.title[:50]}")

    try:
        _require_permission_if_org(auth_ctx, Permission.CONTENT_PUBLISH)

        wordpress_content = content_to_wordpress_blocks(request.content, request.title)

        return PublishResponse(
            success=True,
            content=wordpress_content,
            format="wordpress",
        )
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error in WordPress export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains unsupported characters",
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting WordPress format: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export WordPress format",
        )


@router.post("/medium", response_model=PublishResponse)
async def export_medium(
    request: ExportRequest,
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
):
    """
    Export content as Medium-compatible HTML.

    Returns HTML that can be pasted into Medium's editor.

    **Authorization:** Requires content.publish permission in the organization.
    """
    logger.info(f"Exporting Medium format for: {request.title[:50]}")

    try:
        _require_permission_if_org(auth_ctx, Permission.CONTENT_PUBLISH)

        medium_content = content_to_medium_html(request.content, request.title)

        return PublishResponse(
            success=True,
            content=medium_content,
            format="medium",
        )
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error in Medium export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content contains unsupported characters",
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting Medium format: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export Medium format",
        )
