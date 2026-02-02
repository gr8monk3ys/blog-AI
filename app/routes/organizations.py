"""
Organization management API endpoints.

This module provides REST endpoints for:
- Organization CRUD operations
- Member management
- Invitation handling
- Audit log access
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth import verify_api_key
from app.dependencies import (
    get_organization_context,
    get_request_context,
    require_owner,
    require_permission,
    require_role,
)
from src.organizations import (
    AuthorizationContext,
    InviteExistsError,
    InviteNotFoundError,
    MemberExistsError,
    MemberLimitExceededError,
    MemberNotFoundError,
    OrganizationExistsError,
    OrganizationNotFoundError,
    OrganizationServiceError,
    Permission,
    PermissionDeniedError,
    QuotaExceededError,
    get_audit_service,
    get_organization_service,
)
from src.types.organization import (
    AuditLogQuery,
    AuditLogsResponse,
    InviteAcceptRequest,
    InviteAcceptResponse,
    Organization,
    OrganizationCreate,
    OrganizationInvite,
    OrganizationInviteCreate,
    OrganizationInvitesResponse,
    OrganizationMember,
    OrganizationMemberUpdate,
    OrganizationMembersResponse,
    OrganizationQuotaStatus,
    OrganizationResponse,
    OrganizationRole,
    OrganizationsListResponse,
    OrganizationSummary,
    OrganizationUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"])


# =============================================================================
# Error Handlers
# =============================================================================


def handle_organization_error(e: Exception) -> HTTPException:
    """Convert organization errors to HTTP exceptions."""
    if isinstance(e, OrganizationExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "error": str(e), "error_code": "ORG_SLUG_EXISTS"},
        )
    if isinstance(e, MemberExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "error": str(e), "error_code": "MEMBER_EXISTS"},
        )
    if isinstance(e, InviteExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "error": str(e), "error_code": "INVITE_EXISTS"},
        )
    if isinstance(e, (MemberNotFoundError, InviteNotFoundError)):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": str(e)},
        )
    if isinstance(e, OrganizationNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": "Organization not found"},
        )
    if isinstance(e, PermissionDeniedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": str(e)},
        )
    if isinstance(e, MemberLimitExceededError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "MEMBER_LIMIT_EXCEEDED",
                "current": e.current,
                "limit": e.limit,
            },
        )
    if isinstance(e, QuotaExceededError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "QUOTA_EXCEEDED",
                "current": e.current,
                "limit": e.limit,
            },
        )
    if isinstance(e, OrganizationServiceError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": str(e), "error_code": e.code},
        )

    # Unknown error
    logger.exception(f"Unexpected organization error: {e}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"success": False, "error": "An unexpected error occurred"},
    )


# =============================================================================
# Organization CRUD Endpoints
# =============================================================================


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
    description="Create a new organization with the current user as owner.",
)
async def create_organization(
    data: OrganizationCreate,
    request: Request,
    user_id: str = Depends(verify_api_key),
) -> OrganizationResponse:
    """
    Create a new organization.

    The authenticated user becomes the owner of the organization.
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        org = await org_service.create_organization(
            data=data,
            user_id=user_id,
            request_context=request_context,
        )

        logger.info(f"Organization created: {org.slug} by user {user_id[:8]}...")
        return OrganizationResponse(organization=org)

    except Exception as e:
        raise handle_organization_error(e)


