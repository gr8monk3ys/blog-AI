"""
Organizations module for team/workspace management.

This module provides:
- Organization CRUD operations
- Role-based access control (RBAC)
- Member and invitation management
- Audit logging for compliance

Usage:
    from src.organizations import (
        OrganizationService,
        AuditService,
        Permission,
        has_permission,
    )

    # Initialize services
    org_service = init_organization_service(db_client, audit_service)

    # Create organization
    org = await org_service.create_organization(data, user_id)

    # Check permissions
    if has_permission(role, Permission.CONTENT_CREATE):
        # Allow action
        pass
"""

from src.organizations.audit_service import (
    AuditService,
    AuditStatistics,
    get_audit_service,
    init_audit_service,
)
from src.organizations.organization_service import (
    InviteExistsError,
    InviteNotFoundError,
    MemberExistsError,
    MemberLimitExceededError,
    MemberNotFoundError,
    OrganizationExistsError,
    OrganizationService,
    OrganizationServiceError,
    QuotaExceededError,
    get_organization_service,
    init_organization_service,
)
from src.organizations.rbac import (
    AuthorizationContext,
    AuthorizationError,
    NotOrganizationMemberError,
    OrganizationNotFoundError,
    Permission,
    PermissionDeniedError,
    PermissionGroup,
    can_assign_role,
    can_manage_role,
    get_assignable_roles,
    get_missing_permissions,
    get_permission_description,
    get_role_description,
    get_role_level,
    get_role_permissions,
    has_all_permissions,
    has_any_permission,
    has_permission,
    is_role_higher,
    is_role_higher_or_equal,
    log_authorization_failure,
)

__all__ = [
    # Services
    "OrganizationService",
    "AuditService",
    "AuditStatistics",
    # Service singletons
    "get_organization_service",
    "init_organization_service",
    "get_audit_service",
    "init_audit_service",
    # RBAC
    "Permission",
    "PermissionGroup",
    "AuthorizationContext",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
    "get_role_permissions",
    "get_missing_permissions",
    "can_manage_role",
    "can_assign_role",
    "get_assignable_roles",
    "is_role_higher",
    "is_role_higher_or_equal",
    "get_role_level",
    "get_permission_description",
    "get_role_description",
    "log_authorization_failure",
    # Exceptions
    "AuthorizationError",
    "PermissionDeniedError",
    "NotOrganizationMemberError",
    "OrganizationNotFoundError",
    "OrganizationServiceError",
    "OrganizationExistsError",
    "MemberExistsError",
    "MemberNotFoundError",
    "MemberLimitExceededError",
    "InviteExistsError",
    "InviteNotFoundError",
    "QuotaExceededError",
]
