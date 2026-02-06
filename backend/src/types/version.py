"""
Pydantic models for content version history.

This module defines the data models for:
- Content version records and metadata
- Version comparison results
- Version restoration operations
- Version statistics
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """
    Type of change that created a version.

    - MANUAL: User explicitly saved a new version
    - AUTO: Automatically created on significant edit
    - RESTORE: Created by restoring a previous version
    - INITIAL: First version of content
    """
    MANUAL = "manual"
    AUTO = "auto"
    RESTORE = "restore"
    INITIAL = "initial"


class ContentVersion(BaseModel):
    """
    A single version of content.

    Represents a snapshot of content at a specific point in time,
    with metadata about the change.
    """

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this version (UUID)"
    )
    content_id: str = Field(
        ...,
        description="ID of the parent content"
    )
    version_number: int = Field(
        ...,
        ge=1,
        description="Sequential version number starting from 1"
    )
    content: str = Field(
        ...,
        description="Full content text at this version"
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 hash of content for change detection"
    )
    diff_from_previous: Optional[str] = Field(
        default=None,
        description="Unified diff from previous version (NULL for first version)"
    )
    change_type: ChangeType = Field(
        default=ChangeType.MANUAL,
        description="Type of change that created this version"
    )
    change_summary: Optional[str] = Field(
        default=None,
        description="Optional human-readable description of changes"
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Word count at this version"
    )
    character_count: int = Field(
        default=0,
        ge=0,
        description="Character count at this version"
    )
    created_by: Optional[str] = Field(
        default=None,
        description="User ID who created this version"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="When this version was created"
    )
    is_current: bool = Field(
        default=False,
        description="Whether this is the current active version"
    )


class ContentVersionSummary(BaseModel):
    """
    Summary of a version for list views.

    Contains preview and metadata without full content.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this version"
    )
    version_number: int = Field(
        ...,
        description="Sequential version number"
    )
    content_preview: str = Field(
        ...,
        description="First 200 characters of content"
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 hash of content"
    )
    change_type: ChangeType = Field(
        ...,
        description="Type of change"
    )
    change_summary: Optional[str] = Field(
        default=None,
        description="Description of changes"
    )
    word_count: int = Field(
        default=0,
        description="Word count"
    )
    character_count: int = Field(
        default=0,
        description="Character count"
    )
    created_by: Optional[str] = Field(
        default=None,
        description="User who created this version"
    )
    created_at: datetime = Field(
        ...,
        description="When this version was created"
    )
    is_current: bool = Field(
        default=False,
        description="Whether this is the current version"
    )


class VersionListResponse(BaseModel):
    """Response containing a list of version summaries."""

    success: bool = Field(default=True)
    content_id: str = Field(
        ...,
        description="ID of the content"
    )
    total_versions: int = Field(
        ...,
        description="Total number of versions"
    )
    current_version: int = Field(
        ...,
        description="Current active version number"
    )
    versions: List[ContentVersionSummary] = Field(
        default_factory=list,
        description="List of version summaries"
    )
    has_more: bool = Field(
        default=False,
        description="Whether more versions are available"
    )


class VersionDetailResponse(BaseModel):
    """Response containing full version details."""

    success: bool = Field(default=True)
    version: ContentVersion = Field(
        ...,
        description="The version details"
    )


class VersionComparison(BaseModel):
    """
    Comparison between two versions.

    Contains both versions' content and metadata for comparison.
    """

    version_1: ContentVersion = Field(
        ...,
        description="First version in comparison"
    )
    version_2: ContentVersion = Field(
        ...,
        description="Second version in comparison"
    )
    word_count_diff: int = Field(
        default=0,
        description="Difference in word count (v2 - v1)"
    )
    character_count_diff: int = Field(
        default=0,
        description="Difference in character count (v2 - v1)"
    )
    unified_diff: Optional[str] = Field(
        default=None,
        description="Unified diff between versions"
    )
    additions: int = Field(
        default=0,
        ge=0,
        description="Number of lines added"
    )
    deletions: int = Field(
        default=0,
        ge=0,
        description="Number of lines deleted"
    )


