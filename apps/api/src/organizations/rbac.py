"""
Role-Based Access Control (RBAC) system for organizations.

This module provides:
- Permission definitions and role-to-permission mappings
- Permission checking functions
- Authorization decorators and utilities

Security Notes:
- All permission checks use constant-time operations where possible
- Failed authorization attempts are logged for security monitoring
- Permission checks are designed to fail-closed (deny by default)
"""

import logging
from enum import Enum
from functools import wraps
from typing import Callable, Dict, FrozenSet, List, Optional, Set, Union

from src.types.organization import OrganizationRole

logger = logging.getLogger(__name__)


# =============================================================================
# Permission Definitions
# =============================================================================


class Permission(str, Enum):
    """
    Granular permissions for organization resources.

    Permissions follow the format: resource.action
    """
    # Organization permissions
    ORGANIZATION_VIEW = "organization.view"
    ORGANIZATION_UPDATE = "organization.update"
    ORGANIZATION_DELETE = "organization.delete"
    ORGANIZATION_TRANSFER = "organization.transfer"

    # Member permissions
    MEMBERS_VIEW = "members.view"
    MEMBERS_INVITE = "members.invite"
    MEMBERS_MANAGE = "members.manage"  # Add, remove, update roles

    # Content permissions
    CONTENT_VIEW = "content.view"
    CONTENT_CREATE = "content.create"
    CONTENT_EDIT = "content.edit"  # Edit own content
    CONTENT_EDIT_ANY = "content.edit_any"  # Edit any content
    CONTENT_DELETE = "content.delete"  # Delete own content
    CONTENT_DELETE_ANY = "content.delete_any"  # Delete any content
    CONTENT_PUBLISH = "content.publish"

    # Brand profile permissions
    BRAND_VIEW = "brand.view"
    BRAND_MANAGE = "brand.manage"

    # Template permissions
    TEMPLATES_VIEW = "templates.view"
    TEMPLATES_MANAGE = "templates.manage"

    # Billing permissions
    BILLING_VIEW = "billing.view"
    BILLING_MANAGE = "billing.manage"

    # Audit permissions
    AUDIT_VIEW = "audit.view"

    # Settings permissions
    SETTINGS_VIEW = "settings.view"
    SETTINGS_MANAGE = "settings.manage"


# =============================================================================
# Role-Permission Mappings
# =============================================================================


# Define permissions for each role using frozensets for immutability
ROLE_PERMISSIONS: Dict[OrganizationRole, FrozenSet[Permission]] = {
    OrganizationRole.OWNER: frozenset([
        # Organization
        Permission.ORGANIZATION_VIEW,
        Permission.ORGANIZATION_UPDATE,
        Permission.ORGANIZATION_DELETE,
        Permission.ORGANIZATION_TRANSFER,
        # Members
        Permission.MEMBERS_VIEW,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_MANAGE,
        # Content
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_EDIT_ANY,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_DELETE_ANY,
        Permission.CONTENT_PUBLISH,
        # Brand
        Permission.BRAND_VIEW,
        Permission.BRAND_MANAGE,
        # Templates
        Permission.TEMPLATES_VIEW,
        Permission.TEMPLATES_MANAGE,
        # Billing
        Permission.BILLING_VIEW,
        Permission.BILLING_MANAGE,
        # Audit
        Permission.AUDIT_VIEW,
        # Settings
        Permission.SETTINGS_VIEW,
        Permission.SETTINGS_MANAGE,
    ]),

    OrganizationRole.ADMIN: frozenset([
        # Organization (no delete or transfer)
        Permission.ORGANIZATION_VIEW,
        Permission.ORGANIZATION_UPDATE,
        # Members
        Permission.MEMBERS_VIEW,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_MANAGE,
        # Content
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_EDIT_ANY,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_DELETE_ANY,
        Permission.CONTENT_PUBLISH,
        # Brand
        Permission.BRAND_VIEW,
        Permission.BRAND_MANAGE,
        # Templates
        Permission.TEMPLATES_VIEW,
        Permission.TEMPLATES_MANAGE,
        # Billing (view only)
        Permission.BILLING_VIEW,
        # Audit
        Permission.AUDIT_VIEW,
        # Settings
        Permission.SETTINGS_VIEW,
        Permission.SETTINGS_MANAGE,
    ]),

    OrganizationRole.EDITOR: frozenset([
        # Organization (view only)
        Permission.ORGANIZATION_VIEW,
        # Members (view only)
        Permission.MEMBERS_VIEW,
        # Content (own content management)
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_DELETE,
        # Brand (view only)
        Permission.BRAND_VIEW,
        # Templates (view only)
        Permission.TEMPLATES_VIEW,
        # Settings (view only)
        Permission.SETTINGS_VIEW,
    ]),

    OrganizationRole.VIEWER: frozenset([
        # View-only permissions
        Permission.ORGANIZATION_VIEW,
        Permission.MEMBERS_VIEW,
        Permission.CONTENT_VIEW,
        Permission.BRAND_VIEW,
        Permission.TEMPLATES_VIEW,
        Permission.SETTINGS_VIEW,
    ]),
}