@router.get(
    "",
    response_model=OrganizationsListResponse,
    summary="List organizations",
    description="List all organizations the current user is a member of.",
)
async def list_organizations(
    user_id: str = Depends(verify_api_key),
) -> OrganizationsListResponse:
    """
    List organizations for the current user.

    Returns organizations where the user is an active member.
    """
    try:
        org_service = get_organization_service()
        organizations = await org_service.list_user_organizations(user_id)

        return OrganizationsListResponse(
            organizations=organizations,
            total=len(organizations),
        )

    except Exception as e:
        raise handle_organization_error(e)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
    description="Get organization details.",
)
async def get_organization(
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_VIEW)
    ),
) -> OrganizationResponse:
    """
    Get organization details.

    Requires: organization.view permission (all members have this).
    """
    try:
        org_service = get_organization_service()
        org = await org_service.get_organization(auth_ctx.organization_id)

        return OrganizationResponse(organization=org)

    except Exception as e:
        raise handle_organization_error(e)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update organization settings.",
)
async def update_organization(
    data: OrganizationUpdate,
    request: Request,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_UPDATE)
    ),
) -> OrganizationResponse:
    """
    Update organization details.

    Requires: organization.update permission (owner, admin).
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        org = await org_service.update_organization(
            organization_id=auth_ctx.organization_id,
            data=data,
            auth_context=auth_ctx,
            request_context=request_context,
        )

        logger.info(f"Organization updated: {org.slug}")
        return OrganizationResponse(organization=org)

    except Exception as e:
        raise handle_organization_error(e)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete organization",
    description="Delete an organization (soft delete).",
)
async def delete_organization(
    request: Request,
    auth_ctx: AuthorizationContext = Depends(require_owner),
) -> Dict:
    """
    Delete an organization.

    Requires: owner role.

    This performs a soft delete - the organization is marked as inactive
    but data is retained for potential recovery.
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        await org_service.delete_organization(
            organization_id=auth_ctx.organization_id,
            auth_context=auth_ctx,
            request_context=request_context,
        )

        logger.info(f"Organization deleted: {auth_ctx.organization_id}")
        return {"success": True, "message": "Organization deleted"}

    except Exception as e:
        raise handle_organization_error(e)


# =============================================================================
# Member Management Endpoints
# =============================================================================


@router.get(
    "/{organization_id}/members",
    response_model=OrganizationMembersResponse,
    summary="List members",
    description="List all members of the organization.",
)
async def list_members(
    include_inactive: bool = Query(False, description="Include deactivated members"),
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.MEMBERS_VIEW)
    ),
) -> OrganizationMembersResponse:
    """
    List organization members.

    Requires: members.view permission (all members have this).
    """
    try:
        org_service = get_organization_service()
        members = await org_service.list_members(
            organization_id=auth_ctx.organization_id,
            auth_context=auth_ctx,
            include_inactive=include_inactive,
        )

        return OrganizationMembersResponse(
            members=members,
            total=len(members),
        )

    except Exception as e:
        raise handle_organization_error(e)


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationInvite,
    status_code=status.HTTP_201_CREATED,
    summary="Invite member",
    description="Invite a new member to the organization.",
)
async def invite_member(
    data: OrganizationInviteCreate,
    request: Request,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.MEMBERS_INVITE)
    ),
) -> Dict:
    """
    Invite a new member to the organization.

    Requires: members.invite permission (owner, admin).

    The invited user will receive an email with a link to accept the invitation.
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        invite, token = await org_service.create_invite(
            organization_id=auth_ctx.organization_id,
            data=data,
            auth_context=auth_ctx,
            request_context=request_context,
        )

        logger.info(
            f"Invite created for {data.email} to org {auth_ctx.organization_id}"
        )

        # Return invite details along with the token
        # In production, the token would be sent via email instead
        return {
            "success": True,
            "invite": invite.model_dump(),
            "invite_token": token,  # Would be sent via email in production
            "invite_url": f"/organizations/invites/{token}/accept",
        }

    except Exception as e:
        raise handle_organization_error(e)


@router.patch(
    "/{organization_id}/members/{user_id}",
    response_model=OrganizationMember,
    summary="Update member role",
    description="Update a member's role in the organization.",
)
async def update_member_role(
    user_id: str,
    data: OrganizationMemberUpdate,
    request: Request,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.MEMBERS_MANAGE)
    ),
) -> OrganizationMember:
    """
    Update a member's role.

    Requires: members.manage permission (owner, admin).

    Role change restrictions:
    - Owners can change anyone's role except other owners
    - Admins can change editors and viewers
    - Cannot change own role (use transfer ownership instead)
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        member = await org_service.update_member_role(
            organization_id=auth_ctx.organization_id,
            target_user_id=user_id,
            new_role=data.role,
            auth_context=auth_ctx,
            request_context=request_context,
        )

        logger.info(
            f"Member role updated: {user_id} to {data.role.value} "
            f"in org {auth_ctx.organization_id}"
        )
        return member

    except Exception as e:
        raise handle_organization_error(e)


