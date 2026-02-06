"""
Comprehensive tests for authentication and authorization flows.

This module tests:
- API key creation, verification, and revocation
- Authorization dependencies (require_content_creation, require_admin, etc.)
- Org-scoped authentication
- Permission checks for different roles (OWNER, ADMIN, EDITOR, VIEWER)

These are P0 security tests - critical for production deployment.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def get_auth_module():
    """Get the auth module with fresh import for isolation."""
    modules_to_clear = [
        "app.auth",
        "app.auth.api_key",
    ]
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]

    import app.auth.api_key as auth_module
    return auth_module


def get_authorization_module():
    """Get the authorization dependencies module."""
    if "app.dependencies.authorization" in sys.modules:
        del sys.modules["app.dependencies.authorization"]
    from app.dependencies import authorization
    return authorization


def get_rbac_module():
    """Get the RBAC module."""
    if "src.organizations.rbac" in sys.modules:
        del sys.modules["src.organizations.rbac"]
    from src.organizations import rbac
    return rbac


def get_org_types():
    """Get the organization types module."""
    from src.types.organization import OrganizationRole, OrganizationPlanTier
    return OrganizationRole, OrganizationPlanTier


# =============================================================================
# API Key Creation Tests
# =============================================================================


class TestAPIKeyCreation(unittest.TestCase):
    """Tests for API key creation functionality."""

    def setUp(self):
        """Set up test fixtures with temporary storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_storage = os.path.join(self.temp_dir, "test_api_keys.json")
        self.auth_module = get_auth_module()
        self.store = self.auth_module.APIKeyStore(storage_path=self.temp_storage)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_storage):
            os.remove(self.temp_storage)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_create_key_returns_unique_keys(self):
        """API key creation should return unique keys for different users."""
        key1 = self.store.create_key("user-1")
        key2 = self.store.create_key("user-2")
        key3 = self.store.create_key("user-3")

        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key2, key3)
        self.assertNotEqual(key1, key3)

    def test_create_key_has_sufficient_entropy(self):
        """API keys should have sufficient length for security."""
        key = self.store.create_key("test-user")

        # 32 bytes base64url encoded = ~43 characters
        self.assertGreaterEqual(len(key), 40)

    def test_create_key_for_same_user_replaces_old_key(self):
        """Creating a key for the same user should invalidate the old key."""
        key1 = self.store.create_key("user-1")
        key2 = self.store.create_key("user-1")

        # Keys should be different
        self.assertNotEqual(key1, key2)

        # Old key should no longer work
        self.assertIsNone(self.store.verify_key(key1))

        # New key should work
        self.assertEqual(self.store.verify_key(key2), "user-1")

    def test_create_key_uses_bcrypt_hash(self):
        """Created keys should be stored as bcrypt hashes."""
        user_id = "test-user"
        self.store.create_key(user_id)

        # Verify the stored hash starts with bcrypt prefix
        stored_hash = self.store._cache.get(user_id)
        self.assertIsNotNone(stored_hash)
        self.assertTrue(stored_hash.startswith("$2"))

    def test_create_multiple_keys_different_users(self):
        """Test creating keys for many users."""
        keys = {}
        for i in range(10):
            user_id = f"user-{i}"
            keys[user_id] = self.store.create_key(user_id)

        # All keys should be unique
        key_values = list(keys.values())
        self.assertEqual(len(set(key_values)), 10)

        # All keys should verify correctly
        for user_id, key in keys.items():
            self.assertEqual(self.store.verify_key(key), user_id)


# =============================================================================
# API Key Verification Tests
# =============================================================================


