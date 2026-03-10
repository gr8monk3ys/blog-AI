"""
Content Version History API endpoints.

Provides endpoints for:
- Listing version history
- Retrieving specific versions
- Creating manual versions
- Restoring previous versions
- Comparing versions
- Version statistics

Authorization:
- All endpoints require organization membership
- All operations require content.view or content.edit permission
- SECURITY: Content ownership is validated before allowing version operations
"""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.content import get_version_service
from src.organizations import AuthorizationContext
from src.types.version import (
    ChangeType,
    CreateVersionRequest,
    CreateVersionResponse,
    RestoreVersionResponse,
    VersionCompareResponse,
    VersionDetailResponse,
    VersionListResponse,
    VersionStatsResponse,
)

from ..auth import verify_api_key
from ..dependencies import require_content_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["versions"])


# UUID validation pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_content_id(content_id: str) -> str:
    """Validate content ID format."""
    if not UUID_PATTERN.match(content_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content ID format. Must be a valid UUID.",
        )
    return content_id


def validate_version_number(version: int) -> int:
    """Validate version number."""
    if version < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version number must be a positive integer.",
        )
    return version


async def validate_content_ownership(
    content_id: str,
    auth_ctx: AuthorizationContext,
    allow_register: bool = False,
) -> None:
    """
    SECURITY: Validate that the content belongs to the user's organization.

    This function should verify content ownership before allowing version operations.
    In production, this would query the content table to verify organization_id.
    """
    if not auth_ctx.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required for content access.",
        )

    service = get_version_service()
    is_owned = await service.is_content_in_organization(
        content_id=content_id,
        organization_id=auth_ctx.organization_id,
    )
    if is_owned:
        return

    if allow_register:
        registered = await service.register_content_organization(
            content_id=content_id,
            organization_id=auth_ctx.organization_id,
        )
        if registered:
            return

    # Avoid leaking whether the content exists outside the org
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Content not found.",
    )