@router.delete(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove member",
    description="Remove a member from the organization.",
)
async def remove_member(
    user_id: str,
    request: Request,
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> Dict:
    """
    Remove a member from the organization.

    Users can remove themselves (leave).
    Requires: members.manage permission to remove others.

    The owner cannot be removed - ownership must be transferred first.
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        await org_service.remove_member(
            organization_id=auth_ctx.organization_id,
            target_user_id=user_id,
            auth_context=auth_ctx,
            request_context=request_context,
        )

        is_self = user_id == auth_ctx.user_id
        action = "left" if is_self else "removed from"

        logger.info(
            f"Member {action} org: {user_id} - {auth_ctx.organization_id}"
        )
        return {
            "success": True,
            "message": f"Member {'left' if is_self else 'removed from'} organization",
        }

    except Exception as e:
        raise handle_organization_error(e)


# =============================================================================
# Invitation Endpoints
# =============================================================================


@router.get(
    "/{organization_id}/invites",
    response_model=OrganizationInvitesResponse,
    summary="List invites",
    description="List pending invitations.",
)
async def list_invites(
    include_accepted: bool = Query(False, description="Include accepted invites"),
    include_expired: bool = Query(False, description="Include expired invites"),
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.MEMBERS_INVITE)
    ),
) -> OrganizationInvitesResponse:
    """
    List organization invitations.

    Requires: members.invite permission (owner, admin).
    """
    try:
        org_service = get_organization_service()
        invites = await org_service.list_invites(
            organization_id=auth_ctx.organization_id,
            auth_context=auth_ctx,
            include_accepted=include_accepted,
            include_expired=include_expired,
        )

        return OrganizationInvitesResponse(
            invites=invites,
            total=len(invites),
        )

    except Exception as e:
        raise handle_organization_error(e)


@router.delete(
    "/{organization_id}/invites/{invite_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke invite",
    description="Revoke a pending invitation.",
)
async def revoke_invite(
    invite_id: str,
    request: Request,
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.MEMBERS_INVITE)
    ),
) -> Dict:
    """
    Revoke a pending invitation.

    Requires: members.invite permission (owner, admin).
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        await org_service.revoke_invite(
            organization_id=auth_ctx.organization_id,
            invite_id=invite_id,
            auth_context=auth_ctx,
            request_context=request_context,
        )

        logger.info(f"Invite revoked: {invite_id}")
        return {"success": True, "message": "Invitation revoked"}

    except Exception as e:
        raise handle_organization_error(e)


@router.post(
    "/invites/{token}/accept",
    response_model=InviteAcceptResponse,
    summary="Accept invite",
    description="Accept an organization invitation.",
)
async def accept_invite(
    token: str,
    request: Request,
    user_id: str = Depends(verify_api_key),
) -> InviteAcceptResponse:
    """
    Accept an organization invitation.

    The invitation token is provided in the URL.
    The accepting user must be authenticated.
    """
    try:
        org_service = get_organization_service()
        request_context = await get_request_context(request)

        member = await org_service.accept_invite(
            token=token,
            user_id=user_id,
            request_context=request_context,
        )

        # Get organization name for response
        org = await org_service.get_organization(member.organization_id)

        logger.info(
            f"Invite accepted by {user_id[:8]}... for org {member.organization_id}"
        )
        return InviteAcceptResponse(
            success=True,
            organization_id=member.organization_id,
            organization_name=org.name,
            role=member.role,
            member_id=member.id,
        )

    except Exception as e:
        raise handle_organization_error(e)


# =============================================================================
# Quota Endpoints
# =============================================================================


@router.get(
    "/{organization_id}/quota",
    response_model=OrganizationQuotaStatus,
    summary="Get quota status",
    description="Get organization quota and usage status.",
)
async def get_quota_status(
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.ORGANIZATION_VIEW)
    ),
) -> OrganizationQuotaStatus:
    """
    Get organization quota status.

    Requires: organization.view permission (all members).
    """
    try:
        org_service = get_organization_service()
        status = await org_service.check_quota(auth_ctx.organization_id)
        return status

    except Exception as e:
        raise handle_organization_error(e)


