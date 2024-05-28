"""
Organization, membership, and RBAC type definitions.

This module defines Pydantic models for:
- Organizations and workspaces
- Organization memberships with roles
- Invitations and invite tokens
- Audit log entries
- Permission definitions
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# Enums
# =============================================================================


class OrganizationRole(str, Enum):
    """
    Organization member roles with hierarchical permissions.

    Role hierarchy (highest to lowest):
    - owner: Full control including organization deletion
    - admin: Manage members and settings (cannot delete org)
    - editor: Create and edit content
    - viewer: Read-only access
    """
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class OrganizationPlanTier(str, Enum):
    """
    Organization subscription tiers.

    Each tier has different limits for members and content generation.
    """
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class InviteStatus(str, Enum):
    """Status of an organization invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AuditAction(str, Enum):
    """
    Audit log action types.

    Categorized by resource type for easier filtering.
    """
    # Organization actions
    ORGANIZATION_CREATE = "organization.create"
    ORGANIZATION_UPDATE = "organization.update"
    ORGANIZATION_DELETE = "organization.delete"
    ORGANIZATION_TRANSFER = "organization.transfer"

    # Member actions
    MEMBER_INVITE = "member.invite"
    MEMBER_JOIN = "member.join"
    MEMBER_UPDATE_ROLE = "member.update_role"
    MEMBER_REMOVE = "member.remove"
    MEMBER_LEAVE = "member.leave"

    # Invite actions
    INVITE_CREATE = "invite.create"
    INVITE_ACCEPT = "invite.accept"
    INVITE_REVOKE = "invite.revoke"
    INVITE_RESEND = "invite.resend"

    # Content actions
    CONTENT_CREATE = "content.create"
    CONTENT_UPDATE = "content.update"
    CONTENT_DELETE = "content.delete"
    CONTENT_PUBLISH = "content.publish"

    # Brand profile actions
    BRAND_CREATE = "brand.create"
    BRAND_UPDATE = "brand.update"
    BRAND_DELETE = "brand.delete"

    # Template actions
    TEMPLATE_CREATE = "template.create"
    TEMPLATE_UPDATE = "template.update"
    TEMPLATE_DELETE = "template.delete"

    # Settings actions
    SETTINGS_UPDATE = "settings.update"
    BILLING_UPDATE = "billing.update"

    # Security actions
    API_KEY_CREATE = "api_key.create"
    API_KEY_REVOKE = "api_key.revoke"
    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILURE = "login.failure"


class ResourceType(str, Enum):
    """Types of resources that can be audited."""
    ORGANIZATION = "organization"
    MEMBER = "member"
    INVITE = "invite"
    CONTENT = "content"
    BRAND_PROFILE = "brand_profile"
    TEMPLATE = "template"
    SETTINGS = "settings"
    BILLING = "billing"
    API_KEY = "api_key"
    SESSION = "session"


# =============================================================================
# Organization Models
# =============================================================================


class OrganizationSettings(BaseModel):
    """
    Organization-level settings.

    Settings are stored as JSONB in the database for flexibility.
    """
    default_brand_profile_id: Optional[str] = None
    content_approval_required: bool = False
    sso_enabled: bool = False
    allowed_domains: List[str] = Field(default_factory=list)
    max_members: int = 5
    features: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class OrganizationBase(BaseModel):
    """Base organization model with common fields."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Organization display name"
    )
    slug: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="URL-friendly unique identifier"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional organization description"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format: lowercase alphanumeric with hyphens."""
        v = v.lower().strip()
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", v):
            raise ValueError(
                "Slug must be lowercase alphanumeric with hyphens, "
                "starting and ending with alphanumeric characters"
            )
        if "--" in v:
            raise ValueError("Slug cannot contain consecutive hyphens")
        return v


class OrganizationCreate(OrganizationBase):
    """Request model for creating an organization."""
    plan_tier: OrganizationPlanTier = OrganizationPlanTier.FREE


class OrganizationUpdate(BaseModel):
    """Request model for updating an organization."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    settings: Optional[OrganizationSettings] = None
    logo_url: Optional[str] = Field(default=None, max_length=500)
    website_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator("logo_url", "website_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format."""
        if v is None:
            return None
        v = v.strip()
        if v and not re.match(r"^https?://", v):
            raise ValueError("URL must start with http:// or https://")
        return v


class Organization(OrganizationBase):
    """
    Full organization model with all fields.

    Represents an organization/workspace in the system.
    """
    id: str = Field(..., description="Unique identifier (UUID)")
    plan_tier: OrganizationPlanTier = OrganizationPlanTier.FREE
    settings: OrganizationSettings = Field(default_factory=OrganizationSettings)

    # Billing
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

    # Quotas
    monthly_generation_limit: int = 100
    current_month_usage: int = 0
    quota_reset_date: datetime

    # Metadata
    logo_url: Optional[str] = None
    website_url: Optional[str] = None

    # Status
    is_active: bool = True

    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: str

    model_config = ConfigDict(from_attributes=True)


class OrganizationSummary(BaseModel):
    """
    Summary organization model for list views.

    Contains only essential fields for performance.
    """
    id: str
    name: str
    slug: str
    plan_tier: OrganizationPlanTier
    role: OrganizationRole
    member_count: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Organization Member Models
# =============================================================================


class OrganizationMemberBase(BaseModel):
    """Base member model."""
    role: OrganizationRole = OrganizationRole.VIEWER


