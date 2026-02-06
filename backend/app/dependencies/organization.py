"""
FastAPI dependencies for organization context and authorization.

This module provides:
- Organization context extraction from requests
- Role-based authorization dependencies
- Permission checking dependencies

Usage:
    @router.get("/items")
    async def list_items(
        auth_ctx: AuthorizationContext = Depends(get_organization_context),
    ):
        auth_ctx.require_permission(Permission.CONTENT_VIEW)
        # ...

    @router.post("/items")
    async def create_item(
        _: None = Depends(require_permission(Permission.CONTENT_CREATE)),
    ):
        # Permission already checked
        # ...
"""

import logging
from functools import lru_cache
from typing import Callable, List, Optional

from fastapi import Depends, Header, HTTPException, Path, Request, status

from app.auth import verify_api_key
from src.organizations import (
    AuthorizationContext,
    NotOrganizationMemberError,
    OrganizationNotFoundError,
    Permission,
    PermissionDeniedError,
    get_organization_service,
    log_authorization_failure,
)
from src.types.organization import OrganizationRole

logger = logging.getLogger(__name__)


# =============================================================================
# Request Context Extraction
# =============================================================================


async def get_request_context(request: Request) -> dict:
    """
    Extract request context for audit logging.

    Args:
        request: The FastAPI request object.

    Returns:
        Dictionary with IP address, user agent, and request ID.
    """
    # Get client IP (handle proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (client IP)
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    return {
        "ip_address": ip_address,
        "user_agent": request.headers.get("User-Agent"),
        "request_id": request.headers.get("X-Request-ID"),
    }


# =============================================================================
# Organization Context Dependencies
# =============================================================================


async def get_organization_id_from_header(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> Optional[str]:
    """
    Extract organization ID from request header.

    Args:
        x_organization_id: The X-Organization-ID header value.

    Returns:
        The organization ID or None.
    """
    return x_organization_id


async def get_organization_id_from_path(
    organization_id: str = Path(..., description="Organization ID"),
) -> str:
    """
    Extract organization ID from URL path.

    Args:
        organization_id: The organization_id path parameter.

    Returns:
        The organization ID.
    """
    return organization_id


async def get_current_organization(
    organization_id: str = Depends(get_organization_id_from_path),
    user_id: str = Depends(verify_api_key),
):
    """
    Get the current organization and verify membership.

    Args:
        organization_id: The organization ID from path.
        user_id: The authenticated user ID.

    Returns:
        The organization.

    Raises:
        HTTPException: If organization not found or user not a member.
    """
    try:
        org_service = get_organization_service()
        org = await org_service.get_organization(organization_id)

        # Verify membership
        member = await org_service.get_member(organization_id, user_id)
        if not member:
            raise NotOrganizationMemberError(organization_id)

        return org

    except OrganizationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Organization not found"},
        )
    except NotOrganizationMemberError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You are not a member of this organization",
            },
        )


async def get_organization_context(
    organization_id: str = Depends(get_organization_id_from_path),
    user_id: str = Depends(verify_api_key),
) -> AuthorizationContext:
    """
    Get authorization context for the current request.

    This dependency fetches the user's role in the organization and
    creates an AuthorizationContext for permission checking.

    Args:
        organization_id: The organization ID from path.
        user_id: The authenticated user ID.

    Returns:
        AuthorizationContext with user's permissions.

    Raises:
        HTTPException: If organization not found or user not a member.
    """
    try:
        org_service = get_organization_service()

        # Verify organization exists
        await org_service.get_organization(organization_id)

        # Get user's role in organization
        role = await org_service.get_member_role(organization_id, user_id)

        if role is None:
            raise NotOrganizationMemberError(organization_id)

        return AuthorizationContext(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            is_org_member=True,
        )

    except OrganizationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Organization not found"},
        )
    except NotOrganizationMemberError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You are not a member of this organization",
            },
        )


