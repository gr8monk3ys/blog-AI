"""Markdown formatter for FAQ documents.

Formats FAQ documents as clean Markdown with proper structure,
suitable for documentation sites, GitHub, etc.
"""

import logging
from collections import defaultdict

from ...models.faq import FAQ
from .base import Formatter

logger = logging.getLogger(__name__)


class FAQMarkdownFormatter(Formatter[FAQ]):
    """
    Format FAQ documents as Markdown.

    Creates clean, structured Markdown with:
    - Title and description
    - Optional introduction
    - Questions organized by category
    - Table of contents
    - Optional conclusion

    Example:
        >>> formatter = FAQMarkdownFormatter()
        >>> content = formatter.format(faq)
        >>> with open("faq.md", "w") as f:
        ...     f.write(content)
    """

    def __init__(
        self,
        include_toc: bool = True,
        include_metadata: bool = True,
        heading_level: int = 1,
    ):
        """
        Initialize Markdown formatter.

        Args:
            include_toc: Include table of contents (default: True)
            include_metadata: Include metadata section (default: True)
            heading_level: Starting heading level (1-6, default: 1)
        """
        self._include_toc = include_toc
        self._include_metadata = include_metadata
        self._heading_level = max(1, min(6, heading_level))

    def format(self, content: FAQ) -> str:
        """
        Format FAQ as Markdown.

        Args:
            content: FAQ document to format

        Returns:
            Formatted Markdown string
        """
        logger.debug(f"Formatting FAQ as Markdown: {content.metadata.title}")

        sections = []

        # Title
        sections.append(self._format_title(content))

        # Description
        if content.metadata.description:
            sections.append(content.metadata.description)
            sections.append("")

        # Metadata
        if self._include_metadata:
            sections.append(self._format_metadata(content))

        # Introduction
        if content.introduction:
            sections.append(self._format_introduction(content.introduction))

        # Table of Contents
        if self._include_toc:
            sections.append(self._format_toc(content))

        # FAQ Items (organized by category)
        sections.append(self._format_items(content))

        # Conclusion
        if content.conclusion:
            sections.append(self._format_conclusion(content.conclusion))

        # Footer
        sections.append(self._format_footer(content))

        return "\n\n".join(sections)

    def _format_title(self, faq: FAQ) -> str:
        """Format title with appropriate heading level."""
        hashes = "#" * self._heading_level
        return f"{hashes} {faq.metadata.title}"

    def _format_metadata(self, faq: FAQ) -> str:
        """Format metadata section."""
        lines = []
        lines.append("---")
        lines.append("")
        lines.append(f"**Topic:** {faq.metadata.topic}")

        if faq.metadata.author:
            lines.append(f"**Author:** {faq.metadata.author}")

        lines.append(f"**Questions:** {len(faq.items)}")
        lines.append(f"**Last Updated:** {faq.metadata.created_at.strftime('%Y-%m-%d')}")

        if faq.metadata.categories:
            categories = ", ".join(faq.metadata.categories)
            lines.append(f"**Categories:** {categories}")

        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def _format_introduction(self, intro: str) -> str:
        """Format introduction section."""
        hashes = "#" * (self._heading_level + 1)
        return f"{hashes} Introduction\n\n{intro}"

    def _format_toc(self, faq: FAQ) -> str:
        """Format table of contents."""
        hashes = "#" * (self._heading_level + 1)
        lines = [f"{hashes} Table of Contents", ""]

        # Group by category
        categorized = self._group_by_category(faq)

        if None in categorized:
            # Uncategorized items
            for i, item in enumerate(categorized[None], 1):
                link = self._create_anchor_link(item.question)
                lines.append(f"{i}. [{item.question}](#{link})")

        for category in sorted(categorized.keys()):
            if category is None:
                continue

            lines.append(f"\n**{category}:**")
            for item in categorized[category]:
                link = self._create_anchor_link(item.question)
                lines.append(f"- [{item.question}](#{link})")

        return "\n".join(lines)

    def _format_items(self, faq: FAQ) -> str:
        """Format all FAQ items, organized by category."""
        hashes_section = "#" * (self._heading_level + 1)
        hashes_item = "#" * (self._heading_level + 2)

        sections = []

        # Group by category
        categorized = self._group_by_category(faq)

        # Handle uncategorized items first
        if None in categorized:
            sections.append(f"{hashes_section} Questions\n")
            for item in categorized[None]:
                sections.append(self._format_single_item(item, hashes_item))

        # Handle categorized items
        for category in sorted(categorized.keys()):
            if category is None:
                continue

            sections.append(f"{hashes_section} {category}\n")
            for item in categorized[category]:
                sections.append(self._format_single_item(item, hashes_item))

        return "\n".join(sections)

    def _format_single_item(self, item, heading: str) -> str:
        """Format a single FAQ item."""
        lines = [
            f"{heading} {item.question}",
            "",
            item.answer,
            "",
        ]

        # Add tags if present
        if item.tags:
            tags = " ".join(f"`{tag}`" for tag in item.tags)
            lines.append(f"*Tags: {tags}*")
            lines.append("")

        return "\n".join(lines)

    def _format_conclusion(self, conclusion: str) -> str:
        """Format conclusion section."""
        hashes = "#" * (self._heading_level + 1)
        return f"{hashes} Additional Resources\n\n{conclusion}"

    def _format_footer(self, faq: FAQ) -> str:
        """Format footer with generation info."""
        return f"---\n\n*Generated with blog-AI • {faq.word_count()} words*"

    def _group_by_category(self, faq: FAQ) -> dict:
        """Group FAQ items by category."""
        categorized = defaultdict(list)
        for item in faq.items:
            categorized[item.category].append(item)
        return dict(categorized)

    def _create_anchor_link(self, text: str) -> str:
        """Create markdown anchor link from text."""
        import re

        # Convert to lowercase
        link = text.lower()
        # Remove special characters except spaces and hyphens
        link = re.sub(r"[^\w\s-]", "", link)
        # Replace spaces with hyphens
        link = re.sub(r"[-\s]+", "-", link)
        return link.strip("-")
