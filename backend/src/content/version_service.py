"""
Content Version Service.

Provides version history management for generated content with support for:
- Creating and retrieving versions
- Comparing versions with diff generation
- Restoring previous versions
- Auto-versioning on significant changes

Supports both Supabase (production) and in-memory (development) storage.
"""

import difflib
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from src.types.version import (
    AutoVersionConfig,
    ChangeType,
    ContentVersion,
    ContentVersionSummary,
    DEFAULT_AUTO_VERSION_CONFIG,
    VersionComparison,
    VersionStatistics,
)

logger = logging.getLogger(__name__)


class BaseVersionService(ABC):
    """Abstract base class for version service implementations."""

    @abstractmethod
    async def create_version(
        self,
        content_id: str,
        content: str,
        change_type: ChangeType = ChangeType.MANUAL,
        change_summary: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Tuple[str, int, str, bool]:
        """
        Create a new version for content.

        Args:
            content_id: ID of the content to version.
            content: The new content text.
            change_type: Type of change (manual, auto, restore, initial).
            change_summary: Optional description of the change.
            created_by: User ID who created the version.

        Returns:
            Tuple of (version_id, version_number, content_hash, is_duplicate).
        """
        pass

    @abstractmethod
    async def get_versions(
        self,
        content_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ContentVersionSummary], int]:
        """
        Get version history for content.

        Args:
            content_id: ID of the content.
            limit: Maximum number of versions to return.
            offset: Number of versions to skip.

        Returns:
            Tuple of (list of version summaries, total count).
        """
        pass

    @abstractmethod
    async def get_version(
        self,
        content_id: str,
        version_number: int,
    ) -> Optional[ContentVersion]:
        """
        Get a specific version of content.

        Args:
            content_id: ID of the content.
            version_number: Version number to retrieve.

        Returns:
            ContentVersion if found, None otherwise.
        """
        pass

    @abstractmethod
    async def restore_version(
        self,
        content_id: str,
        version_number: int,
        restored_by: Optional[str] = None,
    ) -> Tuple[bool, str, int, int, str]:
        """
        Restore content to a previous version.

        Creates a new version with the restored content.

        Args:
            content_id: ID of the content.
            version_number: Version number to restore.
            restored_by: User ID who performed the restore.

        Returns:
            Tuple of (success, new_version_id, new_version_number, restored_from, message).
        """
        pass

    @abstractmethod
    async def compare_versions(
        self,
        content_id: str,
        version_1: int,
        version_2: int,
    ) -> Optional[VersionComparison]:
        """
        Compare two versions of content.

        Args:
            content_id: ID of the content.
            version_1: First version number.
            version_2: Second version number.

        Returns:
            VersionComparison if both versions exist, None otherwise.
        """
        pass

    @abstractmethod
    async def get_statistics(
        self,
        content_id: str,
    ) -> Optional[VersionStatistics]:
        """
        Get version statistics for content.

        Args:
            content_id: ID of the content.

        Returns:
            VersionStatistics if content exists, None otherwise.
        """
        pass

    @abstractmethod
    async def should_auto_version(
        self,
        content_id: str,
        new_content: str,
        config: Optional[AutoVersionConfig] = None,
    ) -> bool:
        """
        Check if auto-versioning should trigger.

        Args:
            content_id: ID of the content.
            new_content: The new content to check.
            config: Auto-version configuration.

        Returns:
            True if auto-version should be created.
        """
        pass

    @abstractmethod
    async def is_content_in_organization(
        self,
        content_id: str,
        organization_id: Optional[str],
    ) -> bool:
        """
        Verify content belongs to the provided organization.

        Args:
            content_id: ID of the content.
            organization_id: Organization ID to validate against.

        Returns:
            True if content belongs to organization, False otherwise.
        """
        pass

    @abstractmethod
    async def register_content_organization(
        self,
        content_id: str,
        organization_id: Optional[str],
    ) -> bool:
        """
        Register ownership for content when no persistent store exists.

        Args:
            content_id: ID of the content.
            organization_id: Organization ID to associate.

        Returns:
            True if registered or already matches, False on conflict or failure.
        """
        pass