@router.get(
    "/{content_id}/versions",
    response_model=VersionListResponse,
    summary="List content versions",
    description="Get paginated version history for a content item.",
)
async def list_versions(
    content_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum versions to return"),
    offset: int = Query(default=0, ge=0, description="Number of versions to skip"),
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> VersionListResponse:
    """
    List version history for content.

    **Authorization:** Requires content.view permission in the organization.

    Args:
        content_id: The content UUID.
        limit: Maximum number of versions to return (1-100).
        offset: Number of versions to skip for pagination.
        auth_ctx: The authorization context with user and org info.

    Returns:
        Paginated list of version summaries.
    """
    validate_content_id(content_id)
    # SECURITY: Validate content ownership before allowing access
    await validate_content_ownership(content_id, auth_ctx)
    logger.info(f"Listing versions for content {content_id} (user: {auth_ctx.user_id[:8]}...)")

    try:
        service = get_version_service()
        versions, total = await service.get_versions(content_id, limit, offset)

        # Determine current version
        current_version = 1
        for v in versions:
            if v.is_current:
                current_version = v.version_number
                break

        return VersionListResponse(
            success=True,
            content_id=content_id,
            total_versions=total,
            current_version=current_version,
            versions=versions,
            has_more=offset + limit < total,
        )

    except Exception as e:
        logger.error(f"Error listing versions for {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve version history.",
        )


@router.get(
    "/{content_id}/versions/{version}",
    response_model=VersionDetailResponse,
    summary="Get specific version",
    description="Retrieve full details of a specific content version.",
)
async def get_version(
    content_id: str,
    version: int,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> VersionDetailResponse:
    """
    Get a specific version of content.

    **Authorization:** Requires content.view permission in the organization.

    Args:
        content_id: The content UUID.
        version: The version number to retrieve.
        auth_ctx: The authorization context with user and org info.

    Returns:
        Full version details including content.
    """
    validate_content_id(content_id)
    validate_version_number(version)
    # SECURITY: Validate content ownership before allowing access
    await validate_content_ownership(content_id, auth_ctx)
    logger.info(f"Getting version {version} for content {content_id}")

    try:
        service = get_version_service()
        content_version = await service.get_version(content_id, version)

        if not content_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found for content {content_id}.",
            )

        return VersionDetailResponse(
            success=True,
            version=content_version,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version {version} for {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve version.",
        )


@router.post(
    "/{content_id}/versions",
    response_model=CreateVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new version",
    description="Manually create a new version of content.",
)
async def create_version(
    content_id: str,
    request: CreateVersionRequest,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> CreateVersionResponse:
    """
    Create a new version of content.

    This is used for manual saves. Auto-versioning happens automatically
    on significant edits.

    **Authorization:** Requires content.edit permission in the organization.

    Args:
        content_id: The content UUID.
        request: The version creation request with new content.
        auth_ctx: The authorization context with user and org info.

    Returns:
        Details of the created version.
    """
    validate_content_id(content_id)
    # SECURITY: Validate content ownership before allowing modification
    await validate_content_ownership(content_id, auth_ctx, allow_register=True)
    logger.info(f"Creating version for content {content_id} (user: {auth_ctx.user_id[:8]}...)")

    try:
        service = get_version_service()
        version_id, version_number, content_hash, is_duplicate = await service.create_version(
            content_id=content_id,
            content=request.content,
            change_type=request.change_type,
            change_summary=request.change_summary,
            created_by=auth_ctx.user_id,
        )

        if is_duplicate:
            return CreateVersionResponse(
                success=True,
                version_id=version_id,
                version_number=version_number,
                content_hash=content_hash,
                is_duplicate=True,
                message="Content unchanged. No new version created.",
            )

        return CreateVersionResponse(
            success=True,
            version_id=version_id,
            version_number=version_number,
            content_hash=content_hash,
            is_duplicate=False,
            message=f"Version {version_number} created successfully.",
        )

    except Exception as e:
        logger.error(f"Error creating version for {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create version.",
        )


@router.post(
    "/{content_id}/versions/{version}/restore",
    response_model=RestoreVersionResponse,
    summary="Restore version",
    description="Restore content to a previous version by creating a new version.",
)
async def restore_version(
    content_id: str,
    version: int,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> RestoreVersionResponse:
    """
    Restore content to a previous version.

    This creates a new version with the content from the specified version,
    preserving full version history.

    **Authorization:** Requires content.edit permission in the organization.

    Args:
        content_id: The content UUID.
        version: The version number to restore.
        auth_ctx: The authorization context with user and org info.

    Returns:
        Details of the restoration including new version number.
    """
    validate_content_id(content_id)
    validate_version_number(version)
    # SECURITY: Validate content ownership before allowing restore
    await validate_content_ownership(content_id, auth_ctx)
    logger.info(f"Restoring version {version} for content {content_id}")

    try:
        service = get_version_service()
        success, new_version_id, new_version_number, restored_from, message = (
            await service.restore_version(
                content_id=content_id,
                version_number=version,
                restored_by=auth_ctx.user_id,
            )
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        return RestoreVersionResponse(
            success=True,
            new_version_id=new_version_id,
            new_version_number=new_version_number,
            restored_from_version=restored_from,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring version {version} for {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore version.",
        )


@router.get(
    "/{content_id}/versions/compare",
    response_model=VersionCompareResponse,
    summary="Compare versions",
    description="Compare two versions of content with diff generation.",
)
async def compare_versions(
    content_id: str,
    v1: int = Query(..., ge=1, description="First version number"),
    v2: int = Query(..., ge=1, description="Second version number"),
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> VersionCompareResponse:
    """
    Compare two versions of content.

    Returns both versions with a unified diff showing the changes.

    **Authorization:** Requires content.view permission in the organization.

    Args:
        content_id: The content UUID.
        v1: First version number.
        v2: Second version number.
        auth_ctx: The authorization context with user and org info.

    Returns:
        Comparison result with diff and statistics.
    """
    validate_content_id(content_id)
    validate_version_number(v1)
    validate_version_number(v2)
    # SECURITY: Validate content ownership before allowing comparison
    await validate_content_ownership(content_id, auth_ctx)

    if v1 == v2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a version with itself.",
        )

    logger.info(f"Comparing versions {v1} and {v2} for content {content_id}")

    try:
        service = get_version_service()
        comparison = await service.compare_versions(content_id, v1, v2)

        if not comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"One or both versions not found for content {content_id}.",
            )

        return VersionCompareResponse(
            success=True,
            content_id=content_id,
            comparison=comparison,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing versions {v1} and {v2} for {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare versions.",
        )


@router.get(
    "/{content_id}/versions/stats",
    response_model=VersionStatsResponse,
    summary="Get version statistics",
    description="Get statistics about version history for content.",
)
async def get_version_statistics(
    content_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> VersionStatsResponse:
    """
    Get version statistics for content.

    Returns aggregate statistics about the version history including
    total versions, change patterns, and editing metrics.

    **Authorization:** Requires content.view permission in the organization.

    Args:
        content_id: The content UUID.
        auth_ctx: The authorization context with user and org info.

    Returns:
        Version statistics.
    """
    validate_content_id(content_id)
    # SECURITY: Validate content ownership before allowing access
    await validate_content_ownership(content_id, auth_ctx)
    logger.info(f"Getting version stats for content {content_id}")

    try:
        service = get_version_service()
        stats = await service.get_statistics(content_id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No version history found for content {content_id}.",
            )

        return VersionStatsResponse(
            success=True,
            statistics=stats,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version stats for {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve version statistics.",
        )


@router.post(
    "/{content_id}/versions/auto",
    response_model=CreateVersionResponse,
    summary="Auto-save version",
    description="Trigger auto-save if content has significant changes.",
)
async def auto_save_version(
    content_id: str,
    request: CreateVersionRequest,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> CreateVersionResponse:
    """
    Auto-save a new version if changes are significant.

    This endpoint checks if the new content has significant changes
    compared to the current version before creating a new version.

    **Authorization:** Requires content.edit permission in the organization.

    Args:
        content_id: The content UUID.
        request: The version creation request with new content.
        auth_ctx: The authorization context with user and org info.

    Returns:
        Details of the created version or indication that no version was needed.
    """
    validate_content_id(content_id)
    # SECURITY: Validate content ownership before allowing auto-save
    await validate_content_ownership(content_id, auth_ctx, allow_register=True)
    logger.info(f"Auto-save check for content {content_id}")

    try:
        service = get_version_service()

        # Check if auto-versioning should trigger
        should_version = await service.should_auto_version(content_id, request.content)

        if not should_version:
            # Get current version info
            versions, _ = await service.get_versions(content_id, limit=1)
            if versions:
                return CreateVersionResponse(
                    success=True,
                    version_id=versions[0].id,
                    version_number=versions[0].version_number,
                    content_hash=versions[0].content_hash,
                    is_duplicate=True,
                    message="No significant changes. Auto-save skipped.",
                )
            # Fall through to create first version

        # Create auto-save version
        version_id, version_number, content_hash, is_duplicate = await service.create_version(
            content_id=content_id,
            content=request.content,
            change_type=ChangeType.AUTO,
            change_summary=request.change_summary or "Auto-saved",
            created_by=auth_ctx.user_id,
        )

        if is_duplicate:
            return CreateVersionResponse(
                success=True,
                version_id=version_id,
                version_number=version_number,
                content_hash=content_hash,
                is_duplicate=True,
                message="Content unchanged. Auto-save skipped.",
            )

        return CreateVersionResponse(
            success=True,
            version_id=version_id,
            version_number=version_number,
            content_hash=content_hash,
            is_duplicate=False,
            message=f"Auto-saved as version {version_number}.",
        )

    except Exception as e:
        logger.error(f"Error auto-saving for {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to auto-save version.",
        )