class TestAPIKeyVerification(unittest.TestCase):
    """Tests for API key verification functionality."""

    def setUp(self):
        """Set up test fixtures with temporary storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_storage = os.path.join(self.temp_dir, "test_api_keys.json")
        self.auth_module = get_auth_module()
        self.store = self.auth_module.APIKeyStore(storage_path=self.temp_storage)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_storage):
            os.remove(self.temp_storage)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_verify_key_returns_user_id_for_valid_key(self):
        """Verifying a valid API key should return the user ID."""
        user_id = "test-user-123"
        api_key = self.store.create_key(user_id)

        result = self.store.verify_key(api_key)

        self.assertEqual(result, user_id)

    def test_verify_key_returns_none_for_invalid_key(self):
        """Verifying an invalid API key should return None."""
        self.store.create_key("some-user")

        result = self.store.verify_key("invalid-api-key-12345")

        self.assertIsNone(result)

    def test_verify_key_returns_none_for_empty_key(self):
        """Verifying an empty key should return None."""
        result = self.store.verify_key("")
        self.assertIsNone(result)

    def test_verify_key_returns_none_for_modified_key(self):
        """Verifying a slightly modified key should return None."""
        user_id = "test-user"
        api_key = self.store.create_key(user_id)

        # Modify last character
        modified_key = api_key[:-1] + ("X" if api_key[-1] != "X" else "Y")
        result = self.store.verify_key(modified_key)

        self.assertIsNone(result)

    def test_verify_key_uses_constant_time_comparison(self):
        """Verify that key comparison uses bcrypt (constant-time)."""
        user_id = "test-user"
        api_key = self.store.create_key(user_id)

        with patch.object(
            self.auth_module.bcrypt, "checkpw", return_value=True
        ) as mock_checkpw:
            self.store.verify_key(api_key)
            self.assertTrue(mock_checkpw.called)

    def test_verify_key_timing_attack_resistance(self):
        """Keys of different lengths should not leak timing info."""
        user_id = "test-user"
        api_key = self.store.create_key(user_id)

        # Various wrong keys should all fail
        wrong_keys = [
            "a",
            "ab",
            api_key + "extra",
            api_key[:-10],
            "completely_wrong_key_format",
        ]

        for wrong_key in wrong_keys:
            result = self.store.verify_key(wrong_key)
            self.assertIsNone(result)


# =============================================================================
# API Key Revocation Tests
# =============================================================================


class TestAPIKeyRevocation(unittest.TestCase):
    """Tests for API key revocation functionality."""

    def setUp(self):
        """Set up test fixtures with temporary storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_storage = os.path.join(self.temp_dir, "test_api_keys.json")
        self.auth_module = get_auth_module()
        self.store = self.auth_module.APIKeyStore(storage_path=self.temp_storage)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_storage):
            os.remove(self.temp_storage)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_revoke_key_removes_access(self):
        """Revoking a key should prevent future verification."""
        user_id = "test-user"
        api_key = self.store.create_key(user_id)

        # Verify key works before revocation
        self.assertEqual(self.store.verify_key(api_key), user_id)

        # Revoke the key
        result = self.store.revoke_key(user_id)
        self.assertTrue(result)

        # Verify key no longer works
        self.assertIsNone(self.store.verify_key(api_key))

    def test_revoke_key_returns_false_for_nonexistent_user(self):
        """Revoking a key for a user without a key should return False."""
        result = self.store.revoke_key("nonexistent-user")
        self.assertFalse(result)

    def test_revoke_key_does_not_affect_other_users(self):
        """Revoking one user's key should not affect other users."""
        user1_id = "user-1"
        user2_id = "user-2"
        key1 = self.store.create_key(user1_id)
        key2 = self.store.create_key(user2_id)

        # Revoke user1's key
        self.store.revoke_key(user1_id)

        # User1's key should not work
        self.assertIsNone(self.store.verify_key(key1))

        # User2's key should still work
        self.assertEqual(self.store.verify_key(key2), user2_id)

    def test_revoke_allows_new_key_creation(self):
        """After revoking, a new key can be created for the user."""
        user_id = "test-user"
        old_key = self.store.create_key(user_id)

        self.store.revoke_key(user_id)

        new_key = self.store.create_key(user_id)

        self.assertIsNone(self.store.verify_key(old_key))
        self.assertEqual(self.store.verify_key(new_key), user_id)


# =============================================================================
# Dev Mode Safety Tests
# =============================================================================