def calculate_content_hash(content: str) -> str:
    """Calculate SHA-256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def calculate_word_count(content: str) -> int:
    """Calculate word count of content."""
    return len(content.split())


def generate_unified_diff(
    content_1: str,
    content_2: str,
    from_version: int,
    to_version: int,
) -> Tuple[str, int, int]:
    """
    Generate unified diff between two content versions.

    Args:
        content_1: First content.
        content_2: Second content.
        from_version: Version number of first content.
        to_version: Version number of second content.

    Returns:
        Tuple of (unified_diff, additions, deletions).
    """
    lines_1 = content_1.splitlines(keepends=True)
    lines_2 = content_2.splitlines(keepends=True)

    diff = difflib.unified_diff(
        lines_1,
        lines_2,
        fromfile=f"version_{from_version}",
        tofile=f"version_{to_version}",
        lineterm="",
    )

    diff_lines = list(diff)
    additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    return "".join(diff_lines), additions, deletions


class InMemoryVersionService(BaseVersionService):
    """In-memory version service for development and testing."""

    def __init__(self) -> None:
        self._versions: Dict[str, List[ContentVersion]] = {}
        self._current_versions: Dict[str, int] = {}
        self._last_auto_version: Dict[str, datetime] = {}
        self._auto_version_counts: Dict[str, List[datetime]] = {}
        self._content_organizations: Dict[str, str] = {}
        logger.info("Initialized in-memory version service")

    async def create_version(
        self,
        content_id: str,
        content: str,
        change_type: ChangeType = ChangeType.MANUAL,
        change_summary: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Tuple[str, int, str, bool]:
        """Create a new version."""
        content_hash = calculate_content_hash(content)

        # Check for duplicate
        if content_id in self._versions and self._versions[content_id]:
            latest = self._versions[content_id][-1]
            if latest.content_hash == content_hash:
                return (
                    latest.id or "",
                    latest.version_number,
                    content_hash,
                    True,
                )

        # Initialize if first version
        if content_id not in self._versions:
            self._versions[content_id] = []
            self._current_versions[content_id] = 0

        # Get previous version for diff
        diff_from_previous = None
        if self._versions[content_id]:
            prev_version = self._versions[content_id][-1]
            diff_from_previous, _, _ = generate_unified_diff(
                prev_version.content,
                content,
                prev_version.version_number,
                prev_version.version_number + 1,
            )

        # Create new version
        version_number = len(self._versions[content_id]) + 1
        version_id = f"ver_{content_id}_{version_number}"

        version = ContentVersion(
            id=version_id,
            content_id=content_id,
            version_number=version_number,
            content=content,
            content_hash=content_hash,
            diff_from_previous=diff_from_previous,
            change_type=change_type,
            change_summary=change_summary,
            word_count=calculate_word_count(content),
            character_count=len(content),
            created_by=created_by,
            created_at=datetime.utcnow(),
            is_current=True,
        )

        # Mark previous versions as not current
        for v in self._versions[content_id]:
            v.is_current = False

        self._versions[content_id].append(version)
        self._current_versions[content_id] = version_number

        logger.info(
            f"Created version {version_number} for content {content_id} "
            f"(type: {change_type.value})"
        )

        return version_id, version_number, content_hash, False

    async def get_versions(
        self,
        content_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ContentVersionSummary], int]:
        """Get version history."""
        if content_id not in self._versions:
            return [], 0

        versions = self._versions[content_id]
        total = len(versions)

        # Get paginated and reversed (newest first)
        paginated = list(reversed(versions))[offset : offset + limit]

        summaries = [
            ContentVersionSummary(
                id=v.id or "",
                version_number=v.version_number,
                content_preview=v.content[:200],
                content_hash=v.content_hash,
                change_type=v.change_type,
                change_summary=v.change_summary,
                word_count=v.word_count,
                character_count=v.character_count,
                created_by=v.created_by,
                created_at=v.created_at or datetime.utcnow(),
                is_current=v.is_current,
            )
            for v in paginated
        ]

        return summaries, total

    async def get_version(
        self,
        content_id: str,
        version_number: int,
    ) -> Optional[ContentVersion]:
        """Get a specific version."""
        if content_id not in self._versions:
            return None

        for version in self._versions[content_id]:
            if version.version_number == version_number:
                return version

        return None

    async def restore_version(
        self,
        content_id: str,
        version_number: int,
        restored_by: Optional[str] = None,
    ) -> Tuple[bool, str, int, int, str]:
        """Restore a previous version."""
        version = await self.get_version(content_id, version_number)
        if not version:
            return (
                False,
                "",
                0,
                version_number,
                f"Version {version_number} not found",
            )

        # Create new version with restored content
        version_id, new_version_number, _, _ = await self.create_version(
            content_id=content_id,
            content=version.content,
            change_type=ChangeType.RESTORE,
            change_summary=f"Restored from version {version_number}",
            created_by=restored_by,
        )

        return (
            True,
            version_id,
            new_version_number,
            version_number,
            f"Successfully restored to version {version_number} (new version: {new_version_number})",
        )

    async def compare_versions(
        self,
        content_id: str,
        version_1: int,
        version_2: int,
    ) -> Optional[VersionComparison]:
        """Compare two versions."""
        v1 = await self.get_version(content_id, version_1)
        v2 = await self.get_version(content_id, version_2)

        if not v1 or not v2:
            return None

        unified_diff, additions, deletions = generate_unified_diff(
            v1.content,
            v2.content,
            v1.version_number,
            v2.version_number,
        )

        return VersionComparison(
            version_1=v1,
            version_2=v2,
            word_count_diff=v2.word_count - v1.word_count,
            character_count_diff=v2.character_count - v1.character_count,
            unified_diff=unified_diff,
            additions=additions,
            deletions=deletions,
        )

    async def get_statistics(
        self,
        content_id: str,
    ) -> Optional[VersionStatistics]:
        """Get version statistics."""
        if content_id not in self._versions or not self._versions[content_id]:
            return None

        versions = self._versions[content_id]

        total_word_change = 0
        prev_word_count = 0
        for v in versions:
            total_word_change += abs(v.word_count - prev_word_count)
            prev_word_count = v.word_count

        return VersionStatistics(
            content_id=content_id,
            total_versions=len(versions),
            current_version=self._current_versions.get(content_id, 1),
            first_created_at=versions[0].created_at,
            last_updated_at=versions[-1].created_at,
            total_word_change=total_word_change,
            avg_word_count=sum(v.word_count for v in versions) / len(versions),
            manual_saves=sum(1 for v in versions if v.change_type == ChangeType.MANUAL),
            auto_saves=sum(1 for v in versions if v.change_type == ChangeType.AUTO),
            restores=sum(1 for v in versions if v.change_type == ChangeType.RESTORE),
        )

    async def should_auto_version(
        self,
        content_id: str,
        new_content: str,
        config: Optional[AutoVersionConfig] = None,
    ) -> bool:
        """Check if auto-versioning should trigger."""
        if config is None:
            config = DEFAULT_AUTO_VERSION_CONFIG

        if not config.enabled:
            return False

        # Check time since last auto-version
        if content_id in self._last_auto_version:
            time_since = datetime.utcnow() - self._last_auto_version[content_id]
            if time_since.total_seconds() < config.min_time_between_versions:
                return False

        # Check hourly rate limit
        if content_id in self._auto_version_counts:
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent = [t for t in self._auto_version_counts[content_id] if t > hour_ago]
            if len(recent) >= config.max_versions_per_hour:
                return False

        # Check for significant changes
        if content_id not in self._versions or not self._versions[content_id]:
            return True

        latest = self._versions[content_id][-1]
        new_word_count = calculate_word_count(new_content)
        new_char_count = len(new_content)

        word_diff = abs(new_word_count - latest.word_count)
        char_diff = abs(new_char_count - latest.character_count)

        return word_diff >= config.min_word_change or char_diff >= config.min_char_change

    async def is_content_in_organization(
        self,
        content_id: str,
        organization_id: Optional[str],
    ) -> bool:
        """
        In-memory storage has no organization mapping.

        We allow access in dev/test modes and rely on higher-level authorization.
        """
        if not organization_id:
            logger.warning(
                "Organization ID missing for content ownership check "
                f"(content_id={content_id})."
            )
            return False

        mapped_org = self._content_organizations.get(content_id)
        if mapped_org is None:
            return False

        return mapped_org == organization_id

    async def register_content_organization(
        self,
        content_id: str,
        organization_id: Optional[str],
    ) -> bool:
        if not organization_id:
            return False

        existing = self._content_organizations.get(content_id)
        if existing and existing != organization_id:
            logger.warning(
                "Content ownership conflict for in-memory store "
                f"(content_id={content_id}, existing_org={existing}, requested_org={organization_id})."
            )
            return False

        if existing == organization_id:
            return True

        self._content_organizations[content_id] = organization_id
        return True


class SupabaseVersionService(BaseVersionService):
    """Supabase-backed version service for production."""

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key
        self._client = None
        logger.info("Initialized Supabase version service")

    def _get_client(self):
        """Get or create Supabase client."""
        if self._client is not None:
            return self._client

        try:
            from supabase import create_client

            self._client = create_client(self._supabase_url, self._supabase_key)
            return self._client
        except ImportError:
            logger.error("Supabase Python client not installed. Run: pip install supabase")
            raise RuntimeError("Supabase client not available")
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise

    async def create_version(
        self,
        content_id: str,
        content: str,
        change_type: ChangeType = ChangeType.MANUAL,
        change_summary: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Tuple[str, int, str, bool]:
        """Create a new version using database function."""
        try:
            client = self._get_client()

            # Generate diff from previous version
            diff_from_previous = None
            result = (
                client.table("content_versions")
                .select("content, version_number")
                .eq("content_id", content_id)
                .order("version_number", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                prev = result.data[0]
                diff_from_previous, _, _ = generate_unified_diff(
                    prev["content"],
                    content,
                    prev["version_number"],
                    prev["version_number"] + 1,
                )

            # Call the database function
            result = client.rpc(
                "create_content_version",
                {
                    "p_content_id": content_id,
                    "p_content": content,
                    "p_change_type": change_type.value,
                    "p_change_summary": change_summary,
                    "p_created_by": created_by,
                    "p_diff_from_previous": diff_from_previous,
                },
            ).execute()

            if not result.data:
                raise RuntimeError("Failed to create version")

            row = result.data[0]
            return (
                str(row["version_id"]),
                row["version_number"],
                row["content_hash"],
                row["is_duplicate"],
            )

        except Exception as e:
            logger.error(f"Error creating version: {e}")
            raise

    async def get_versions(
        self,
        content_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ContentVersionSummary], int]:
        """Get version history using database function."""
        try:
            client = self._get_client()

            # Get total count
            count_result = (
                client.table("content_versions")
                .select("id", count="exact")
                .eq("content_id", content_id)
                .execute()
            )
            total = count_result.count or 0

            # Get versions using the function
            result = client.rpc(
                "get_content_versions",
                {
                    "p_content_id": content_id,
                    "p_limit": limit,
                    "p_offset": offset,
                },
            ).execute()

            if not result.data:
                return [], total

            summaries = [
                ContentVersionSummary(
                    id=str(row["version_id"]),
                    version_number=row["version_number"],
                    content_preview=row["content_preview"],
                    content_hash=row["content_hash"],
                    change_type=ChangeType(row["change_type"]),
                    change_summary=row["change_summary"],
                    word_count=row["word_count"],
                    character_count=row["character_count"],
                    created_by=row["created_by"],
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    is_current=row["is_current"],
                )
                for row in result.data
            ]

            return summaries, total

        except Exception as e:
            logger.error(f"Error getting versions: {e}")
            raise

    async def get_version(
        self,
        content_id: str,
        version_number: int,
    ) -> Optional[ContentVersion]:
        """Get a specific version using database function."""
        try:
            client = self._get_client()

            result = client.rpc(
                "get_content_version",
                {
                    "p_content_id": content_id,
                    "p_version_number": version_number,
                },
            ).execute()

            if not result.data:
                return None

            row = result.data[0]
            return ContentVersion(
                id=str(row["version_id"]),
                content_id=content_id,
                version_number=row["version_number"],
                content=row["content"],
                content_hash=row["content_hash"],
                diff_from_previous=row["diff_from_previous"],
                change_type=ChangeType(row["change_type"]),
                change_summary=row["change_summary"],
                word_count=row["word_count"],
                character_count=row["character_count"],
                created_by=row["created_by"],
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                is_current=row["is_current"],
            )

        except Exception as e:
            logger.error(f"Error getting version: {e}")
            raise

    async def restore_version(
        self,
        content_id: str,
        version_number: int,
        restored_by: Optional[str] = None,
    ) -> Tuple[bool, str, int, int, str]:
        """Restore a previous version using database function."""
        try:
            client = self._get_client()

            result = client.rpc(
                "restore_content_version",
                {
                    "p_content_id": content_id,
                    "p_version_number": version_number,
                    "p_restored_by": restored_by,
                },
            ).execute()

            if not result.data:
                return (
                    False,
                    "",
                    0,
                    version_number,
                    "Failed to restore version",
                )

            row = result.data[0]
            return (
                row["success"],
                str(row["new_version_id"]) if row["new_version_id"] else "",
                row["new_version_number"] or 0,
                row["restored_from_version"],
                row["message"],
            )

        except Exception as e:
            logger.error(f"Error restoring version: {e}")
            raise

    async def compare_versions(
        self,
        content_id: str,
        version_1: int,
        version_2: int,
    ) -> Optional[VersionComparison]:
        """Compare two versions using database function."""
        try:
            client = self._get_client()

            result = client.rpc(
                "compare_content_versions",
                {
                    "p_content_id": content_id,
                    "p_version_1": version_1,
                    "p_version_2": version_2,
                },
            ).execute()

            if not result.data:
                return None

            row = result.data[0]

            # Get full versions for comparison object
            v1 = await self.get_version(content_id, version_1)
            v2 = await self.get_version(content_id, version_2)

            if not v1 or not v2:
                return None

            # Generate diff
            unified_diff, additions, deletions = generate_unified_diff(
                row["version_1_content"],
                row["version_2_content"],
                version_1,
                version_2,
            )

            return VersionComparison(
                version_1=v1,
                version_2=v2,
                word_count_diff=row["word_count_diff"],
                character_count_diff=row["char_count_diff"],
                unified_diff=unified_diff,
                additions=additions,
                deletions=deletions,
            )

        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            raise

    async def get_statistics(
        self,
        content_id: str,
    ) -> Optional[VersionStatistics]:
        """Get version statistics using database function."""
        try:
            client = self._get_client()

            result = client.rpc(
                "get_version_statistics",
                {"p_content_id": content_id},
            ).execute()

            if not result.data:
                return None

            row = result.data[0]
            return VersionStatistics(
                content_id=content_id,
                total_versions=row["total_versions"],
                current_version=row["current_version"],
                first_created_at=datetime.fromisoformat(
                    row["first_created_at"].replace("Z", "+00:00")
                ) if row["first_created_at"] else None,
                last_updated_at=datetime.fromisoformat(
                    row["last_updated_at"].replace("Z", "+00:00")
                ) if row["last_updated_at"] else None,
                total_word_change=row["total_word_change"],
                avg_word_count=float(row["avg_word_count"] or 0),
                manual_saves=row["manual_saves"],
                auto_saves=row["auto_saves"],
                restores=row["restores"],
            )

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise

    async def should_auto_version(
        self,
        content_id: str,
        new_content: str,
        config: Optional[AutoVersionConfig] = None,
    ) -> bool:
        """Check if auto-versioning should trigger using database function."""
        if config is None:
            config = DEFAULT_AUTO_VERSION_CONFIG

        if not config.enabled:
            return False

        try:
            client = self._get_client()

            result = client.rpc(
                "has_significant_changes",
                {
                    "p_content_id": content_id,
                    "p_new_content": new_content,
                    "p_min_word_change": config.min_word_change,
                    "p_min_char_change": config.min_char_change,
                },
            ).execute()

            return result.data if result.data else False

        except Exception as e:
            logger.error(f"Error checking auto-version: {e}")
            return False

    async def is_content_in_organization(
        self,
        content_id: str,
        organization_id: Optional[str],
    ) -> bool:
        """Validate content ownership using generated_content table."""
        if not organization_id:
            return False

        try:
            client = self._get_client()
            result = (
                client.table("generated_content")
                .select("organization_id")
                .eq("id", content_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                return False

            row = result.data[0]
            return str(row.get("organization_id")) == str(organization_id)
        except Exception as e:
            logger.error(f"Error verifying content ownership: {e}")
            return False

    async def register_content_organization(
        self,
        content_id: str,
        organization_id: Optional[str],
    ) -> bool:
        """Supabase is authoritative; no-op registration."""
        return False


class ContentVersionService:
    """
    Factory class for content version service.

    Automatically selects between Supabase and in-memory storage based on
    environment configuration.
    """

    _instance: Optional[BaseVersionService] = None

    @classmethod
    def get_service(cls) -> BaseVersionService:
        """
        Get or create the version service instance.

        Uses Supabase if SUPABASE_URL and SUPABASE_KEY are configured,
        otherwise falls back to in-memory storage.
        """
        if cls._instance is not None:
            return cls._instance

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

        if supabase_url and supabase_key:
            try:
                cls._instance = SupabaseVersionService(supabase_url, supabase_key)
                logger.info("Using Supabase storage for content versions")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Supabase version service: {e}. "
                    "Falling back to in-memory."
                )
                cls._instance = InMemoryVersionService()
        else:
            logger.info(
                "Supabase not configured. Using in-memory storage for content versions."
            )
            cls._instance = InMemoryVersionService()

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the service instance. Useful for testing."""
        cls._instance = None


def get_version_service() -> BaseVersionService:
    """Get the content version service instance."""
    return ContentVersionService.get_service()
