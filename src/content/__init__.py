"""
Content management module.

Provides services for managing generated content including:
- Version history tracking
- Content snapshots and restoration
- Change detection and diff generation
"""

from .version_service import (
    ContentVersionService,
    get_version_service,
)

__all__ = [
    "ContentVersionService",
    "get_version_service",
]
