"""
FastAPI dependencies for the Blog AI application.

This module provides reusable dependencies for:
- Organization context and authorization
- Request context extraction
- Permission checking

Usage:
    from app.dependencies import (
        get_organization_context,
        require_permission,
        require_role,
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

__all__ = [
    # Context extraction
    "get_request_context",
    "get_organization_id_from_header",
    "get_organization_id_from_path",
    "get_current_organization",
    "get_organization_context",
    "get_optional_organization_context",
    # Authorization
    "require_role",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_owner",
    "require_resource_owner_or_permission",
]