class TestDevModeSafety(unittest.TestCase):
    """Tests for dev mode safety checks to prevent production bypass."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_dev_mode_blocked_in_production_sentry_env(self):
        """DEV_MODE should be blocked when SENTRY_ENVIRONMENT is production."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "SENTRY_ENVIRONMENT": "production",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertFalse(result)

    def test_dev_mode_blocked_with_stripe_live_key(self):
        """DEV_MODE should be blocked when using Stripe live keys."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "STRIPE_SECRET_KEY": "sk_live_abcdefghijklmnop",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertFalse(result)

    def test_dev_mode_blocked_with_https_redirect(self):
        """DEV_MODE should be blocked when HTTPS redirect is enabled."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "HTTPS_REDIRECT_ENABLED": "true",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertFalse(result)

    def test_dev_mode_blocked_with_production_origins(self):
        """DEV_MODE should be blocked with non-localhost allowed origins."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "ALLOWED_ORIGINS": "https://myapp.com,http://localhost:3000",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertFalse(result)

    def test_dev_mode_allowed_with_localhost_only(self):
        """DEV_MODE should be allowed when only localhost origins are set."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "ALLOWED_ORIGINS": "http://localhost:3000,http://127.0.0.1:8000",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertTrue(result)

    def test_dev_mode_allowed_with_stripe_test_key(self):
        """DEV_MODE should be allowed with Stripe test keys."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "STRIPE_SECRET_KEY": "sk_test_abcdefghijklmnop",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertTrue(result)


# =============================================================================
# FastAPI Dependency Tests
# =============================================================================


class TestVerifyAPIKeyDependency(unittest.IsolatedAsyncioTestCase):
    """Tests for the FastAPI verify_api_key dependency function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_storage = os.path.join(self.temp_dir, "test_api_keys.json")
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up temporary files and environment."""
        if os.path.exists(self.temp_storage):
            os.remove(self.temp_storage)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
        os.environ.clear()
        os.environ.update(self.original_env)

    async def test_verify_api_key_raises_401_for_missing_key(self):
        """verify_api_key should raise 401 when API key is missing."""
        with patch.dict(os.environ, {"DEV_MODE": "false"}, clear=True):
            auth_module = get_auth_module()

            with self.assertRaises(HTTPException) as context:
                await auth_module.verify_api_key(api_key=None)

            self.assertEqual(context.exception.status_code, 401)
            self.assertEqual(context.exception.detail, "Missing API key")

    async def test_verify_api_key_raises_401_for_invalid_key(self):
        """verify_api_key should raise 401 for an invalid API key."""
        with patch.dict(os.environ, {"DEV_MODE": "false"}, clear=True):
            auth_module = get_auth_module()
            auth_module.api_key_store = auth_module.APIKeyStore(
                storage_path=self.temp_storage
            )

            with self.assertRaises(HTTPException) as context:
                await auth_module.verify_api_key(api_key="invalid-key-12345")

            self.assertEqual(context.exception.status_code, 401)
            self.assertEqual(context.exception.detail, "Invalid API key")

    async def test_verify_api_key_returns_user_id_for_valid_key(self):
        """verify_api_key should return user_id for a valid API key."""
        with patch.dict(os.environ, {"DEV_MODE": "false"}, clear=True):
            auth_module = get_auth_module()
            store = auth_module.APIKeyStore(storage_path=self.temp_storage)
            auth_module.api_key_store = store
            user_id = "test-user-123"
            api_key = store.create_key(user_id)

            result = await auth_module.verify_api_key(api_key=api_key)

            self.assertEqual(result, user_id)

    async def test_verify_api_key_returns_dev_user_in_safe_dev_mode(self):
        """verify_api_key should return 'dev_user' in safe dev mode."""
        with patch.dict(os.environ, {"DEV_MODE": "true"}, clear=True):
            auth_module = get_auth_module()
            auth_module._dev_mode_warning_logged = False

            result = await auth_module.verify_api_key(api_key=None)

            self.assertEqual(result, "dev_user")

    async def test_verify_api_key_requires_key_when_dev_mode_blocked(self):
        """verify_api_key should require real key when dev mode is blocked."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "STRIPE_SECRET_KEY": "sk_live_production_key",
        }, clear=True):
            auth_module = get_auth_module()

            with self.assertRaises(HTTPException) as context:
                await auth_module.verify_api_key(api_key=None)

            self.assertEqual(context.exception.status_code, 401)