# =============================================================================
# Permission Checking Functions
# =============================================================================


def get_role_permissions(role: OrganizationRole) -> FrozenSet[Permission]:
    """
    Get all permissions for a role.

    Args:
        role: The organization role.

    Returns:
        Frozenset of permissions for the role.
    """
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: OrganizationRole, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: The organization role to check.
        permission: The permission to verify.

    Returns:
        True if the role has the permission, False otherwise.
    """
    return permission in get_role_permissions(role)


def has_any_permission(role: OrganizationRole, permissions: List[Permission]) -> bool:
    """
    Check if a role has any of the specified permissions.

    Args:
        role: The organization role to check.
        permissions: List of permissions where at least one must be present.

    Returns:
        True if the role has at least one of the permissions.
    """
    role_perms = get_role_permissions(role)
    return any(p in role_perms for p in permissions)


def has_all_permissions(role: OrganizationRole, permissions: List[Permission]) -> bool:
    """
    Check if a role has all of the specified permissions.

    Args:
        role: The organization role to check.
        permissions: List of permissions that must all be present.

    Returns:
        True if the role has all of the permissions.
    """
    role_perms = get_role_permissions(role)
    return all(p in role_perms for p in permissions)


def get_missing_permissions(
    role: OrganizationRole,
    required_permissions: List[Permission]
) -> List[Permission]:
    """
    Get list of permissions that a role is missing.

    Args:
        role: The organization role to check.
        required_permissions: List of required permissions.

    Returns:
        List of missing permissions (empty if all present).
    """
    role_perms = get_role_permissions(role)
    return [p for p in required_permissions if p not in role_perms]


# =============================================================================
# Role Hierarchy Functions
# =============================================================================


# Role hierarchy levels (higher number = more privileges)
ROLE_LEVELS: Dict[OrganizationRole, int] = {
    OrganizationRole.OWNER: 100,
    OrganizationRole.ADMIN: 75,
    OrganizationRole.EDITOR: 50,
    OrganizationRole.VIEWER: 25,
}


def get_role_level(role: OrganizationRole) -> int:
    """
    Get the privilege level of a role.

    Args:
        role: The organization role.

    Returns:
        Integer privilege level (higher = more privileges).
    """
    return ROLE_LEVELS.get(role, 0)


def is_role_higher(role1: OrganizationRole, role2: OrganizationRole) -> bool:
    """
    Check if role1 has higher privileges than role2.

    Args:
        role1: The first role.
        role2: The second role to compare against.

    Returns:
        True if role1 > role2 in privilege level.
    """
    return get_role_level(role1) > get_role_level(role2)


def is_role_higher_or_equal(role1: OrganizationRole, role2: OrganizationRole) -> bool:
    """
    Check if role1 has higher or equal privileges to role2.

    Args:
        role1: The first role.
        role2: The second role to compare against.

    Returns:
        True if role1 >= role2 in privilege level.
    """
    return get_role_level(role1) >= get_role_level(role2)


def can_manage_role(manager_role: OrganizationRole, target_role: OrganizationRole) -> bool:
    """
    Check if a manager can modify a user with the target role.

    Rules:
    - Owners can manage anyone except other owners (special transfer process)
    - Admins can manage editors and viewers
    - Others cannot manage anyone

    Args:
        manager_role: The role of the user attempting to manage.
        target_role: The role of the user being managed.

    Returns:
        True if the management action is allowed.
    """
    if manager_role == OrganizationRole.OWNER:
        return target_role != OrganizationRole.OWNER

    if manager_role == OrganizationRole.ADMIN:
        return target_role in (OrganizationRole.EDITOR, OrganizationRole.VIEWER)

    return False


def can_assign_role(assigner_role: OrganizationRole, new_role: OrganizationRole) -> bool:
    """
    Check if a user can assign a specific role to another user.

    Rules:
    - Owners can assign any role except owner (ownership transfer is separate)
    - Admins can assign editor and viewer roles
    - Others cannot assign roles

    Args:
        assigner_role: The role of the user assigning the role.
        new_role: The role being assigned.

    Returns:
        True if the role assignment is allowed.
    """
    if assigner_role == OrganizationRole.OWNER:
        return new_role != OrganizationRole.OWNER

    if assigner_role == OrganizationRole.ADMIN:
        return new_role in (OrganizationRole.EDITOR, OrganizationRole.VIEWER)

    return False


def get_assignable_roles(assigner_role: OrganizationRole) -> List[OrganizationRole]:
    """
    Get list of roles that a user can assign.

    Args:
        assigner_role: The role of the user attempting to assign.

    Returns:
        List of roles that can be assigned.
    """
    if assigner_role == OrganizationRole.OWNER:
        return [OrganizationRole.ADMIN, OrganizationRole.EDITOR, OrganizationRole.VIEWER]

    if assigner_role == OrganizationRole.ADMIN:
        return [OrganizationRole.EDITOR, OrganizationRole.VIEWER]

    return []


# =============================================================================
# Permission Groups (for UI/API convenience)
# =============================================================================


class PermissionGroup:
    """
    Grouped permissions for common use cases.

    These groups can be used for UI displays or bulk permission checks.
    """

    # Full organization management
    ORGANIZATION_FULL = [
        Permission.ORGANIZATION_VIEW,
        Permission.ORGANIZATION_UPDATE,
        Permission.ORGANIZATION_DELETE,
        Permission.ORGANIZATION_TRANSFER,
    ]

    # Content creation and editing
    CONTENT_AUTHOR = [
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_DELETE,
    ]

    # Full content management
    CONTENT_MANAGER = [
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_EDIT_ANY,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_DELETE_ANY,
        Permission.CONTENT_PUBLISH,
    ]

    # Team management
    TEAM_MANAGER = [
        Permission.MEMBERS_VIEW,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_MANAGE,
    ]

    # View-only access
    READ_ONLY = [
        Permission.ORGANIZATION_VIEW,
        Permission.MEMBERS_VIEW,
        Permission.CONTENT_VIEW,
        Permission.BRAND_VIEW,
        Permission.TEMPLATES_VIEW,
        Permission.SETTINGS_VIEW,
    ]


# =============================================================================
# Authorization Context
# =============================================================================


class AuthorizationContext:
    """
    Context object for authorization decisions.

    Holds all relevant information for making authorization decisions
    and provides methods for checking permissions.
    """

    def __init__(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        role: Optional[OrganizationRole] = None,
        is_org_member: bool = False,
    ):
        """
        Initialize authorization context.

        Args:
            user_id: The authenticated user's ID.
            organization_id: The organization context (if any).
            role: The user's role in the organization (if member).
            is_org_member: Whether the user is a member of the organization.
        """
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role
        self.is_org_member = is_org_member
        self._permissions: Optional[FrozenSet[Permission]] = None

    @property
    def permissions(self) -> FrozenSet[Permission]:
        """Get the user's permissions (cached)."""
        if self._permissions is None:
            if self.role:
                self._permissions = get_role_permissions(self.role)
            else:
                self._permissions = frozenset()
        return self._permissions

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(p in self.permissions for p in permissions)

    def can_manage_member(self, target_role: OrganizationRole) -> bool:
        """Check if user can manage a member with the target role."""
        if not self.role:
            return False
        return can_manage_role(self.role, target_role)

    def can_assign_role(self, new_role: OrganizationRole) -> bool:
        """Check if user can assign a specific role."""
        if not self.role:
            return False
        return can_assign_role(self.role, new_role)

    def require_permission(self, permission: Permission) -> None:
        """
        Require a specific permission, raising if not present.

        Args:
            permission: The required permission.

        Raises:
            PermissionDeniedError: If permission is not present.
        """
        if not self.has_permission(permission):
            raise PermissionDeniedError(
                required_permission=permission,
                user_role=self.role,
            )

    def require_any_permission(self, permissions: List[Permission]) -> None:
        """
        Require any of the specified permissions.

        Args:
            permissions: List of permissions where at least one is required.

        Raises:
            PermissionDeniedError: If no permission is present.
        """
        if not self.has_any_permission(permissions):
            raise PermissionDeniedError(
                required_permission=permissions[0],  # Report first as example
                user_role=self.role,
            )

    def require_all_permissions(self, permissions: List[Permission]) -> None:
        """
        Require all of the specified permissions.

        Args:
            permissions: List of required permissions.

        Raises:
            PermissionDeniedError: If any permission is missing.
        """
        missing = get_missing_permissions(self.role, permissions) if self.role else permissions
        if missing:
            raise PermissionDeniedError(
                required_permission=missing[0],
                user_role=self.role,
            )


