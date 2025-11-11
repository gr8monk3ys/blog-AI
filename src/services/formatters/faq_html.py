"""HTML formatter for FAQ documents.

Formats FAQ documents as semantic HTML with Schema.org markup
for better SEO and accessibility.
"""

import html
import logging
from collections import defaultdict

from ...models.faq import FAQ
from .base import Formatter

logger = logging.getLogger(__name__)


class FAQHTMLFormatter(Formatter[FAQ]):
    """
    Format FAQ documents as HTML with Schema.org FAQPage markup.

    Creates semantic HTML with:
    - Proper heading hierarchy
    - Schema.org FAQPage structured data
    - Accessible markup (ARIA labels, semantic HTML)
    - Optional styling

    Example:
        >>> formatter = FAQHTMLFormatter()
        >>> html_content = formatter.format(faq)
        >>> with open("faq.html", "w") as f:
        ...     f.write(html_content)
    """

    def __init__(
        self,
        include_schema: bool = True,
        include_styles: bool = True,
        standalone: bool = True,
    ):
        """
        Initialize HTML formatter.

        Args:
            include_schema: Include Schema.org FAQPage markup (default: True)
            include_styles: Include embedded CSS (default: True)
            standalone: Create standalone HTML document (default: True)
        """
        self._include_schema = include_schema
        self._include_styles = include_styles
        self._standalone = standalone

    def format(self, content: FAQ) -> str:
        """
        Format FAQ as HTML.

        Args:
            content: FAQ document to format

        Returns:
            Formatted HTML string
        """
        logger.debug(f"Formatting FAQ as HTML: {content.metadata.title}")

        if self._standalone:
            return self._format_standalone(content)
        else:
            return self._format_fragment(content)

    def _format_standalone(self, faq: FAQ) -> str:
        """Format as standalone HTML document."""
        parts = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            self._format_head(faq),
            "<body>",
            self._format_fragment(faq),
            "</body>",
            "</html>",
        ]
        return "\n".join(parts)

    def _format_head(self, faq: FAQ) -> str:
        """Format HTML head section."""
        lines = [
            "<head>",
            '  <meta charset="UTF-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"  <title>{html.escape(faq.metadata.title)}</title>",
        ]

        if faq.metadata.description:
            lines.append(
                f'  <meta name="description" content="{html.escape(faq.metadata.description)}">'
            )

        if self._include_styles:
            lines.append(self._get_styles())

        lines.append("</head>")
        return "\n".join(lines)

    def _format_fragment(self, faq: FAQ) -> str:
        """Format as HTML fragment (no html/body tags)."""
        sections = []

        # Container with Schema.org markup
        if self._include_schema:
            sections.append('<article itemscope itemtype="https://schema.org/FAQPage">')
        else:
            sections.append('<article class="faq-document">')

        # Header
        sections.append(self._format_header(faq))

        # Introduction
        if faq.introduction:
            sections.append(self._format_introduction(faq.introduction))

        # FAQ Items
        sections.append(self._format_items(faq))

        # Conclusion
        if faq.conclusion:
            sections.append(self._format_conclusion(faq.conclusion))

        # Footer
        sections.append(self._format_footer(faq))

        sections.append("</article>")

        return "\n\n".join(sections)

    def _format_header(self, faq: FAQ) -> str:
        """Format header section."""
        lines = [
            '  <header class="faq-header">',
            f"    <h1>{html.escape(faq.metadata.title)}</h1>",
        ]

        if faq.metadata.description:
            lines.append(
                f'    <p class="faq-description">{html.escape(faq.metadata.description)}</p>'
            )

        # Metadata
        meta_parts = []
        if faq.metadata.author:
            meta_parts.append(f'<span class="author">{html.escape(faq.metadata.author)}</span>')

        meta_parts.append(f'<span class="date">{faq.metadata.created_at.strftime("%B %d, %Y")}</span>')
        meta_parts.append(f'<span class="count">{len(faq.items)} questions</span>')

        lines.append(f'    <div class="faq-metadata">{" • ".join(meta_parts)}</div>')
        lines.append("  </header>")

        return "\n".join(lines)

    def _format_introduction(self, intro: str) -> str:
        """Format introduction section."""
        return f"""  <section class="faq-introduction">
    <h2>Introduction</h2>
    <p>{html.escape(intro)}</p>
  </section>"""

    def _format_items(self, faq: FAQ) -> str:
        """Format all FAQ items."""
        sections = []
        sections.append('  <section class="faq-items">')

        # Group by category
        categorized = self._group_by_category(faq)

        # Uncategorized items
        if None in categorized:
            for item in categorized[None]:
                sections.append(self._format_single_item(item))

        # Categorized items
        for category in sorted(categorized.keys()):
            if category is None:
                continue

            sections.append(f'    <div class="faq-category">')
            sections.append(f"      <h2>{html.escape(category)}</h2>")

            for item in categorized[category]:
                sections.append(self._format_single_item(item, indent=6))

            sections.append("    </div>")

        sections.append("  </section>")
        return "\n".join(sections)

    def _format_single_item(self, item, indent: int = 4) -> str:
        """Format a single FAQ item with Schema.org markup."""
        ind = " " * indent

        if self._include_schema:
            lines = [
                f'{ind}<div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">',
                f'{ind}  <h3 class="faq-question" itemprop="name">{html.escape(item.question)}</h3>',
                f'{ind}  <div class="faq-answer" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">',
                f'{ind}    <div itemprop="text">',
                f'{ind}      {html.escape(item.answer)}',
                f'{ind}    </div>',
                f'{ind}  </div>',
            ]
        else:
            lines = [
                f'{ind}<div class="faq-item">',
                f'{ind}  <h3 class="faq-question">{html.escape(item.question)}</h3>',
                f'{ind}  <div class="faq-answer">',
                f'{ind}    <p>{html.escape(item.answer)}</p>',
                f'{ind}  </div>',
            ]

        # Add tags if present
        if item.tags:
            tags_html = " ".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in item.tags)
            lines.append(f'{ind}  <div class="faq-tags">{tags_html}</div>')

        lines.append(f'{ind}</div>')
        return "\n".join(lines)

    def _format_conclusion(self, conclusion: str) -> str:
        """Format conclusion section."""
        return f"""  <section class="faq-conclusion">
    <h2>Additional Resources</h2>
    <p>{html.escape(conclusion)}</p>
  </section>"""

    def _format_footer(self, faq: FAQ) -> str:
        """Format footer."""
        return f"""  <footer class="faq-footer">
    <p>Generated with <strong>blog-AI</strong> • {faq.word_count()} words</p>
  </footer>"""

    def _group_by_category(self, faq: FAQ) -> dict:
        """Group FAQ items by category."""
        categorized = defaultdict(list)
        for item in faq.items:
            categorized[item.category].append(item)
        return dict(categorized)

    def _get_styles(self) -> str:
        """Get embedded CSS styles."""
        return """  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      line-height: 1.6;
      max-width: 900px;
      margin: 0 auto;
      padding: 2rem;
      color: #333;
    }

    .faq-header {
      border-bottom: 3px solid #0066cc;
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
    }

    .faq-header h1 {
      margin: 0 0 0.5rem 0;
      color: #0066cc;
    }

    .faq-description {
      font-size: 1.1rem;
      color: #666;
      margin: 0.5rem 0;
    }

    .faq-metadata {
      color: #888;
      font-size: 0.9rem;
      margin-top: 0.5rem;
    }

    .faq-introduction, .faq-conclusion {
      background: #f5f5f5;
      padding: 1.5rem;
      border-radius: 8px;
      margin: 2rem 0;
    }

    .faq-category {
      margin: 3rem 0;
    }

    .faq-category h2 {
      color: #0066cc;
      border-bottom: 2px solid #e0e0e0;
      padding-bottom: 0.5rem;
    }

    .faq-item {
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 1.5rem;
      margin: 1rem 0;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
      transition: box-shadow 0.2s;
    }

    .faq-item:hover {
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .faq-question {
      color: #333;
      margin: 0 0 1rem 0;
      font-size: 1.2rem;
    }

    .faq-answer {
      color: #555;
      line-height: 1.7;
    }

    .faq-tags {
      margin-top: 1rem;
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .tag {
      background: #e8f4f8;
      color: #0066cc;
      padding: 0.25rem 0.75rem;
      border-radius: 12px;
      font-size: 0.85rem;
    }

    .faq-footer {
      text-align: center;
      margin-top: 3rem;
      padding-top: 2rem;
      border-top: 1px solid #e0e0e0;
      color: #888;
      font-size: 0.9rem;
    }

    @media (max-width: 768px) {
      body {
        padding: 1rem;
      }

      .faq-item {
        padding: 1rem;
      }
    }
  </style>"""