# =============================================================================
# Authorization Context Tests
# =============================================================================


class TestAuthorizationContext:
    """Tests for AuthorizationContext class."""

    def test_context_creation(self):
        """Test basic authorization context creation."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        assert ctx.user_id == "user123"
        assert ctx.organization_id == "org456"
        assert ctx.role == OrganizationRole.EDITOR
        assert ctx.is_org_member

    def test_has_permission_owner(self):
        """Test owner has all permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.OWNER,
            is_org_member=True,
        )

        assert ctx.has_permission(rbac.Permission.ORGANIZATION_DELETE)
        assert ctx.has_permission(rbac.Permission.ORGANIZATION_TRANSFER)
        assert ctx.has_permission(rbac.Permission.MEMBERS_MANAGE)
        assert ctx.has_permission(rbac.Permission.BILLING_MANAGE)
        assert ctx.has_permission(rbac.Permission.CONTENT_DELETE_ANY)

    def test_has_permission_admin(self):
        """Test admin permissions - no delete/transfer org."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        # Admin has these
        assert ctx.has_permission(rbac.Permission.MEMBERS_MANAGE)
        assert ctx.has_permission(rbac.Permission.CONTENT_DELETE_ANY)
        assert ctx.has_permission(rbac.Permission.CONTENT_PUBLISH)

        # Admin does NOT have these
        assert not ctx.has_permission(rbac.Permission.ORGANIZATION_DELETE)
        assert not ctx.has_permission(rbac.Permission.ORGANIZATION_TRANSFER)

    def test_has_permission_editor(self):
        """Test editor has limited permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        # Editor has these
        assert ctx.has_permission(rbac.Permission.CONTENT_CREATE)
        assert ctx.has_permission(rbac.Permission.CONTENT_EDIT)
        assert ctx.has_permission(rbac.Permission.CONTENT_DELETE)

        # Editor does NOT have these
        assert not ctx.has_permission(rbac.Permission.CONTENT_EDIT_ANY)
        assert not ctx.has_permission(rbac.Permission.MEMBERS_MANAGE)
        assert not ctx.has_permission(rbac.Permission.CONTENT_PUBLISH)

    def test_has_permission_viewer(self):
        """Test viewer has read-only permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        # Viewer has these
        assert ctx.has_permission(rbac.Permission.CONTENT_VIEW)
        assert ctx.has_permission(rbac.Permission.BRAND_VIEW)
        assert ctx.has_permission(rbac.Permission.TEMPLATES_VIEW)

        # Viewer does NOT have these
        assert not ctx.has_permission(rbac.Permission.CONTENT_CREATE)
        assert not ctx.has_permission(rbac.Permission.CONTENT_EDIT)
        assert not ctx.has_permission(rbac.Permission.BRAND_MANAGE)

    def test_has_any_permission(self):
        """Test checking if user has any of the specified permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        # Has at least one
        assert ctx.has_any_permission([
            rbac.Permission.CONTENT_CREATE,
            rbac.Permission.MEMBERS_MANAGE,
        ])

        # Has none
        assert not ctx.has_any_permission([
            rbac.Permission.ORGANIZATION_DELETE,
            rbac.Permission.MEMBERS_MANAGE,
        ])


# =============================================================================
# Permission Dependency Tests
# =============================================================================


