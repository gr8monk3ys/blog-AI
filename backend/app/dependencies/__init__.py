"""
FastAPI dependencies for the Blog AI application.

This module provides reusable dependencies for:
- Organization context and authorization
- Request context extraction
- Permission checking
- Content and resource authorization
- Quota enforcement

Usage:
    from app.dependencies import (
        get_organization_context,
        require_permission,
        require_role,
        require_content_creation,
        require_org_scoped_api_key,
    )
"""

from app.dependencies.organization import (
    get_current_organization,
    get_optional_organization_context,
    get_organization_context,
    get_organization_id_from_header,
    get_organization_id_from_path,
    get_request_context,
    require_all_permissions,
    require_any_permission,
    require_owner,
    require_permission,
    require_resource_owner_or_permission,
    require_role,
)

from app.dependencies.authorization import (
    # Auth context types
    OrganizationAuthContext,
    # Organization-scoped authentication
    require_org_scoped_api_key,
    # Content authorization
    require_content_creation,
    require_content_access,
    require_content_edit,
    require_content_publish,
    # Knowledge base authorization
    require_knowledge_read,
    require_knowledge_write,
    # Brand profile authorization
    require_brand_read,
    require_brand_write,
    # Quota enforcement
    get_organization_quota_context,
    require_content_generation_quota,
    # Feature flags
    require_feature,
    # Admin operations
    require_admin,
    # Audit helpers
    log_authorized_action,
)

__all__ = [
    # Context extraction
    "get_request_context",
    "get_organization_id_from_header",
    "get_organization_id_from_path",
    "get_current_organization",
    "get_organization_context",
    "get_optional_organization_context",
    # Base authorization
    "require_role",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_owner",
    "require_resource_owner_or_permission",
    # Auth context types
    "OrganizationAuthContext",
    # Organization-scoped authentication
    "require_org_scoped_api_key",
    # Content authorization
    "require_content_creation",
    "require_content_access",
    "require_content_edit",
    "require_content_publish",
    # Knowledge base authorization
    "require_knowledge_read",
    "require_knowledge_write",
    # Brand profile authorization
    "require_brand_read",
    "require_brand_write",
    # Quota enforcement
    "get_organization_quota_context",
    "require_content_generation_quota",
    # Feature flags
    "require_feature",
    # Admin operations
    "require_admin",
    # Audit helpers
    "log_authorized_action",
]
