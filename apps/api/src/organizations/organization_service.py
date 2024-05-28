"""
Organization service for managing organizations, members, and invitations.

This module provides:
- CRUD operations for organizations
- Member management (invite, add, remove, update role)
- Invitation handling
- Organization settings management
- Quota management

Security Notes:
- All operations validate permissions before execution
- Sensitive operations are logged to audit trail
- Database operations use parameterized queries
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.types.organization import (
    AuditAction,
    InviteStatus,
    Organization,
    OrganizationCreate,
    OrganizationInvite,
    OrganizationInviteCreate,
    OrganizationMember,
    OrganizationMemberUpdate,
    OrganizationPlanTier,
    OrganizationQuotaStatus,
    OrganizationRole,
    OrganizationSettings,
    OrganizationSummary,
    OrganizationUpdate,
    ResourceType,
)
from src.organizations.rbac import (
    AuthorizationContext,
    NotOrganizationMemberError,
    OrganizationNotFoundError,
    Permission,
    PermissionDeniedError,
    can_assign_role,
    can_manage_role,
    has_permission,
)

logger = logging.getLogger(__name__)


class OrganizationServiceError(Exception):
    """Base exception for organization service errors."""

    def __init__(self, message: str, code: str = "ORG_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class OrganizationExistsError(OrganizationServiceError):
    """Raised when an organization slug already exists."""

    def __init__(self, slug: str):
        super().__init__(
            f"Organization with slug '{slug}' already exists",
            code="ORG_SLUG_EXISTS"
        )


class MemberExistsError(OrganizationServiceError):
    """Raised when a user is already a member."""

    def __init__(self, user_id: str, organization_id: str):
        super().__init__(
            "User is already a member of this organization",
            code="MEMBER_EXISTS"
        )


class InviteExistsError(OrganizationServiceError):
    """Raised when a pending invite already exists."""

    def __init__(self, email: str, organization_id: str):
        super().__init__(
            f"A pending invitation for {email} already exists",
            code="INVITE_EXISTS"
        )


class InviteNotFoundError(OrganizationServiceError):
    """Raised when an invite is not found or expired."""

    def __init__(self, token: str):
        super().__init__(
            "Invitation not found, expired, or already used",
            code="INVITE_NOT_FOUND"
        )


class MemberNotFoundError(OrganizationServiceError):
    """Raised when a member is not found."""

    def __init__(self, user_id: str, organization_id: str):
        super().__init__(
            "Member not found in this organization",
            code="MEMBER_NOT_FOUND"
        )


class QuotaExceededError(OrganizationServiceError):
    """Raised when organization quota is exceeded."""

    def __init__(self, organization_id: str, current: int, limit: int):
        self.current = current
        self.limit = limit
        super().__init__(
            f"Organization quota exceeded ({current}/{limit})",
            code="QUOTA_EXCEEDED"
        )


class MemberLimitExceededError(OrganizationServiceError):
    """Raised when organization member limit is reached."""

    def __init__(self, organization_id: str, current: int, limit: int):
        self.current = current
        self.limit = limit
        super().__init__(
            f"Organization member limit reached ({current}/{limit})",
            code="MEMBER_LIMIT_EXCEEDED"
        )


class OrganizationService:
    """
    Service for organization management operations.

    This class provides the business logic for organization operations,
    separate from the database layer for better testability.
    """

    def __init__(self, db_client: Any, audit_service: Optional[Any] = None):
        """
        Initialize the organization service.

        Args:
            db_client: Database client (Supabase client or similar).
            audit_service: Optional audit service for logging actions.
        """
        self.db = db_client
        self.audit = audit_service
        self._invite_expiry_days = 7

    # =========================================================================
    # Organization CRUD Operations
    # =========================================================================

    async def create_organization(
        self,
        data: OrganizationCreate,
        user_id: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Organization:
        """
        Create a new organization with the user as owner.

        Args:
            data: Organization creation data.
            user_id: ID of the user creating the organization.
            request_context: Optional request context for audit logging.

        Returns:
            The created organization.

        Raises:
            OrganizationExistsError: If slug is already taken.
        """
        logger.info(f"Creating organization: {data.slug} for user: {user_id[:8]}...")

        # Check if slug is available
        existing = await self._get_organization_by_slug(data.slug)
        if existing:
            raise OrganizationExistsError(data.slug)

        # Use database function to create org with owner atomically
        result = await self.db.rpc(
            "create_organization_with_owner",
            {
                "p_name": data.name,
                "p_slug": data.slug,
                "p_user_id": user_id,
                "p_description": data.description,
                "p_plan_tier": data.plan_tier.value,
            }
        ).execute()

        if not result.data or len(result.data) == 0:
            raise OrganizationServiceError("Failed to create organization")

        org_id = result.data[0]["organization_id"]

        # Fetch the created organization
        org = await self.get_organization(org_id)

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=org_id,
                user_id=user_id,
                action=AuditAction.ORGANIZATION_CREATE,
                resource_type=ResourceType.ORGANIZATION,
                resource_id=org_id,
                new_values={
                    "name": data.name,
                    "slug": data.slug,
                    "plan_tier": data.plan_tier.value,
                },
                request_context=request_context,
            )

        logger.info(f"Organization created: {org_id}")
        return org

    async def get_organization(self, organization_id: str) -> Organization:
        """
        Get an organization by ID.

        Args:
            organization_id: The organization UUID.

        Returns:
            The organization.

        Raises:
            OrganizationNotFoundError: If organization doesn't exist.
        """
        result = await self.db.table("organizations").select("*").eq(
            "id", organization_id
        ).eq("is_active", True).single().execute()

        if not result.data:
            raise OrganizationNotFoundError(organization_id)

        return self._map_organization(result.data)

    async def get_organization_by_slug(self, slug: str) -> Organization:
        """
        Get an organization by slug.

        Args:
            slug: The organization slug.

        Returns:
            The organization.

        Raises:
            OrganizationNotFoundError: If organization doesn't exist.
        """
        result = await self.db.table("organizations").select("*").eq(
            "slug", slug.lower()
        ).eq("is_active", True).single().execute()

        if not result.data:
            raise OrganizationNotFoundError(slug)

        return self._map_organization(result.data)

    async def _get_organization_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Internal: Get organization by slug without raising."""
        result = await self.db.table("organizations").select("id").eq(
            "slug", slug.lower()
        ).eq("is_active", True).maybe_single().execute()
        return result.data

    async def list_user_organizations(self, user_id: str) -> List[OrganizationSummary]:
        """
        List all organizations a user is a member of.

        Args:
            user_id: The user ID.

        Returns:
            List of organization summaries with user's role.
        """
        result = await self.db.rpc(
            "get_user_organizations",
            {"p_user_id": user_id}
        ).execute()

        return [
            OrganizationSummary(
                id=row["organization_id"],
                name=row["organization_name"],
                slug=row["organization_slug"],
                role=OrganizationRole(row["role"]),
                plan_tier=OrganizationPlanTier(row["plan_tier"]),
                member_count=row["member_count"],
                joined_at=datetime.fromisoformat(row["joined_at"].replace("Z", "+00:00")),
            )
            for row in (result.data or [])
        ]

    async def update_organization(
        self,
        organization_id: str,
        data: OrganizationUpdate,
        auth_context: AuthorizationContext,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Organization:
        """
        Update an organization.

        Args:
            organization_id: The organization ID.
            data: Update data.
            auth_context: Authorization context.
            request_context: Optional request context for audit logging.

        Returns:
            The updated organization.

        Raises:
            PermissionDeniedError: If user lacks permission.
        """
        auth_context.require_permission(Permission.ORGANIZATION_UPDATE)

        # Get current state for audit
        current = await self.get_organization(organization_id)
        old_values = {
            "name": current.name,
            "description": current.description,
            "logo_url": current.logo_url,
            "website_url": current.website_url,
        }

        # Build update dict
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.description is not None:
            update_data["description"] = data.description
        if data.logo_url is not None:
            update_data["logo_url"] = data.logo_url
        if data.website_url is not None:
            update_data["website_url"] = data.website_url
        if data.settings is not None:
            update_data["settings"] = data.settings.model_dump()

        if not update_data:
            return current

        update_data["updated_at"] = datetime.utcnow().isoformat()

        await self.db.table("organizations").update(
            update_data
        ).eq("id", organization_id).execute()

        org = await self.get_organization(organization_id)

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=organization_id,
                user_id=auth_context.user_id,
                action=AuditAction.ORGANIZATION_UPDATE,
                resource_type=ResourceType.ORGANIZATION,
                resource_id=organization_id,
                old_values=old_values,
                new_values=update_data,
                request_context=request_context,
            )

        logger.info(f"Organization updated: {organization_id}")
        return org

    async def delete_organization(
        self,
        organization_id: str,
        auth_context: AuthorizationContext,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Soft delete an organization.

        Args:
            organization_id: The organization ID.
            auth_context: Authorization context.
            request_context: Optional request context for audit logging.

        Returns:
            True if deleted.

        Raises:
            PermissionDeniedError: If user lacks permission.
        """
        auth_context.require_permission(Permission.ORGANIZATION_DELETE)

        org = await self.get_organization(organization_id)

        # Soft delete
        await self.db.table("organizations").update({
            "is_active": False,
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": auth_context.user_id,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", organization_id).execute()

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=organization_id,
                user_id=auth_context.user_id,
                action=AuditAction.ORGANIZATION_DELETE,
                resource_type=ResourceType.ORGANIZATION,
                resource_id=organization_id,
                old_values={"name": org.name, "slug": org.slug},
                request_context=request_context,
            )

        logger.info(f"Organization deleted: {organization_id}")
        return True

    # =========================================================================
    # Member Management
    # =========================================================================

    async def get_member(
        self,
        organization_id: str,
        user_id: str,
    ) -> Optional[OrganizationMember]:
        """
        Get a member's details in an organization.

        Args:
            organization_id: The organization ID.
            user_id: The user ID.

        Returns:
            The member or None if not found.
        """
        result = await self.db.table("organization_members").select("*").eq(
            "organization_id", organization_id
        ).eq("user_id", user_id).eq("is_active", True).maybe_single().execute()

        if not result.data:
            return None

        return self._map_member(result.data)

    async def get_member_role(
        self,
        organization_id: str,
        user_id: str,
    ) -> Optional[OrganizationRole]:
        """
        Get a user's role in an organization.

        Args:
            organization_id: The organization ID.
            user_id: The user ID.

        Returns:
            The role or None if not a member.
        """
        member = await self.get_member(organization_id, user_id)
        return member.role if member else None

    async def list_members(
        self,
        organization_id: str,
        auth_context: AuthorizationContext,
        include_inactive: bool = False,
    ) -> List[OrganizationMember]:
        """
        List all members of an organization.

        Args:
            organization_id: The organization ID.
            auth_context: Authorization context.
            include_inactive: Include deactivated members.

        Returns:
            List of members.
        """
        auth_context.require_permission(Permission.MEMBERS_VIEW)

        query = self.db.table("organization_members").select("*").eq(
            "organization_id", organization_id
        )

        if not include_inactive:
            query = query.eq("is_active", True)

        result = await query.order("created_at", desc=False).execute()

        return [self._map_member(row) for row in (result.data or [])]

    async def add_member(
        self,
        organization_id: str,
        user_id: str,
        role: OrganizationRole,
        auth_context: AuthorizationContext,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> OrganizationMember:
        """
        Add a member directly to an organization.

        Args:
            organization_id: The organization ID.
            user_id: The user to add.
            role: The role to assign.
            auth_context: Authorization context.
            request_context: Optional request context.

        Returns:
            The new member.

        Raises:
            PermissionDeniedError: If user lacks permission.
            MemberExistsError: If user is already a member.
            MemberLimitExceededError: If member limit reached.
        """
        auth_context.require_permission(Permission.MEMBERS_MANAGE)

        if not can_assign_role(auth_context.role, role):
            raise PermissionDeniedError(
                message=f"You cannot assign the {role.value} role"
            )

        # Check if already a member
        existing = await self.get_member(organization_id, user_id)
        if existing:
            raise MemberExistsError(user_id, organization_id)

        # Check member limit
        await self._check_member_limit(organization_id)

        # Get the adder's member ID for the invited_by field
        adder_member = await self.get_member(organization_id, auth_context.user_id)

        result = await self.db.table("organization_members").insert({
            "organization_id": organization_id,
            "user_id": user_id,
            "role": role.value,
            "invited_by": adder_member.id if adder_member else None,
            "invite_accepted_at": datetime.utcnow().isoformat(),
        }).execute()

        member = self._map_member(result.data[0])

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=organization_id,
                user_id=auth_context.user_id,
                action=AuditAction.MEMBER_JOIN,
                resource_type=ResourceType.MEMBER,
                resource_id=member.id,
                new_values={"user_id": user_id, "role": role.value},
                request_context=request_context,
            )

        logger.info(f"Member added to organization: {user_id} -> {organization_id}")
        return member

    async def update_member_role(
        self,
        organization_id: str,
        target_user_id: str,
        new_role: OrganizationRole,
        auth_context: AuthorizationContext,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> OrganizationMember:
        """
        Update a member's role.

        Args:
            organization_id: The organization ID.
            target_user_id: The user whose role to update.
            new_role: The new role.
            auth_context: Authorization context.
            request_context: Optional request context.

        Returns:
            The updated member.

        Raises:
            PermissionDeniedError: If lacking permission.
            MemberNotFoundError: If member not found.
        """
        auth_context.require_permission(Permission.MEMBERS_MANAGE)

        # Get target member
        member = await self.get_member(organization_id, target_user_id)
        if not member:
            raise MemberNotFoundError(target_user_id, organization_id)

        # Check if can manage this member's role
        if not can_manage_role(auth_context.role, member.role):
            raise PermissionDeniedError(
                message=f"You cannot modify users with the {member.role.value} role"
            )

        # Check if can assign new role
        if not can_assign_role(auth_context.role, new_role):
            raise PermissionDeniedError(
                message=f"You cannot assign the {new_role.value} role"
            )

        old_role = member.role

        await self.db.table("organization_members").update({
            "role": new_role.value,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", member.id).execute()

        updated_member = await self.get_member(organization_id, target_user_id)

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=organization_id,
                user_id=auth_context.user_id,
                action=AuditAction.MEMBER_UPDATE_ROLE,
                resource_type=ResourceType.MEMBER,
                resource_id=member.id,
                old_values={"role": old_role.value},
                new_values={"role": new_role.value},
                metadata={"target_user_id": target_user_id},
                request_context=request_context,
            )

        logger.info(
            f"Member role updated: {target_user_id} {old_role.value} -> {new_role.value}"
        )
        return updated_member

    async def remove_member(
        self,
        organization_id: str,
        target_user_id: str,
        auth_context: AuthorizationContext,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Remove a member from an organization.

        Args:
            organization_id: The organization ID.
            target_user_id: The user to remove.
            auth_context: Authorization context.
            request_context: Optional request context.

        Returns:
            True if removed.

        Raises:
            PermissionDeniedError: If lacking permission.
            MemberNotFoundError: If member not found.
        """
        # Users can remove themselves (leave)
        is_self_removal = auth_context.user_id == target_user_id

        if not is_self_removal:
            auth_context.require_permission(Permission.MEMBERS_MANAGE)

        member = await self.get_member(organization_id, target_user_id)
        if not member:
            raise MemberNotFoundError(target_user_id, organization_id)

        # Cannot remove owner (must transfer ownership first)
        if member.role == OrganizationRole.OWNER:
            raise PermissionDeniedError(
                message="Cannot remove organization owner. Transfer ownership first."
            )

        # Check if can manage this member
        if not is_self_removal and not can_manage_role(auth_context.role, member.role):
            raise PermissionDeniedError(
                message=f"You cannot remove users with the {member.role.value} role"
            )

        # Soft delete the membership
        await self.db.table("organization_members").update({
            "is_active": False,
            "deactivated_at": datetime.utcnow().isoformat(),
            "deactivated_by": auth_context.user_id,
            "deactivation_reason": "self_leave" if is_self_removal else "removed",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", member.id).execute()

        # Log audit event
        if self.audit:
            action = AuditAction.MEMBER_LEAVE if is_self_removal else AuditAction.MEMBER_REMOVE
            await self.audit.log(
                organization_id=organization_id,
                user_id=auth_context.user_id,
                action=action,
                resource_type=ResourceType.MEMBER,
                resource_id=member.id,
                old_values={"user_id": target_user_id, "role": member.role.value},
                request_context=request_context,
            )

        logger.info(f"Member removed from organization: {target_user_id}")
        return True

    async def _check_member_limit(self, organization_id: str) -> None:
        """Check if organization has reached member limit."""
        org = await self.get_organization(organization_id)
        max_members = org.settings.max_members

        if max_members == -1:  # Unlimited
            return

        # Count current members
        result = await self.db.table("organization_members").select(
            "id", count="exact"
        ).eq("organization_id", organization_id).eq("is_active", True).execute()

        current_count = result.count or 0

        if current_count >= max_members:
            raise MemberLimitExceededError(organization_id, current_count, max_members)

    # =========================================================================
    # Invitation Management
    # =========================================================================

    async def create_invite(
        self,
        organization_id: str,
        data: OrganizationInviteCreate,
        auth_context: AuthorizationContext,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[OrganizationInvite, str]:
        """
        Create an invitation to join the organization.

        Args:
            organization_id: The organization ID.
            data: Invite creation data.
            auth_context: Authorization context.
            request_context: Optional request context.

        Returns:
            Tuple of (invite, plaintext_token).

        Raises:
            PermissionDeniedError: If lacking permission.
            InviteExistsError: If pending invite exists.
            MemberExistsError: If user is already a member.
        """
        auth_context.require_permission(Permission.MEMBERS_INVITE)

        if not can_assign_role(auth_context.role, data.role):
            raise PermissionDeniedError(
                message=f"You cannot invite users with the {data.role.value} role"
            )

        # Check member limit before inviting
        await self._check_member_limit(organization_id)

        # Check if email is already a member (would need to look up user by email)
        # For now, this is handled when they try to accept

        # Check for existing pending invite
        existing = await self._get_pending_invite(organization_id, data.email)
        if existing:
            raise InviteExistsError(data.email, organization_id)

        # Generate invite token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Get inviter's member ID
        inviter_member = await self.get_member(organization_id, auth_context.user_id)

        expires_at = datetime.utcnow() + timedelta(days=self._invite_expiry_days)

        result = await self.db.table("organization_invites").insert({
            "organization_id": organization_id,
            "invited_by": inviter_member.id,
            "email": data.email.lower(),
            "role": data.role.value,
            "token_hash": token_hash,
            "message": data.message,
            "expires_at": expires_at.isoformat(),
        }).execute()

        invite = self._map_invite(result.data[0])

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=organization_id,
                user_id=auth_context.user_id,
                action=AuditAction.INVITE_CREATE,
                resource_type=ResourceType.INVITE,
                resource_id=invite.id,
                new_values={"email": data.email, "role": data.role.value},
                request_context=request_context,
            )

        logger.info(f"Invite created for {data.email} to org {organization_id}")
        return invite, token

    async def accept_invite(
        self,
        token: str,
        user_id: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> OrganizationMember:
        """
        Accept an organization invitation.

        Args:
            token: The invitation token.
            user_id: The accepting user's ID.
            request_context: Optional request context.

        Returns:
            The new membership.

        Raises:
            InviteNotFoundError: If token is invalid or expired.
            MemberExistsError: If already a member.
        """
        # Use database function for atomic operation
        result = await self.db.rpc(
            "accept_organization_invite",
            {
                "p_token": token,
                "p_user_id": user_id,
            }
        ).execute()

        if not result.data or len(result.data) == 0:
            raise InviteNotFoundError(token)

        row = result.data[0]
        if not row["success"]:
            error_msg = row.get("error_message", "Unknown error")
            if "already a member" in error_msg.lower():
                raise MemberExistsError(user_id, row.get("organization_id", ""))
            raise OrganizationServiceError(error_msg)

        organization_id = row["organization_id"]
        member_id = row["member_id"]

        # Fetch the created member
        member_result = await self.db.table("organization_members").select("*").eq(
            "id", member_id
        ).single().execute()

        member = self._map_member(member_result.data)

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=organization_id,
                user_id=user_id,
                action=AuditAction.INVITE_ACCEPT,
                resource_type=ResourceType.MEMBER,
                resource_id=member_id,
                new_values={"role": member.role.value},
                request_context=request_context,
            )

        logger.info(f"Invite accepted by {user_id} for org {organization_id}")
        return member

    async def revoke_invite(
        self,
        organization_id: str,
        invite_id: str,
        auth_context: AuthorizationContext,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Revoke a pending invitation.

        Args:
            organization_id: The organization ID.
            invite_id: The invite ID to revoke.
            auth_context: Authorization context.
            request_context: Optional request context.

        Returns:
            True if revoked.
        """
        auth_context.require_permission(Permission.MEMBERS_INVITE)

        # Get the invite
        result = await self.db.table("organization_invites").select("*").eq(
            "id", invite_id
        ).eq("organization_id", organization_id).single().execute()

        if not result.data:
            raise OrganizationServiceError("Invitation not found", code="INVITE_NOT_FOUND")

        invite = result.data

        if invite.get("accepted_at") or invite.get("revoked_at"):
            raise OrganizationServiceError(
                "Invitation is no longer pending",
                code="INVITE_NOT_PENDING"
            )

        # Revoke
        await self.db.table("organization_invites").update({
            "revoked_at": datetime.utcnow().isoformat(),
            "revoked_by": auth_context.user_id,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", invite_id).execute()

        # Log audit event
        if self.audit:
            await self.audit.log(
                organization_id=organization_id,
                user_id=auth_context.user_id,
                action=AuditAction.INVITE_REVOKE,
                resource_type=ResourceType.INVITE,
                resource_id=invite_id,
                old_values={"email": invite.get("email")},
                request_context=request_context,
            )

        logger.info(f"Invite revoked: {invite_id}")
        return True

    async def list_invites(
        self,
        organization_id: str,
        auth_context: AuthorizationContext,
        include_accepted: bool = False,
        include_expired: bool = False,
    ) -> List[OrganizationInvite]:
        """
        List organization invitations.

        Args:
            organization_id: The organization ID.
            auth_context: Authorization context.
            include_accepted: Include accepted invites.
            include_expired: Include expired invites.

        Returns:
            List of invitations.
        """
        auth_context.require_permission(Permission.MEMBERS_INVITE)

        query = self.db.table("organization_invites").select("*").eq(
            "organization_id", organization_id
        ).is_("revoked_at", "null")

        if not include_accepted:
            query = query.is_("accepted_at", "null")

        if not include_expired:
            query = query.gt("expires_at", datetime.utcnow().isoformat())

        result = await query.order("created_at", desc=True).execute()

        return [self._map_invite(row) for row in (result.data or [])]

    async def _get_pending_invite(
        self,
        organization_id: str,
        email: str,
    ) -> Optional[Dict[str, Any]]:
        """Internal: Get pending invite by email."""
        result = await self.db.table("organization_invites").select("id").eq(
            "organization_id", organization_id
        ).eq("email", email.lower()).is_("accepted_at", "null").is_(
            "revoked_at", "null"
        ).gt("expires_at", datetime.utcnow().isoformat()).maybe_single().execute()

        return result.data

    # =========================================================================
    # Quota Management
    # =========================================================================

    async def check_quota(
        self,
        organization_id: str,
    ) -> OrganizationQuotaStatus:
        """
        Check organization quota status.

        Args:
            organization_id: The organization ID.

        Returns:
            Quota status.
        """
        result = await self.db.rpc(
            "check_organization_quota",
            {"p_organization_id": organization_id}
        ).execute()

        if not result.data or len(result.data) == 0:
            raise OrganizationNotFoundError(organization_id)

        row = result.data[0]
        monthly_limit = row["monthly_limit"]
        current_usage = row["current_usage"]

        return OrganizationQuotaStatus(
            organization_id=organization_id,
            has_quota=row["has_quota"],
            current_usage=current_usage,
            monthly_limit=monthly_limit,
            remaining=row["remaining"],
            reset_date=datetime.fromisoformat(
                row["reset_date"].replace("Z", "+00:00")
            ),
            percentage_used=(
                (current_usage / monthly_limit * 100) if monthly_limit > 0 else 0
            ),
        )

    async def increment_usage(
        self,
        organization_id: str,
        amount: int = 1,
    ) -> OrganizationQuotaStatus:
        """
        Increment organization usage atomically.

        Args:
            organization_id: The organization ID.
            amount: Amount to increment.

        Returns:
            Updated quota status.

        Raises:
            QuotaExceededError: If quota would be exceeded.
        """
        # Check quota first
        status = await self.check_quota(organization_id)
        if not status.has_quota:
            raise QuotaExceededError(
                organization_id,
                status.current_usage,
                status.monthly_limit
            )

        # Increment
        result = await self.db.rpc(
            "increment_organization_usage",
            {
                "p_organization_id": organization_id,
                "p_amount": amount,
            }
        ).execute()

        if not result.data or not result.data[0]["success"]:
            raise OrganizationServiceError("Failed to increment usage")

        # Return updated status
        return await self.check_quota(organization_id)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _map_organization(self, data: Dict[str, Any]) -> Organization:
        """Map database row to Organization model."""
        settings_data = data.get("settings") or {}
        return Organization(
            id=data["id"],
            name=data["name"],
            slug=data["slug"],
            description=data.get("description"),
            plan_tier=OrganizationPlanTier(data.get("plan_tier", "free")),
            settings=OrganizationSettings(**settings_data),
            stripe_customer_id=data.get("stripe_customer_id"),
            stripe_subscription_id=data.get("stripe_subscription_id"),
            monthly_generation_limit=data.get("monthly_generation_limit", 100),
            current_month_usage=data.get("current_month_usage", 0),
            quota_reset_date=datetime.fromisoformat(
                data["quota_reset_date"].replace("Z", "+00:00")
            ),
            logo_url=data.get("logo_url"),
            website_url=data.get("website_url"),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            ),
            created_by=data["created_by"],
        )

    def _map_member(self, data: Dict[str, Any]) -> OrganizationMember:
        """Map database row to OrganizationMember model."""
        return OrganizationMember(
            id=data["id"],
            organization_id=data["organization_id"],
            user_id=data["user_id"],
            role=OrganizationRole(data["role"]),
            invited_by=data.get("invited_by"),
            invite_accepted_at=(
                datetime.fromisoformat(data["invite_accepted_at"].replace("Z", "+00:00"))
                if data.get("invite_accepted_at")
                else None
            ),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            ),
        )

    def _map_invite(self, data: Dict[str, Any]) -> OrganizationInvite:
        """Map database row to OrganizationInvite model."""
        # Determine status
        if data.get("accepted_at"):
            status = InviteStatus.ACCEPTED
        elif data.get("revoked_at"):
            status = InviteStatus.REVOKED
        elif datetime.fromisoformat(
            data["expires_at"].replace("Z", "+00:00")
        ) < datetime.utcnow():
            status = InviteStatus.EXPIRED
        else:
            status = InviteStatus.PENDING

        return OrganizationInvite(
            id=data["id"],
            organization_id=data["organization_id"],
            email=data["email"],
            role=OrganizationRole(data["role"]),
            invited_by=data["invited_by"],
            message=data.get("message"),
            expires_at=datetime.fromisoformat(
                data["expires_at"].replace("Z", "+00:00")
            ),
            status=status,
            resend_count=data.get("resend_count", 0),
            last_resent_at=(
                datetime.fromisoformat(data["last_resent_at"].replace("Z", "+00:00"))
                if data.get("last_resent_at")
                else None
            ),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            ),
        )


# =============================================================================
# Service Singleton (for dependency injection)
# =============================================================================


_organization_service: Optional[OrganizationService] = None


def get_organization_service() -> OrganizationService:
    """
    Get the organization service singleton.

    Returns:
        The organization service instance.

    Raises:
        RuntimeError: If service not initialized.
    """
    global _organization_service
    if _organization_service is None:
        raise RuntimeError(
            "OrganizationService not initialized. "
            "Call init_organization_service() first."
        )
    return _organization_service


def init_organization_service(
    db_client: Any,
    audit_service: Optional[Any] = None,
) -> OrganizationService:
    """
    Initialize the organization service singleton.

    Args:
        db_client: Database client.
        audit_service: Optional audit service.

    Returns:
        The initialized organization service.
    """
    global _organization_service
    _organization_service = OrganizationService(db_client, audit_service)
    logger.info("OrganizationService initialized")
    return _organization_service
