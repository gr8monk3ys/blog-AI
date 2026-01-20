"""
Shared utility functions for handling content metadata.
"""

from typing import Any, Dict


class MetadataError(Exception):
    """Exception raised for errors in metadata operations."""

    pass


def add_markdown_metadata(content: str, metadata: Dict[str, Any]) -> str:
    """
    Add YAML front matter metadata to Markdown content.

    Args:
        content: The Markdown content.
        metadata: The metadata to add (supports strings and lists).

    Returns:
        The Markdown content with YAML front matter.

    Raises:
        MetadataError: If an error occurs during addition.
    """
    try:
        # Create YAML front matter
        front_matter = "---\n"
        for key, value in metadata.items():
            if isinstance(value, list):
                front_matter += f"{key}:\n"
                for item in value:
                    front_matter += f"  - {item}\n"
            else:
                front_matter += f"{key}: {value}\n"
        front_matter += "---\n\n"

        return front_matter + content
    except Exception as e:
        raise MetadataError(f"Error adding Markdown metadata: {str(e)}")


def extract_markdown_metadata(content: str) -> tuple[Dict[str, Any], str]:
    """
    Extract YAML front matter metadata from Markdown content.

    Args:
        content: The Markdown content with front matter.

    Returns:
        A tuple of (metadata dict, content without front matter).

    Raises:
        MetadataError: If an error occurs during extraction.
    """
    try:
        if not content.startswith("---"):
            return {}, content

        # Find the end of front matter
        end_index = content.find("---", 3)
        if end_index == -1:
            return {}, content

        # Extract front matter
        front_matter = content[3:end_index].strip()
        remaining_content = content[end_index + 3:].strip()

        # Parse YAML front matter (simple key: value parsing)
        metadata = {}
        current_key = None
        current_list = None

        for line in front_matter.split("\n"):
            line = line.rstrip()
            if not line:
                continue

            # Check for list item
            if line.startswith("  - "):
                if current_key and current_list is not None:
                    current_list.append(line[4:])
            # Check for new key
            elif ":" in line:
                # Save previous list if exists
                if current_key and current_list is not None:
                    metadata[current_key] = current_list

                key, value = line.split(":", 1)
                current_key = key.strip()
                value = value.strip()

                if value:
                    metadata[current_key] = value
                    current_list = None
                else:
                    # Start a new list
                    current_list = []

        # Save final list if exists
        if current_key and current_list is not None:
            metadata[current_key] = current_list

        return metadata, remaining_content
    except Exception as e:
        raise MetadataError(f"Error extracting Markdown metadata: {str(e)}")