# =============================================================================
# Authorization Exceptions
# =============================================================================


class AuthorizationError(Exception):
    """Base exception for authorization failures."""

    def __init__(self, message: str = "Authorization failed"):
        self.message = message
        super().__init__(message)


class PermissionDeniedError(AuthorizationError):
    """Raised when a user lacks required permissions."""

    def __init__(
        self,
        required_permission: Optional[Permission] = None,
        user_role: Optional[OrganizationRole] = None,
        message: Optional[str] = None,
    ):
        self.required_permission = required_permission
        self.user_role = user_role

        if message:
            self.message = message
        elif required_permission:
            self.message = f"Permission denied: {required_permission.value} is required"
        else:
            self.message = "Permission denied"

        super().__init__(self.message)


class NotOrganizationMemberError(AuthorizationError):
    """Raised when a user is not a member of the organization."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.message = "You are not a member of this organization"
        super().__init__(self.message)


class OrganizationNotFoundError(AuthorizationError):
    """Raised when an organization does not exist."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.message = "Organization not found"
        super().__init__(self.message)


# =============================================================================
# Utility Functions
# =============================================================================


def log_authorization_failure(
    user_id: str,
    organization_id: Optional[str],
    required_permission: Permission,
    user_role: Optional[OrganizationRole],
) -> None:
    """
    Log an authorization failure for security monitoring.

    Args:
        user_id: The user who was denied.
        organization_id: The organization context.
        required_permission: The permission that was required.
        user_role: The user's current role (if any).
    """
    logger.warning(
        "Authorization denied",
        extra={
            "user_id": user_id[:8] + "..." if len(user_id) > 8 else user_id,
            "organization_id": organization_id,
            "required_permission": required_permission.value,
            "user_role": user_role.value if user_role else None,
            "security_event": "authorization_denied",
        }
    )


