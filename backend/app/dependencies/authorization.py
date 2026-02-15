"""
Enhanced authorization dependencies for content and resource operations.

This module extends the organization-based authorization with:
- Organization-scoped content access checks
- User-owned resource verification
- Composite authorization for multi-tenant scenarios
- Rate limit enforcement by organization tier

Security Notes:
- All authorization checks fail-closed (deny by default)
- Failed authorization attempts are logged for security monitoring
- Organization context is required for all org-scoped operations

Usage:
    from app.dependencies.authorization import (
        require_content_creation,
        require_content_access,
        require_org_scoped_api_key,
        get_organization_quota_context,
    )

    @router.post("/content")
    async def create_content(
        auth_ctx: AuthorizationContext = Depends(require_content_creation),
    ):
        # User has content.create permission in their organization
        pass
"""

import logging
from functools import lru_cache
from typing import Callable, List, Optional, Tuple

from fastapi import Depends, Header, HTTPException, Path, Request, status

from app.auth import verify_api_key
from app.dependencies.organization import (
    get_optional_organization_context,
    get_organization_context,
    get_request_context,
)
from src.organizations import (
    AuthorizationContext,
    NotOrganizationMemberError,
    OrganizationNotFoundError,
    Permission,
    PermissionDeniedError,
    get_organization_service,
    log_authorization_failure,
)
from src.types.organization import OrganizationPlanTier, OrganizationRole

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================


# Default permissions required for common operations
CONTENT_READ_PERMISSIONS = [Permission.CONTENT_VIEW]
CONTENT_WRITE_PERMISSIONS = [Permission.CONTENT_CREATE]
CONTENT_EDIT_PERMISSIONS = [Permission.CONTENT_EDIT, Permission.CONTENT_EDIT_ANY]
CONTENT_DELETE_PERMISSIONS = [Permission.CONTENT_DELETE, Permission.CONTENT_DELETE_ANY]
CONTENT_PUBLISH_PERMISSIONS = [Permission.CONTENT_PUBLISH]

# Knowledge base permissions
KNOWLEDGE_READ_PERMISSIONS = [Permission.CONTENT_VIEW]
KNOWLEDGE_WRITE_PERMISSIONS = [Permission.CONTENT_CREATE]

# Brand profile permissions
BRAND_READ_PERMISSIONS = [Permission.BRAND_VIEW]
BRAND_WRITE_PERMISSIONS = [Permission.BRAND_MANAGE]


# =============================================================================
# Organization-Scoped API Key Authentication
# =============================================================================


class OrganizationAuthContext:
    """
    Extended authorization context with organization details.

    Includes organization tier and quota information for rate limiting
    and feature gating.
    """

    def __init__(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        role: Optional[OrganizationRole] = None,
        is_org_member: bool = False,
        plan_tier: Optional[OrganizationPlanTier] = None,
        monthly_limit: int = 0,
        current_usage: int = 0,
    ):
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role
        self.is_org_member = is_org_member
        self.plan_tier = plan_tier
        self.monthly_limit = monthly_limit
        self.current_usage = current_usage
        self._auth_context: Optional[AuthorizationContext] = None

    @property
    def auth_context(self) -> AuthorizationContext:
        """Get the base authorization context."""
        if self._auth_context is None:
            self._auth_context = AuthorizationContext(
                user_id=self.user_id,
                organization_id=self.organization_id,
                role=self.role,
                is_org_member=self.is_org_member,
            )
        return self._auth_context

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return self.auth_context.has_permission(permission)

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return self.auth_context.has_any_permission(permissions)

    @property
    def remaining_quota(self) -> int:
        """Get remaining quota for the billing period."""
        if self.monthly_limit == -1:  # Unlimited
            return float('inf')
        return max(0, self.monthly_limit - self.current_usage)

    @property
    def has_quota(self) -> bool:
        """Check if user has remaining quota."""
        return self.remaining_quota > 0