class VersionCompareResponse(BaseModel):
    """Response containing version comparison."""

    success: bool = Field(default=True)
    content_id: str = Field(
        ...,
        description="ID of the content"
    )
    comparison: VersionComparison = Field(
        ...,
        description="The comparison result"
    )


class CreateVersionRequest(BaseModel):
    """Request to create a new version."""

    content: str = Field(
        ...,
        min_length=1,
        description="The new content text"
    )
    change_summary: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description of changes"
    )
    change_type: ChangeType = Field(
        default=ChangeType.MANUAL,
        description="Type of change"
    )


class CreateVersionResponse(BaseModel):
    """Response after creating a version."""

    success: bool = Field(default=True)
    version_id: str = Field(
        ...,
        description="ID of the new version"
    )
    version_number: int = Field(
        ...,
        description="Version number assigned"
    )
    content_hash: str = Field(
        ...,
        description="Hash of the content"
    )
    is_duplicate: bool = Field(
        default=False,
        description="Whether this was a duplicate (no changes)"
    )
    message: str = Field(
        default="Version created successfully",
        description="Human-readable status message"
    )


class RestoreVersionRequest(BaseModel):
    """Request to restore a previous version."""

    version_number: int = Field(
        ...,
        ge=1,
        description="Version number to restore"
    )


class RestoreVersionResponse(BaseModel):
    """Response after restoring a version."""

    success: bool = Field(default=True)
    new_version_id: str = Field(
        ...,
        description="ID of the newly created version"
    )
    new_version_number: int = Field(
        ...,
        description="Version number of the restored content"
    )
    restored_from_version: int = Field(
        ...,
        description="Version number that was restored"
    )
    message: str = Field(
        ...,
        description="Human-readable status message"
    )


class VersionStatistics(BaseModel):
    """
    Statistics about version history for content.

    Provides insights into editing patterns and history.
    """

    content_id: str = Field(
        ...,
        description="ID of the content"
    )
    total_versions: int = Field(
        default=0,
        description="Total number of versions"
    )
    current_version: int = Field(
        default=1,
        description="Current active version number"
    )
    first_created_at: Optional[datetime] = Field(
        default=None,
        description="When the first version was created"
    )
    last_updated_at: Optional[datetime] = Field(
        default=None,
        description="When the last version was created"
    )
    total_word_change: int = Field(
        default=0,
        description="Total words changed across all versions"
    )
    avg_word_count: float = Field(
        default=0.0,
        description="Average word count across versions"
    )
    manual_saves: int = Field(
        default=0,
        description="Number of manual saves"
    )
    auto_saves: int = Field(
        default=0,
        description="Number of auto-saves"
    )
    restores: int = Field(
        default=0,
        description="Number of version restores"
    )


class VersionStatsResponse(BaseModel):
    """Response containing version statistics."""

    success: bool = Field(default=True)
    statistics: VersionStatistics = Field(
        ...,
        description="Version statistics"
    )


class AutoVersionConfig(BaseModel):
    """
    Configuration for automatic versioning.

    Defines thresholds for when auto-versioning triggers.
    """

    enabled: bool = Field(
        default=True,
        description="Whether auto-versioning is enabled"
    )
    min_word_change: int = Field(
        default=10,
        ge=1,
        description="Minimum word change to trigger auto-version"
    )
    min_char_change: int = Field(
        default=50,
        ge=1,
        description="Minimum character change to trigger auto-version"
    )
    min_time_between_versions: int = Field(
        default=60,
        ge=0,
        description="Minimum seconds between auto-versions"
    )
    max_versions_per_hour: int = Field(
        default=10,
        ge=1,
        description="Maximum auto-versions allowed per hour"
    )


# Default auto-version configuration
DEFAULT_AUTO_VERSION_CONFIG = AutoVersionConfig(
    enabled=True,
    min_word_change=10,
    min_char_change=50,
    min_time_between_versions=60,
    max_versions_per_hour=10,
)