def get_permission_description(permission: Permission) -> str:
    """
    Get a human-readable description of a permission.

    Args:
        permission: The permission to describe.

    Returns:
        Human-readable description string.
    """
    descriptions = {
        Permission.ORGANIZATION_VIEW: "View organization details",
        Permission.ORGANIZATION_UPDATE: "Update organization settings",
        Permission.ORGANIZATION_DELETE: "Delete the organization",
        Permission.ORGANIZATION_TRANSFER: "Transfer organization ownership",
        Permission.MEMBERS_VIEW: "View organization members",
        Permission.MEMBERS_INVITE: "Invite new members",
        Permission.MEMBERS_MANAGE: "Manage member roles and access",
        Permission.CONTENT_VIEW: "View content",
        Permission.CONTENT_CREATE: "Create new content",
        Permission.CONTENT_EDIT: "Edit own content",
        Permission.CONTENT_EDIT_ANY: "Edit any content",
        Permission.CONTENT_DELETE: "Delete own content",
        Permission.CONTENT_DELETE_ANY: "Delete any content",
        Permission.CONTENT_PUBLISH: "Publish content",
        Permission.BRAND_VIEW: "View brand profiles",
        Permission.BRAND_MANAGE: "Manage brand profiles",
        Permission.TEMPLATES_VIEW: "View templates",
        Permission.TEMPLATES_MANAGE: "Manage templates",
        Permission.BILLING_VIEW: "View billing information",
        Permission.BILLING_MANAGE: "Manage billing and subscriptions",
        Permission.AUDIT_VIEW: "View audit logs",
        Permission.SETTINGS_VIEW: "View settings",
        Permission.SETTINGS_MANAGE: "Manage settings",
    }
    return descriptions.get(permission, permission.value)


def get_role_description(role: OrganizationRole) -> str:
    """
    Get a human-readable description of a role.

    Args:
        role: The role to describe.

    Returns:
        Human-readable description string.
    """
    descriptions = {
        OrganizationRole.OWNER: "Full control of the organization including deletion and ownership transfer",
        OrganizationRole.ADMIN: "Manage members, content, and settings (cannot delete organization)",
        OrganizationRole.EDITOR: "Create and edit content, view organization resources",
        OrganizationRole.VIEWER: "Read-only access to organization resources",
    }
    return descriptions.get(role, role.value)