async def get_optional_organization_context(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    user_id: str = Depends(verify_api_key),
) -> AuthorizationContext:
    """
    Get authorization context with optional organization.

    Use this for endpoints that work with or without an organization context.

    Args:
        x_organization_id: Optional organization ID from header.
        user_id: The authenticated user ID.

    Returns:
        AuthorizationContext (with or without organization).
    """
    if not x_organization_id:
        return AuthorizationContext(
            user_id=user_id,
            organization_id=None,
            role=None,
            is_org_member=False,
        )

    try:
        org_service = get_organization_service()

        # Verify organization exists
        await org_service.get_organization(x_organization_id)

        # Get user's role in organization
        role = await org_service.get_member_role(x_organization_id, user_id)

        return AuthorizationContext(
            user_id=user_id,
            organization_id=x_organization_id,
            role=role,
            is_org_member=role is not None,
        )

    except OrganizationNotFoundError:
        # Organization not found - treat as no organization context
        logger.warning(f"Organization not found: {x_organization_id}")
        return AuthorizationContext(
            user_id=user_id,
            organization_id=None,
            role=None,
            is_org_member=False,
        )


# =============================================================================
# Role-Based Authorization Dependencies
# =============================================================================


def require_role(
    minimum_role: OrganizationRole,
) -> Callable:
    """
    Create a dependency that requires a minimum role.

    Args:
        minimum_role: The minimum role required.

    Returns:
        A FastAPI dependency function.

    Usage:
        @router.delete("/item")
        async def delete_item(
            _: None = Depends(require_role(OrganizationRole.ADMIN)),
        ):
            # Only admins and owners can reach here
            pass
    """
    from src.organizations.rbac import ROLE_LEVELS

    required_level = ROLE_LEVELS[minimum_role]

    async def dependency(
        auth_ctx: AuthorizationContext = Depends(get_organization_context),
    ) -> AuthorizationContext:
        if auth_ctx.role is None:
            log_authorization_failure(
                user_id=auth_ctx.user_id,
                organization_id=auth_ctx.organization_id,
                required_permission=Permission.ORGANIZATION_VIEW,
                user_role=None,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": "Not a member of this organization",
                },
            )

        user_level = ROLE_LEVELS.get(auth_ctx.role, 0)
        if user_level < required_level:
            log_authorization_failure(
                user_id=auth_ctx.user_id,
                organization_id=auth_ctx.organization_id,
                required_permission=Permission.ORGANIZATION_VIEW,
                user_role=auth_ctx.role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": f"This action requires the {minimum_role.value} role or higher",
                    "required_role": minimum_role.value,
                    "your_role": auth_ctx.role.value,
                },
            )

        return auth_ctx

    return dependency


def require_permission(
    permission: Permission,
) -> Callable:
    """
    Create a dependency that requires a specific permission.

    Args:
        permission: The required permission.

    Returns:
        A FastAPI dependency function.

    Usage:
        @router.post("/content")
        async def create_content(
            auth_ctx: AuthorizationContext = Depends(
                require_permission(Permission.CONTENT_CREATE)
            ),
        ):
            # User has CONTENT_CREATE permission
            pass
    """
    async def dependency(
        auth_ctx: AuthorizationContext = Depends(get_organization_context),
    ) -> AuthorizationContext:
        if not auth_ctx.has_permission(permission):
            log_authorization_failure(
                user_id=auth_ctx.user_id,
                organization_id=auth_ctx.organization_id,
                required_permission=permission,
                user_role=auth_ctx.role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": f"Permission denied: {permission.value}",
                    "required_permission": permission.value,
                },
            )

        return auth_ctx

    return dependency