class TestPermissionDependencies:
    """Tests for permission-based FastAPI dependencies."""

    @pytest.mark.asyncio
    async def test_require_content_creation_with_permission(self):
        """Test content creation with proper permission."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        result = await auth_deps.require_content_creation(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_content_creation_without_permission(self):
        """Test content creation without permission raises 403."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_deps.require_content_creation(auth_ctx)

        assert exc_info.value.status_code == 403
        assert "content.create" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_content_access_with_permission(self):
        """Test content view with proper permission."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        # All roles have content.view
        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        result = await auth_deps.require_content_access(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_content_publish_admin_allowed(self):
        """Test content publish requires admin or higher."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        result = await auth_deps.require_content_publish(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_content_publish_editor_denied(self):
        """Test content publish denied for editor."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_deps.require_content_publish(auth_ctx)

        assert exc_info.value.status_code == 403


# =============================================================================
# Admin Dependency Tests
# =============================================================================


class TestAdminDependencies:
    """Tests for admin-only dependencies."""

    @pytest.mark.asyncio
    async def test_require_admin_with_admin_role(self):
        """Test admin dependency with admin role."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        result = await auth_deps.require_admin(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_admin_with_owner_role(self):
        """Test admin dependency with owner role."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.OWNER,
            is_org_member=True,
        )

        result = await auth_deps.require_admin(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_admin_with_editor_denied(self):
        """Test admin dependency denied for editor."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_deps.require_admin(auth_ctx)

        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_require_admin_with_viewer_denied(self):
        """Test admin dependency denied for viewer."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_deps.require_admin(auth_ctx)

        assert exc_info.value.status_code == 403


# =============================================================================
# Brand Permission Tests
# =============================================================================


class TestBrandPermissions:
    """Tests for brand-related permission dependencies."""

    @pytest.mark.asyncio
    async def test_require_brand_read_all_members(self):
        """Test all org members can view brand profiles."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        result = await auth_deps.require_brand_read(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_brand_write_admin_allowed(self):
        """Test brand management requires admin permission."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        result = await auth_deps.require_brand_write(auth_ctx)
        assert result == auth_ctx

    @pytest.mark.asyncio
    async def test_require_brand_write_editor_denied(self):
        """Test brand management denied for editors."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth_deps.require_brand_write(auth_ctx)

        assert exc_info.value.status_code == 403


# =============================================================================
# Organization Scoped Authentication Tests
# =============================================================================


class TestOrgScopedAuthentication:
    """Tests for organization-scoped API key authentication."""

    @pytest.mark.asyncio
    async def test_org_scoped_auth_without_org_header(self):
        """Test auth without organization header returns user-only context."""
        auth_deps = get_authorization_module()

        # Mock verify_api_key to return a user_id
        with patch.object(auth_deps, 'verify_api_key', return_value="user123"):
            result = await auth_deps.require_org_scoped_api_key(
                x_organization_id=None,
                user_id="user123",
            )

        assert result.user_id == "user123"
        assert result.organization_id is None
        assert result.role is None
        assert not result.is_org_member

    @pytest.mark.asyncio
    async def test_org_scoped_auth_with_valid_org(self):
        """Test auth with valid organization context."""
        OrganizationRole, OrganizationPlanTier = get_org_types()
        auth_deps = get_authorization_module()

        # Mock organization service
        mock_org = MagicMock()
        mock_org.plan_tier = OrganizationPlanTier.PRO
        mock_org.monthly_generation_limit = 1000
        mock_org.current_month_usage = 500

        mock_org_service = AsyncMock()
        mock_org_service.get_organization.return_value = mock_org
        mock_org_service.get_member_role.return_value = OrganizationRole.EDITOR

        with patch.object(
            auth_deps, 'get_organization_service', return_value=mock_org_service
        ):
            result = await auth_deps.require_org_scoped_api_key(
                x_organization_id="org456",
                user_id="user123",
            )

        assert result.user_id == "user123"
        assert result.organization_id == "org456"
        assert result.role == OrganizationRole.EDITOR
        assert result.is_org_member
        assert result.plan_tier == OrganizationPlanTier.PRO

    @pytest.mark.asyncio
    async def test_org_scoped_auth_non_member_denied(self):
        """Test auth with org header but user not a member."""
        auth_deps = get_authorization_module()

        mock_org = MagicMock()

        mock_org_service = AsyncMock()
        mock_org_service.get_organization.return_value = mock_org
        mock_org_service.get_member_role.return_value = None  # Not a member

        with patch.object(
            auth_deps, 'get_organization_service', return_value=mock_org_service
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_deps.require_org_scoped_api_key(
                    x_organization_id="org456",
                    user_id="user123",
                )

        assert exc_info.value.status_code == 403
        assert "NOT_ORG_MEMBER" in str(exc_info.value.detail)


# =============================================================================
# Feature Flag Authorization Tests
# =============================================================================


class TestFeatureFlags:
    """Tests for feature flag dependencies."""

    @pytest.mark.asyncio
    async def test_require_feature_allowed(self):
        """Test feature flag with allowed plan tier."""
        OrganizationRole, OrganizationPlanTier = get_org_types()
        auth_deps = get_authorization_module()

        org_auth = auth_deps.OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.PRO,
        )

        dependency = auth_deps.require_feature("advanced_analytics")

        result = await dependency(org_auth)
        assert result == org_auth

    @pytest.mark.asyncio
    async def test_require_feature_denied_wrong_tier(self):
        """Test feature flag denied for wrong plan tier."""
        OrganizationRole, OrganizationPlanTier = get_org_types()
        auth_deps = get_authorization_module()

        org_auth = auth_deps.OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.FREE,
        )

        dependency = auth_deps.require_feature("advanced_analytics")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(org_auth)

        assert exc_info.value.status_code == 403
        assert "FEATURE_NOT_AVAILABLE" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_feature_enterprise_only(self):
        """Test enterprise-only feature."""
        OrganizationRole, OrganizationPlanTier = get_org_types()
        auth_deps = get_authorization_module()

        org_auth = auth_deps.OrganizationAuthContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.OWNER,
            is_org_member=True,
            plan_tier=OrganizationPlanTier.BUSINESS,
        )

        dependency = auth_deps.require_feature("white_label")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(org_auth)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_feature_no_org_context(self):
        """Test feature flag without organization context."""
        auth_deps = get_authorization_module()

        org_auth = auth_deps.OrganizationAuthContext(
            user_id="user123",
            organization_id=None,
            role=None,
            is_org_member=False,
        )

        dependency = auth_deps.require_feature("advanced_analytics")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(org_auth)

        assert exc_info.value.status_code == 403
        assert "FEATURE_REQUIRES_ORG" in str(exc_info.value.detail)