class OrganizationMemberCreate(OrganizationMemberBase):
    """Request model for adding a member directly."""
    user_id: str = Field(..., description="User identifier to add")


class OrganizationMemberUpdate(BaseModel):
    """Request model for updating a member's role."""
    role: OrganizationRole


class OrganizationMember(OrganizationMemberBase):
    """
    Full organization member model.

    Represents a user's membership in an organization.
    """
    id: str = Field(..., description="Membership identifier (UUID)")
    organization_id: str
    user_id: str
    invited_by: Optional[str] = None
    invite_accepted_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationMemberDetails(OrganizationMember):
    """
    Extended member model with additional details.

    Used for detailed member views.
    """
    email: Optional[str] = None  # Retrieved from user profile if available
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    last_active_at: Optional[datetime] = None


# =============================================================================
# Organization Invite Models
# =============================================================================


class OrganizationInviteCreate(BaseModel):
    """Request model for creating an invitation."""
    email: str = Field(..., description="Email address to invite")
    role: OrganizationRole = OrganizationRole.VIEWER
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional personal message"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        v = v.lower().strip()
        email_pattern = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email address format")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: OrganizationRole) -> OrganizationRole:
        """Prevent inviting as owner."""
        if v == OrganizationRole.OWNER:
            raise ValueError("Cannot invite users as owner. Use ownership transfer instead.")
        return v


class OrganizationInvite(BaseModel):
    """
    Full organization invite model.

    Represents a pending invitation to join an organization.
    """
    id: str = Field(..., description="Invite identifier (UUID)")
    organization_id: str
    email: str
    role: OrganizationRole
    invited_by: str
    message: Optional[str] = None
    expires_at: datetime
    status: InviteStatus = InviteStatus.PENDING
    resend_count: int = 0
    last_resent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Populated on response only
    organization_name: Optional[str] = None
    inviter_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InviteAcceptRequest(BaseModel):
    """Request model for accepting an invitation."""
    token: str = Field(..., min_length=20, description="Invitation token")


class InviteAcceptResponse(BaseModel):
    """Response model for accepted invitation."""
    success: bool
    organization_id: str
    organization_name: str
    role: OrganizationRole
    member_id: str


# =============================================================================
# Audit Log Models
# =============================================================================


class AuditLogEntry(BaseModel):
    """
    Audit log entry model.

    Represents a single audit event for compliance and security monitoring.
    """
    id: str = Field(..., description="Audit log entry ID (UUID)")
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogCreate(BaseModel):
    """Internal model for creating audit log entries."""
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class AuditLogQuery(BaseModel):
    """Query parameters for filtering audit logs."""
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


# =============================================================================
# Plan and Quota Models
# =============================================================================


class OrganizationPlanLimits(BaseModel):
    """Plan limits configuration."""
    plan_tier: OrganizationPlanTier
    max_members: int
    monthly_generation_limit: int
    features: Dict[str, bool] = Field(default_factory=dict)
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    description: Optional[str] = None


class OrganizationQuotaStatus(BaseModel):
    """Organization quota status."""
    organization_id: str
    has_quota: bool
    current_usage: int
    monthly_limit: int
    remaining: int
    reset_date: datetime
    percentage_used: float = Field(default=0.0)


# =============================================================================
# Response Models
# =============================================================================


class OrganizationResponse(BaseModel):
    """API response for organization operations."""
    success: bool = True
    organization: Organization


class OrganizationsListResponse(BaseModel):
    """API response for listing organizations."""
    success: bool = True
    organizations: List[OrganizationSummary]
    total: int


class OrganizationMembersResponse(BaseModel):
    """API response for listing organization members."""
    success: bool = True
    members: List[OrganizationMember]
    total: int


class OrganizationInvitesResponse(BaseModel):
    """API response for listing organization invites."""
    success: bool = True
    invites: List[OrganizationInvite]
    total: int


class AuditLogsResponse(BaseModel):
    """API response for listing audit logs."""
    success: bool = True
    logs: List[AuditLogEntry]
    total: int
    has_more: bool = False


# =============================================================================
# Permission Constants
# =============================================================================


# Role hierarchy for permission inheritance
ROLE_HIERARCHY: Dict[OrganizationRole, int] = {
    OrganizationRole.OWNER: 4,
    OrganizationRole.ADMIN: 3,
    OrganizationRole.EDITOR: 2,
    OrganizationRole.VIEWER: 1,
}


def is_role_higher_or_equal(role1: OrganizationRole, role2: OrganizationRole) -> bool:
    """
    Check if role1 is higher or equal to role2 in the hierarchy.

    Args:
        role1: The role to check.
        role2: The role to compare against.

    Returns:
        True if role1 >= role2 in the hierarchy.
    """
    return ROLE_HIERARCHY[role1] >= ROLE_HIERARCHY[role2]


def can_manage_role(manager_role: OrganizationRole, target_role: OrganizationRole) -> bool:
    """
    Check if a manager can modify a target role.

    Managers can only modify roles below their own level.

    Args:
        manager_role: The role of the user attempting the action.
        target_role: The role being modified.

    Returns:
        True if the manager can modify the target role.
    """
    # Owner can manage all except other owners
    if manager_role == OrganizationRole.OWNER:
        return True

    # Admin can manage editors and viewers
    if manager_role == OrganizationRole.ADMIN:
        return target_role in (OrganizationRole.EDITOR, OrganizationRole.VIEWER)

    return False
