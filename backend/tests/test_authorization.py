"""
Tests for authorization dependencies.

Verifies that:
- Organization-scoped authentication works correctly
- Permission checks enforce RBAC rules
- Quota enforcement blocks over-limit requests
- Feature flags gate features by plan tier
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from src.organizations import (
    AuthorizationContext,
    Permission,
    OrganizationNotFoundError,
)
from src.types.organization import OrganizationPlanTier, OrganizationRole


class TestOrganizationAuthContext:
    """Tests for OrganizationAuthContext class."""

    def test_basic_context_without_org(self):
        """Test context creation without organization."""
        from app.dependencies.authorization import OrganizationAuthContext

        ctx = OrganizationAuthContext(
            user_id="user123",
            organization_id=None,
            role=None,
            is_org_member=False,
        )

        assert ctx.user_id == "user123"
        assert ctx.organization_id is None
        assert ctx.role is None
        assert not ctx.is_org_member

    def test_context_with_org_and_role(self):
        """Test context creation with organization."""
        from app.dependencies.authorization import OrganizationAuthContext

        ctx = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.PRO,
            monthly_limit=1000,
            current_usage=500,
        )

        assert ctx.user_id == "user123"
        assert ctx.organization_id == "org456"
        assert ctx.role == OrganizationRole.EDITOR
        assert ctx.is_org_member
        assert ctx.plan_tier == OrganizationPlanTier.PRO
        assert ctx.remaining_quota == 500
        assert ctx.has_quota

    def test_quota_exceeded(self):
        """Test quota exceeded detection."""
        from app.dependencies.authorization import OrganizationAuthContext

        ctx = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.FREE,
            monthly_limit=100,
            current_usage=100,
        )

        assert ctx.remaining_quota == 0
        assert not ctx.has_quota

    def test_unlimited_quota(self):
        """Test unlimited quota handling."""
        from app.dependencies.authorization import OrganizationAuthContext

        ctx = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.ENTERPRISE,
            monthly_limit=-1,  # Unlimited
            current_usage=10000,
        )

        assert ctx.remaining_quota == float('inf')
        assert ctx.has_quota


class TestPermissionDependencies:
    """Tests for permission-based dependencies."""

    @pytest.mark.asyncio
    async def test_require_content_creation_with_permission(self):
        """Test content creation with proper permission."""
        from app.dependencies.authorization import require_content_creation

        # Create context with content.create permission (EDITOR role has this)
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        # Should return context without raising
        result = await require_content_creation(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_content_creation_without_permission(self):
        """Test content creation without permission."""
        from app.dependencies.authorization import require_content_creation

        # VIEWER role does not have content.create permission
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_content_creation(auth_ctx)

        assert exc_info.value.status_code == 403
        assert "content.create" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_content_access_with_permission(self):
        """Test content view with proper permission."""
        from app.dependencies.authorization import require_content_access

        # All roles have content.view permission
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        result = await require_content_access(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_content_publish_admin_allowed(self):
        """Test content publish requires admin or higher."""
        from app.dependencies.authorization import require_content_publish

        # ADMIN role has content.publish permission
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        result = await require_content_publish(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_content_publish_editor_denied(self):
        """Test content publish denied for editor."""
        from app.dependencies.authorization import require_content_publish

        # EDITOR role does not have content.publish permission
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_content_publish(auth_ctx)

        assert exc_info.value.status_code == 403


class TestBrandPermissions:
    """Tests for brand-related permission dependencies."""

    @pytest.mark.asyncio
    async def test_require_brand_read_all_members(self):
        """Test all org members can view brand profiles."""
        from app.dependencies.authorization import require_brand_read

        # Even VIEWER can view brand profiles
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        result = await require_brand_read(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_brand_write_admin_allowed(self):
        """Test brand management requires admin permission."""
        from app.dependencies.authorization import require_brand_write

        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        result = await require_brand_write(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_brand_write_editor_denied(self):
        """Test brand management denied for editors."""
        from app.dependencies.authorization import require_brand_write

        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_brand_write(auth_ctx)

        assert exc_info.value.status_code == 403


class TestAdminDependencies:
    """Tests for admin-only dependencies."""

    @pytest.mark.asyncio
    async def test_require_admin_with_admin_role(self):
        """Test admin dependency with admin role."""
        from app.dependencies.authorization import require_admin

        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        result = await require_admin(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_admin_with_owner_role(self):
        """Test admin dependency with owner role."""
        from app.dependencies.authorization import require_admin

        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.OWNER,
            is_org_member=True,
        )

        result = await require_admin(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_admin_with_editor_denied(self):
        """Test admin dependency denied for editor."""
        from app.dependencies.authorization import require_admin

        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(auth_ctx)

        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail).lower()


class TestFeatureFlags:
    """Tests for feature flag dependencies."""

    @pytest.mark.asyncio
    async def test_require_feature_allowed(self):
        """Test feature flag with allowed plan tier."""
        from app.dependencies.authorization import require_feature, OrganizationAuthContext

        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.PRO,
        )

        # PRO tier has advanced_analytics
        dependency = require_feature("advanced_analytics")

        result = await dependency(org_auth)
        assert result == org_auth

    @pytest.mark.asyncio
    async def test_require_feature_denied_wrong_tier(self):
        """Test feature flag denied for wrong plan tier."""
        from app.dependencies.authorization import require_feature, OrganizationAuthContext

        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.FREE,
        )

        # FREE tier does not have advanced_analytics
        dependency = require_feature("advanced_analytics")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(org_auth)

        assert exc_info.value.status_code == 403
        assert "FEATURE_NOT_AVAILABLE" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_feature_enterprise_only(self):
        """Test enterprise-only feature."""
        from app.dependencies.authorization import require_feature, OrganizationAuthContext

        # Business tier trying to access enterprise feature
        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.OWNER,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.BUSINESS,
        )

        dependency = require_feature("white_label")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(org_auth)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_feature_no_org_context(self):
        """Test feature flag without organization context."""
        from app.dependencies.authorization import require_feature, OrganizationAuthContext

        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id=None,  # No org
            role=None,
            is_org_member=False,
        )

        dependency = require_feature("advanced_analytics")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(org_auth)

        assert exc_info.value.status_code == 403
        assert "FEATURE_REQUIRES_ORG" in str(exc_info.value.detail)


class TestQuotaEnforcement:
    """Tests for quota enforcement dependencies."""

    @pytest.mark.asyncio
    async def test_get_organization_quota_context_with_quota(self):
        """Test quota context with available quota."""
        from app.dependencies.authorization import (
            get_organization_quota_context,
            OrganizationAuthContext,
        )

        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.PRO,
            monthly_limit=1000,
            current_usage=500,
        )

        result = await get_organization_quota_context(org_auth)
        assert result == org_auth
        assert result.has_quota

    @pytest.mark.asyncio
    async def test_get_organization_quota_context_exceeded(self):
        """Test quota context when quota exceeded."""
        from app.dependencies.authorization import (
            get_organization_quota_context,
            OrganizationAuthContext,
        )

        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.FREE,
            monthly_limit=100,
            current_usage=100,
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_organization_quota_context(org_auth)

        assert exc_info.value.status_code == 429
        assert "QUOTA_EXCEEDED" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_content_generation_quota_success(self):
        """Test content generation with quota and permission."""
        from app.dependencies.authorization import (
            require_content_generation_quota,
            OrganizationAuthContext,
        )

        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.PRO,
            monthly_limit=1000,
            current_usage=500,
        )

        # Mock the quota check
        with patch(
            "app.dependencies.authorization.get_organization_quota_context",
            return_value=org_auth,
        ):
            result = await require_content_generation_quota(org_auth)
            assert result == org_auth

    @pytest.mark.asyncio
    async def test_require_content_generation_quota_no_permission(self):
        """Test content generation denied without permission."""
        from app.dependencies.authorization import (
            require_content_generation_quota,
            OrganizationAuthContext,
        )

        org_auth = OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,  # No content.create permission
            is_org_member=True,
            plan_tier=OrganizationPlanTier.PRO,
            monthly_limit=1000,
            current_usage=500,
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_content_generation_quota(org_auth)

        assert exc_info.value.status_code == 403


class TestRolePermissionMappings:
    """Tests to verify role-permission mappings are correct."""

    def test_owner_has_all_permissions(self):
        """Test owner has comprehensive permissions."""
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.OWNER,
            is_org_member=True,
        )

        assert auth_ctx.has_permission(Permission.ORGANIZATION_DELETE)
        assert auth_ctx.has_permission(Permission.ORGANIZATION_TRANSFER)
        assert auth_ctx.has_permission(Permission.MEMBERS_MANAGE)
        assert auth_ctx.has_permission(Permission.BILLING_MANAGE)
        assert auth_ctx.has_permission(Permission.CONTENT_DELETE_ANY)

    def test_admin_no_destructive_org_permissions(self):
        """Test admin cannot delete/transfer organization."""
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        assert not auth_ctx.has_permission(Permission.ORGANIZATION_DELETE)
        assert not auth_ctx.has_permission(Permission.ORGANIZATION_TRANSFER)
        # But can manage other things
        assert auth_ctx.has_permission(Permission.MEMBERS_MANAGE)
        assert auth_ctx.has_permission(Permission.CONTENT_DELETE_ANY)

    def test_editor_limited_permissions(self):
        """Test editor has limited permissions."""
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        # Can create and edit own content
        assert auth_ctx.has_permission(Permission.CONTENT_CREATE)
        assert auth_ctx.has_permission(Permission.CONTENT_EDIT)
        # Cannot edit others' content or manage members
        assert not auth_ctx.has_permission(Permission.CONTENT_EDIT_ANY)
        assert not auth_ctx.has_permission(Permission.MEMBERS_MANAGE)
        assert not auth_ctx.has_permission(Permission.CONTENT_PUBLISH)

    def test_viewer_read_only(self):
        """Test viewer has read-only permissions."""
        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        # Can view everything
        assert auth_ctx.has_permission(Permission.CONTENT_VIEW)
        assert auth_ctx.has_permission(Permission.BRAND_VIEW)
        assert auth_ctx.has_permission(Permission.TEMPLATES_VIEW)
        # Cannot modify anything
        assert not auth_ctx.has_permission(Permission.CONTENT_CREATE)
        assert not auth_ctx.has_permission(Permission.CONTENT_EDIT)
        assert not auth_ctx.has_permission(Permission.BRAND_MANAGE)


class TestSecurityLogging:
    """Tests for security event logging."""

    @pytest.mark.asyncio
    async def test_authorization_failure_logged(self):
        """Test that authorization failures are logged."""
        from app.dependencies.authorization import require_content_creation

        auth_ctx = AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        with patch("app.dependencies.authorization.log_authorization_failure") as mock_log:
            with pytest.raises(HTTPException):
                await require_content_creation(auth_ctx)

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args.kwargs["user_id"] == "user123"
            assert call_args.kwargs["organization_id"] == "org456"
            assert call_args.kwargs["required_permission"] == Permission.CONTENT_CREATE