# =============================================================================
# Audit Log Endpoints
# =============================================================================


@router.get(
    "/{organization_id}/audit-logs",
    response_model=AuditLogsResponse,
    summary="Get audit logs",
    description="Query organization audit logs.",
)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id_filter: Optional[str] = Query(None, alias="user_id", description="Filter by user"),
    success: Optional[bool] = Query(None, description="Filter by success/failure"),
    limit: int = Query(50, ge=1, le=500, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    auth_ctx: AuthorizationContext = Depends(
        require_permission(Permission.AUDIT_VIEW)
    ),
) -> AuditLogsResponse:
    """
    Query organization audit logs.

    Requires: audit.view permission (owner, admin).

    Supports filtering by:
    - action: e.g., "member.invite", "content.create"
    - resource_type: e.g., "organization", "member", "content"
    - user_id: Filter by user who performed the action
    - success: Filter by success/failure status
    """
    try:
        audit_service = get_audit_service()

        query = AuditLogQuery(
            organization_id=auth_ctx.organization_id,
            user_id=user_id_filter,
            action=action,
            resource_type=resource_type,
            success=success,
            limit=limit,
            offset=offset,
        )

        logs, total = await audit_service.query(query)

        return AuditLogsResponse(
            logs=logs,
            total=total,
            has_more=offset + len(logs) < total,
        )

    except Exception as e:
        raise handle_organization_error(e)


# =============================================================================
# Role Information Endpoints
# =============================================================================


@router.get(
    "/roles/permissions",
    summary="Get role permissions",
    description="Get the permissions for each organization role.",
)
async def get_role_permissions(
    user_id: str = Depends(verify_api_key),
) -> Dict:
    """
    Get permissions for each organization role.

    This endpoint is public information useful for UI permission displays.
    """
    from src.organizations.rbac import ROLE_PERMISSIONS, get_role_description

    return {
        "success": True,
        "roles": {
            role.value: {
                "description": get_role_description(role),
                "permissions": [p.value for p in permissions],
            }
            for role, permissions in ROLE_PERMISSIONS.items()
        },
    }


@router.get(
    "/{organization_id}/my-permissions",
    summary="Get my permissions",
    description="Get the current user's permissions in the organization.",
)
async def get_my_permissions(
    auth_ctx: AuthorizationContext = Depends(get_organization_context),
) -> Dict:
    """
    Get the current user's role and permissions in the organization.
    """
    from src.organizations.rbac import (
        get_assignable_roles,
        get_permission_description,
        get_role_description,
    )

    permissions_list = [
        {
            "permission": p.value,
            "description": get_permission_description(p),
        }
        for p in auth_ctx.permissions
    ]

    assignable = get_assignable_roles(auth_ctx.role) if auth_ctx.role else []

    return {
        "success": True,
        "organization_id": auth_ctx.organization_id,
        "role": auth_ctx.role.value if auth_ctx.role else None,
        "role_description": (
            get_role_description(auth_ctx.role) if auth_ctx.role else None
        ),
        "permissions": permissions_list,
        "can_assign_roles": [r.value for r in assignable],
    }