async def require_org_scoped_api_key(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    user_id: str = Depends(verify_api_key),
) -> OrganizationAuthContext:
    """
    Authenticate API key and optionally resolve organization context.

    This dependency:
    1. Validates the API key (authentication)
    2. If X-Organization-ID header is provided:
       - Verifies user is a member of that organization
       - Loads their role and permissions
       - Loads organization quota information

    Args:
        x_organization_id: Optional organization ID from header.
        user_id: The authenticated user ID from API key.

    Returns:
        OrganizationAuthContext with user and optional org details.

    Raises:
        HTTPException: If organization specified but user is not a member.
    """
    if not x_organization_id:
        # No organization context - user-level access only
        return OrganizationAuthContext(
            user_id=user_id,
            organization_id=None,
            role=None,
            is_org_member=False,
        )

    try:
        org_service = get_organization_service()

        # Get organization and verify it exists
        org = await org_service.get_organization(x_organization_id)

        # Get user's role in organization
        role = await org_service.get_member_role(x_organization_id, user_id)

        if role is None:
            # User is not a member of this organization
            logger.warning(
                f"User {user_id[:8]}... attempted to access org {x_organization_id} "
                "without membership"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": "You are not a member of this organization",
                    "error_code": "NOT_ORG_MEMBER",
                },
            )

        return OrganizationAuthContext(
            user_id=user_id,
            organization_id=x_organization_id,
            role=role,
            is_org_member=True,
            plan_tier=org.plan_tier,
            monthly_limit=org.monthly_generation_limit,
            current_usage=org.current_month_usage,
        )

    except OrganizationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Organization not found",
                "error_code": "ORG_NOT_FOUND",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving organization context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to verify organization access",
            },
        )


# =============================================================================
# Content Authorization Dependencies
# =============================================================================


async def require_content_creation(
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
) -> AuthorizationContext:
    """
    Require permission to create content in the organization.

    Args:
        auth_ctx: The authorization context from organization dependency.

    Returns:
        The authorization context if permitted.

    Raises:
        HTTPException: If user lacks content.create permission.
    """
    if not auth_ctx.organization_id:
        return auth_ctx

    if not auth_ctx.has_permission(Permission.CONTENT_CREATE):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.CONTENT_CREATE,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You do not have permission to create content in this organization",
                "required_permission": Permission.CONTENT_CREATE.value,
                "your_role": auth_ctx.role.value if auth_ctx.role else None,
            },
        )
    return auth_ctx


async def require_content_access(
    auth_ctx: AuthorizationContext = Depends(get_optional_organization_context),
) -> AuthorizationContext:
    """
    Require permission to view content in the organization.

    Args:
        auth_ctx: The authorization context from organization dependency.

    Returns:
        The authorization context if permitted.

    Raises:
        HTTPException: If user lacks content.view permission.
    """
    if not auth_ctx.organization_id:
        return auth_ctx

    if not auth_ctx.has_permission(Permission.CONTENT_VIEW):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.CONTENT_VIEW,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You do not have permission to view content in this organization",
                "required_permission": Permission.CONTENT_VIEW.value,
            },
        )
    return auth_ctx


def require_content_edit(
    content_owner_id_param: str = "content_owner_id",
) -> Callable:
    """
    Create a dependency that requires permission to edit content.

    Users can edit their own content with CONTENT_EDIT permission,
    or any content with CONTENT_EDIT_ANY permission.

    Args:
        content_owner_id_param: Request parameter containing content owner ID.

    Returns:
        A FastAPI dependency function.

    Usage:
        @router.put("/content/{content_id}")
        async def update_content(
            content_id: str,
            content_owner_id: str,  # Resolved from content lookup
            auth_ctx: AuthorizationContext = Depends(require_content_edit()),
        ):
            pass
    """

    async def dependency(
        request: Request,
        auth_ctx: AuthorizationContext = Depends(get_organization_context),
    ) -> AuthorizationContext:
        # Check for CONTENT_EDIT_ANY (can edit any content)
        if auth_ctx.has_permission(Permission.CONTENT_EDIT_ANY):
            return auth_ctx

        # Check for CONTENT_EDIT (own content only)
        if auth_ctx.has_permission(Permission.CONTENT_EDIT):
            # Need to verify ownership - get from request state or path
            content_owner_id = getattr(request.state, content_owner_id_param, None)

            if content_owner_id is None:
                # Try to get from query params or body
                # This is a limitation - caller needs to set request.state
                logger.warning(
                    f"Content owner ID not found in request state for "
                    f"user {auth_ctx.user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": "Cannot verify content ownership",
                    },
                )

            if content_owner_id == auth_ctx.user_id:
                return auth_ctx

        # No permission to edit
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.CONTENT_EDIT,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You can only edit your own content",
                "required_permissions": [
                    Permission.CONTENT_EDIT.value,
                    Permission.CONTENT_EDIT_ANY.value,
                ],
            },
        )

    return dependency