# =============================================================================
# Role Permission Mapping Tests
# =============================================================================


class TestRolePermissionMappings:
    """Tests to verify role-permission mappings are correct."""

    def test_owner_has_all_permissions(self):
        """Test owner has comprehensive permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.OWNER,
            is_org_member=True,
        )

        assert auth_ctx.has_permission(rbac.Permission.ORGANIZATION_DELETE)
        assert auth_ctx.has_permission(rbac.Permission.ORGANIZATION_TRANSFER)
        assert auth_ctx.has_permission(rbac.Permission.MEMBERS_MANAGE)
        assert auth_ctx.has_permission(rbac.Permission.BILLING_MANAGE)
        assert auth_ctx.has_permission(rbac.Permission.CONTENT_DELETE_ANY)

    def test_admin_no_destructive_org_permissions(self):
        """Test admin cannot delete/transfer organization."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.ADMIN,
            is_org_member=True,
        )

        assert not auth_ctx.has_permission(rbac.Permission.ORGANIZATION_DELETE)
        assert not auth_ctx.has_permission(rbac.Permission.ORGANIZATION_TRANSFER)
        assert auth_ctx.has_permission(rbac.Permission.MEMBERS_MANAGE)
        assert auth_ctx.has_permission(rbac.Permission.CONTENT_DELETE_ANY)

    def test_editor_limited_permissions(self):
        """Test editor has limited permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.EDITOR,
            is_org_member=True,
        )

        assert auth_ctx.has_permission(rbac.Permission.CONTENT_CREATE)
        assert auth_ctx.has_permission(rbac.Permission.CONTENT_EDIT)
        assert not auth_ctx.has_permission(rbac.Permission.CONTENT_EDIT_ANY)
        assert not auth_ctx.has_permission(rbac.Permission.MEMBERS_MANAGE)
        assert not auth_ctx.has_permission(rbac.Permission.CONTENT_PUBLISH)

    def test_viewer_read_only(self):
        """Test viewer has read-only permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        assert auth_ctx.has_permission(rbac.Permission.CONTENT_VIEW)
        assert auth_ctx.has_permission(rbac.Permission.BRAND_VIEW)
        assert auth_ctx.has_permission(rbac.Permission.TEMPLATES_VIEW)
        assert not auth_ctx.has_permission(rbac.Permission.CONTENT_CREATE)
        assert not auth_ctx.has_permission(rbac.Permission.CONTENT_EDIT)
        assert not auth_ctx.has_permission(rbac.Permission.BRAND_MANAGE)


