"""MDX formatter for blog posts."""

import json
import logging

from ...exceptions import FormattingError
from ...models import BlogPost
from .base import Formatter

logger = logging.getLogger(__name__)


class MDXFormatter(Formatter[BlogPost]):
    """
    Formats blog posts as MDX (Markdown + JSX).

    MDX is commonly used in modern static site generators
    like Next.js, Gatsby, and Astro.
    """

    def format(self, content: BlogPost, **kwargs) -> str:
        """
        Format blog post as MDX with frontmatter.

        Args:
            content: BlogPost to format
            **kwargs: Additional options

        Returns:
            MDX-formatted string

        Raises:
            FormattingError: If formatting fails
        """
        try:
            logger.debug(f"Formatting blog post: {content.metadata.title}")

            # Create MDX content
            mdx_parts = []

            # Add frontmatter header
            mdx_parts.append(self._create_frontmatter(content))

            # Add sections
            for section in content.sections:
                # Section heading
                mdx_parts.append(f"## {section.title}\n")

                # Subtopic content
                for subtopic in section.subtopics:
                    if subtopic.content:
                        mdx_parts.append(f"{subtopic.content}\n")

            return "\n".join(mdx_parts)

        except Exception as e:
            raise FormattingError(
                f"Failed to format blog post as MDX: {e}",
                details={"title": content.metadata.title},
            ) from e

    def _create_frontmatter(self, blog_post: BlogPost) -> str:
        """
        Create MDX frontmatter with metadata.

        Args:
            blog_post: BlogPost with metadata

        Returns:
            Formatted frontmatter string
        """
        meta = blog_post.metadata

        frontmatter = f"""import {{ BlogLayout }} from "@/components/BlogLayout";

export const meta = {{
  date: "{meta.date}",
  title: "{meta.title}",
  description:
    "{meta.description}",
  image:
    "{meta.image}",
  tags: {json.dumps(meta.tags)},
}};

export default (props) => <BlogLayout meta={{meta}} {{...props}} />;

"""
        return frontmatter

    @property
    def output_extension(self) -> str:
        """Get file extension."""
        return ".mdx"

    @property
    def content_type(self) -> str:
        """Get MIME type."""
        return "text/markdown"