async def require_content_publish(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> AuthorizationContext:
    """
    Require permission to publish content.

    Args:
        auth_ctx: The authorization context from organization dependency.

    Returns:
        The authorization context if permitted.

    Raises:
        HTTPException: If user lacks content.publish permission.
    """
    if not auth_ctx.has_permission(Permission.CONTENT_PUBLISH):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.CONTENT_PUBLISH,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You do not have permission to publish content",
                "required_permission": Permission.CONTENT_PUBLISH.value,
            },
        )
    return auth_ctx


# =============================================================================
# Knowledge Base Authorization Dependencies
# =============================================================================


async def require_knowledge_read(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> AuthorizationContext:
    """
    Require permission to read from the knowledge base.

    Uses content.view permission as knowledge base access is tied to content.

    Args:
        auth_ctx: The authorization context.

    Returns:
        The authorization context if permitted.
    """
    if not auth_ctx.has_permission(Permission.CONTENT_VIEW):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.CONTENT_VIEW,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You do not have permission to access the knowledge base",
            },
        )
    return auth_ctx


async def require_knowledge_write(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> AuthorizationContext:
    """
    Require permission to write to the knowledge base (upload documents).

    Uses content.create permission.

    Args:
        auth_ctx: The authorization context.

    Returns:
        The authorization context if permitted.
    """
    if not auth_ctx.has_permission(Permission.CONTENT_CREATE):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.CONTENT_CREATE,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You do not have permission to upload documents",
            },
        )
    return auth_ctx


# =============================================================================
# Brand Profile Authorization Dependencies
# =============================================================================


async def require_brand_read(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> AuthorizationContext:
    """
    Require permission to view brand profiles.

    Args:
        auth_ctx: The authorization context.

    Returns:
        The authorization context if permitted.
    """
    if not auth_ctx.has_permission(Permission.BRAND_VIEW):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.BRAND_VIEW,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You do not have permission to view brand profiles",
            },
        )
    return auth_ctx


async def require_brand_write(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> AuthorizationContext:
    """
    Require permission to manage brand profiles.

    Args:
        auth_ctx: The authorization context.

    Returns:
        The authorization context if permitted.
    """
    if not auth_ctx.has_permission(Permission.BRAND_MANAGE):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.BRAND_MANAGE,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "You do not have permission to manage brand profiles",
            },
        )
    return auth_ctx


# =============================================================================
# Quota and Rate Limit Authorization
# =============================================================================


async def get_organization_quota_context(
    org_auth: OrganizationAuthContext = Depends(require_org_scoped_api_key),
) -> OrganizationAuthContext:
    """
    Get organization auth context with quota verification.

    Verifies that the organization has remaining quota before allowing
    the operation to proceed.

    Args:
        org_auth: The organization auth context.

    Returns:
        The organization auth context if quota available.

    Raises:
        HTTPException: If organization quota is exhausted.
    """
    if org_auth.organization_id and not org_auth.has_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": "Organization quota exceeded",
                "error_code": "QUOTA_EXCEEDED",
                "current_usage": org_auth.current_usage,
                "monthly_limit": org_auth.monthly_limit,
            },
        )
    return org_auth


async def require_content_generation_quota(
    org_auth: OrganizationAuthContext = Depends(get_organization_quota_context),
) -> OrganizationAuthContext:
    """
    Require both content creation permission AND available quota.

    This is the primary dependency for content generation endpoints.

    Args:
        org_auth: The organization auth context with quota.

    Returns:
        The organization auth context if permitted and quota available.

    Raises:
        HTTPException: If lacking permission or quota.
    """
    # If in an organization context, verify content creation permission
    if org_auth.is_org_member:
        if not org_auth.has_permission(Permission.CONTENT_CREATE):
            log_authorization_failure(
                user_id=org_auth.user_id,
                organization_id=org_auth.organization_id,
                required_permission=Permission.CONTENT_CREATE,
                user_role=org_auth.role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": "You do not have permission to generate content in this organization",
                    "required_permission": Permission.CONTENT_CREATE.value,
                },
            )

    return org_auth