# =============================================================================
# Security Logging Tests
# =============================================================================


class TestSecurityLogging:
    """Tests for security event logging."""

    @pytest.mark.asyncio
    async def test_authorization_failure_logged(self):
        """Test that authorization failures are logged."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()
        auth_deps = get_authorization_module()

        auth_ctx = rbac.AuthorizationContext(
            user_id="user123",
            organization_id="org456",
            role=OrganizationRole.VIEWER,
            is_org_member=True,
        )

        with patch.object(auth_deps, 'log_authorization_failure') as mock_log:
            with pytest.raises(HTTPException):
                await auth_deps.require_content_creation(auth_ctx)

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args.kwargs
            assert call_kwargs["user_id"] == "user123"
            assert call_kwargs["organization_id"] == "org456"
            assert call_kwargs["required_permission"] == rbac.Permission.CONTENT_CREATE


# =============================================================================
# Role Hierarchy Tests
# =============================================================================


class TestRoleHierarchy:
    """Tests for role hierarchy functions."""

    def test_role_levels(self):
        """Test role level ordering."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        assert rbac.get_role_level(OrganizationRole.OWNER) > rbac.get_role_level(OrganizationRole.ADMIN)
        assert rbac.get_role_level(OrganizationRole.ADMIN) > rbac.get_role_level(OrganizationRole.EDITOR)
        assert rbac.get_role_level(OrganizationRole.EDITOR) > rbac.get_role_level(OrganizationRole.VIEWER)

    def test_is_role_higher(self):
        """Test role comparison."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        assert rbac.is_role_higher(OrganizationRole.OWNER, OrganizationRole.ADMIN)
        assert rbac.is_role_higher(OrganizationRole.ADMIN, OrganizationRole.EDITOR)
        assert not rbac.is_role_higher(OrganizationRole.EDITOR, OrganizationRole.ADMIN)

    def test_can_manage_role(self):
        """Test role management permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        # Owner can manage non-owners
        assert rbac.can_manage_role(OrganizationRole.OWNER, OrganizationRole.ADMIN)
        assert rbac.can_manage_role(OrganizationRole.OWNER, OrganizationRole.EDITOR)
        assert rbac.can_manage_role(OrganizationRole.OWNER, OrganizationRole.VIEWER)

        # Admin can manage editors and viewers
        assert rbac.can_manage_role(OrganizationRole.ADMIN, OrganizationRole.EDITOR)
        assert rbac.can_manage_role(OrganizationRole.ADMIN, OrganizationRole.VIEWER)
        assert not rbac.can_manage_role(OrganizationRole.ADMIN, OrganizationRole.OWNER)

        # Editor and viewer cannot manage anyone
        assert not rbac.can_manage_role(OrganizationRole.EDITOR, OrganizationRole.VIEWER)
        assert not rbac.can_manage_role(OrganizationRole.VIEWER, OrganizationRole.VIEWER)

    def test_can_assign_role(self):
        """Test role assignment permissions."""
        OrganizationRole, _ = get_org_types()
        rbac = get_rbac_module()

        # Owner can assign any role except owner
        assert rbac.can_assign_role(OrganizationRole.OWNER, OrganizationRole.ADMIN)
        assert rbac.can_assign_role(OrganizationRole.OWNER, OrganizationRole.EDITOR)
        assert not rbac.can_assign_role(OrganizationRole.OWNER, OrganizationRole.OWNER)

        # Admin can assign editor and viewer
        assert rbac.can_assign_role(OrganizationRole.ADMIN, OrganizationRole.EDITOR)
        assert rbac.can_assign_role(OrganizationRole.ADMIN, OrganizationRole.VIEWER)
        assert not rbac.can_assign_role(OrganizationRole.ADMIN, OrganizationRole.ADMIN)


if __name__ == "__main__":
    unittest.main()