def require_any_permission(
    permissions: List[Permission],
) -> Callable:
    """
    Create a dependency that requires any of the specified permissions.

    Args:
        permissions: List of permissions where at least one is required.

    Returns:
        A FastAPI dependency function.

    Usage:
        @router.put("/content/{id}")
        async def update_content(
            auth_ctx: AuthorizationContext = Depends(
                require_any_permission([
                    Permission.CONTENT_EDIT,
                    Permission.CONTENT_EDIT_ANY,
                ])
            ),
        ):
            # User has at least one of the permissions
            pass
    """
    async def dependency(
        auth_ctx: AuthorizationContext = Depends(get_organization_context),
    ) -> AuthorizationContext:
        if not auth_ctx.has_any_permission(permissions):
            log_authorization_failure(
                user_id=auth_ctx.user_id,
                organization_id=auth_ctx.organization_id,
                required_permission=permissions[0],
                user_role=auth_ctx.role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": "Permission denied",
                    "required_permissions": [p.value for p in permissions],
                },
            )

        return auth_ctx

    return dependency


def require_all_permissions(
    permissions: List[Permission],
) -> Callable:
    """
    Create a dependency that requires all of the specified permissions.

    Args:
        permissions: List of permissions that must all be present.

    Returns:
        A FastAPI dependency function.

    Usage:
        @router.delete("/organization")
        async def delete_organization(
            auth_ctx: AuthorizationContext = Depends(
                require_all_permissions([
                    Permission.ORGANIZATION_DELETE,
                    Permission.BILLING_MANAGE,
                ])
            ),
        ):
            # User has all required permissions
            pass
    """
    async def dependency(
        auth_ctx: AuthorizationContext = Depends(get_organization_context),
    ) -> AuthorizationContext:
        if not auth_ctx.has_all_permissions(permissions):
            missing = [p for p in permissions if not auth_ctx.has_permission(p)]
            log_authorization_failure(
                user_id=auth_ctx.user_id,
                organization_id=auth_ctx.organization_id,
                required_permission=missing[0] if missing else permissions[0],
                user_role=auth_ctx.role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": "Missing required permissions",
                    "missing_permissions": [p.value for p in missing],
                },
            )

        return auth_ctx

    return dependency


# =============================================================================
# Ownership Verification
# =============================================================================


async def require_owner(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> AuthorizationContext:
    """
    Require the user to be the organization owner.

    Args:
        auth_ctx: The authorization context.

    Returns:
        The authorization context if user is owner.

    Raises:
        HTTPException: If user is not the owner.
    """
    if auth_ctx.role != OrganizationRole.OWNER:
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.ORGANIZATION_DELETE,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "Only the organization owner can perform this action",
            },
        )

    return auth_ctx


# =============================================================================
# Resource Ownership
# =============================================================================


def require_resource_owner_or_permission(
    permission: Permission,
    get_owner_id: Callable,
) -> Callable:
    """
    Create a dependency that requires either resource ownership or a permission.

    This is useful for "edit own content" vs "edit any content" scenarios.

    Args:
        permission: The permission that bypasses ownership check.
        get_owner_id: Async function to get the resource owner's user ID.

    Returns:
        A FastAPI dependency function.

    Usage:
        async def get_content_owner(content_id: str) -> str:
            content = await get_content(content_id)
            return content.created_by

        @router.put("/content/{content_id}")
        async def update_content(
            content_id: str,
            auth_ctx: AuthorizationContext = Depends(
                require_resource_owner_or_permission(
                    Permission.CONTENT_EDIT_ANY,
                    get_content_owner,
                )
            ),
        ):
            pass
    """
    async def dependency(
        auth_ctx: AuthorizationContext = Depends(get_organization_context),
        request: Request = None,
    ) -> AuthorizationContext:
        # If user has the bypass permission, allow immediately
        if auth_ctx.has_permission(permission):
            return auth_ctx

        # Otherwise, check resource ownership
        try:
            owner_id = await get_owner_id(request)
            if owner_id == auth_ctx.user_id:
                return auth_ctx
        except Exception as e:
            logger.error(f"Error checking resource ownership: {e}")

        # Neither owner nor has permission
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=permission,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You can only modify your own resources, or need the appropriate permission",
            },
        )

    return dependency