# =============================================================================
# Feature Flag Authorization
# =============================================================================


def require_feature(feature_name: str) -> Callable:
    """
    Create a dependency that requires a specific feature to be enabled.

    Features are controlled at the organization level based on plan tier.

    Args:
        feature_name: The feature flag name to check.

    Returns:
        A FastAPI dependency function.

    Usage:
        @router.post("/advanced-analysis")
        async def advanced_analysis(
            _: None = Depends(require_feature("advanced_analytics")),
        ):
            pass
    """

    async def dependency(
        org_auth: OrganizationAuthContext = Depends(require_org_scoped_api_key),
    ) -> OrganizationAuthContext:
        # Define features by plan tier
        feature_requirements = {
            "advanced_analytics": [
                OrganizationPlanTier.PRO,
                OrganizationPlanTier.BUSINESS,
                OrganizationPlanTier.ENTERPRISE,
            ],
            "sso": [
                OrganizationPlanTier.BUSINESS,
                OrganizationPlanTier.ENTERPRISE,
            ],
            "custom_templates": [
                OrganizationPlanTier.PRO,
                OrganizationPlanTier.BUSINESS,
                OrganizationPlanTier.ENTERPRISE,
            ],
            "api_webhooks": [
                OrganizationPlanTier.STARTER,
                OrganizationPlanTier.PRO,
                OrganizationPlanTier.BUSINESS,
                OrganizationPlanTier.ENTERPRISE,
            ],
            "white_label": [
                OrganizationPlanTier.ENTERPRISE,
            ],
        }

        # If no organization context, feature check fails
        if not org_auth.organization_id or not org_auth.plan_tier:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": f"Feature '{feature_name}' requires an organization context",
                    "error_code": "FEATURE_REQUIRES_ORG",
                },
            )

        allowed_tiers = feature_requirements.get(feature_name, [])

        if org_auth.plan_tier not in allowed_tiers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": f"Feature '{feature_name}' is not available on your plan",
                    "error_code": "FEATURE_NOT_AVAILABLE",
                    "current_plan": org_auth.plan_tier.value,
                    "required_plans": [t.value for t in allowed_tiers],
                },
            )

        return org_auth

    return dependency


# =============================================================================
# Admin-Only Operations
# =============================================================================


async def require_admin(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> AuthorizationContext:
    """
    Require admin or owner role in the organization.

    Args:
        auth_ctx: The authorization context.

    Returns:
        The authorization context if user is admin or owner.

    Raises:
        HTTPException: If user is not admin or owner.
    """
    if auth_ctx.role not in (OrganizationRole.ADMIN, OrganizationRole.OWNER):
        log_authorization_failure(
            user_id=auth_ctx.user_id,
            organization_id=auth_ctx.organization_id,
            required_permission=Permission.MEMBERS_MANAGE,
            user_role=auth_ctx.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "This action requires admin privileges",
                "your_role": auth_ctx.role.value if auth_ctx.role else None,
            },
        )
    return auth_ctx


# =============================================================================
# Audit Logging Helpers
# =============================================================================


async def log_authorized_action(
    auth_ctx: AuthorizationContext,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Log a successful authorization for audit purposes.

    Args:
        auth_ctx: The authorization context.
        action: The action being performed.
        resource_type: Type of resource being accessed.
        resource_id: Optional ID of the specific resource.
        metadata: Optional additional metadata.
    """
    logger.info(
        "Authorization granted",
        extra={
            "user_id": auth_ctx.user_id[:8] + "..." if len(auth_ctx.user_id) > 8 else auth_ctx.user_id,
            "organization_id": auth_ctx.organization_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_role": auth_ctx.role.value if auth_ctx.role else None,
            "security_event": "authorization_granted",
            **(metadata or {}),
        }
    )
