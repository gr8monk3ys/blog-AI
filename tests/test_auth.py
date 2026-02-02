"""
Tests for API key authentication and security.

This module tests the authentication system including:
- API key creation and uniqueness
- API key verification
- API key revocation
- Dev mode safety checks
- FastAPI dependency authentication

These are P0 security tests - critical for production deployment.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Note: Do NOT mock sentry_sdk globally here as it pollutes other test files.
# The auth module does not use sentry_sdk, so no mock is needed.


def get_auth_module():
    """Get the auth module with fresh import for isolation."""
    # Clear cached modules
    modules_to_clear = [
        "app.auth",
        "app.auth.api_key",
    ]
    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]

    import app.auth.api_key as auth_module
    return auth_module


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

        # All keys should be unique
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key2, key3)
        self.assertNotEqual(key1, key3)

        # Keys should be sufficiently long (32 bytes base64 encoded)
        self.assertGreater(len(key1), 30)
        self.assertGreater(len(key2), 30)
        self.assertGreater(len(key3), 30)

    def test_create_key_for_same_user_returns_new_key(self):
        """Creating a key for the same user should replace the old key."""
        key1 = self.store.create_key("user-1")
        key2 = self.store.create_key("user-1")

        # Keys should be different
        self.assertNotEqual(key1, key2)

        # Old key should no longer work
        self.assertIsNone(self.store.verify_key(key1))

        # New key should work
        self.assertEqual(self.store.verify_key(key2), "user-1")


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
        """Verifying a valid API key should return the associated user_id."""
        user_id = "test-user-123"
        api_key = self.store.create_key(user_id)

        result = self.store.verify_key(api_key)

        self.assertEqual(result, user_id)

    def test_verify_key_returns_none_for_invalid_key(self):
        """Verifying an invalid API key should return None."""
        # Create a key for another user
        self.store.create_key("some-user")

        # Try to verify a completely invalid key
        result = self.store.verify_key("invalid-api-key-12345")

        self.assertIsNone(result)

    def test_verify_key_returns_none_for_empty_key(self):
        """Verifying an empty key should return None."""
        result = self.store.verify_key("")
        self.assertIsNone(result)

    def test_verify_key_returns_none_for_similar_key(self):
        """Verifying a key that is similar but not exact should return None."""
        user_id = "test-user"
        api_key = self.store.create_key(user_id)

        # Try with slightly modified key
        modified_key = api_key[:-1] + "X"
        result = self.store.verify_key(modified_key)

        self.assertIsNone(result)

    def test_verify_key_uses_bcrypt_constant_time_comparison(self):
        """Verify that key comparison uses bcrypt (which has constant-time comparison)."""
        user_id = "test-user"
        api_key = self.store.create_key(user_id)

        # Patch bcrypt.checkpw to verify it's being used for constant-time comparison
        with patch.object(
            self.auth_module.bcrypt, "checkpw", return_value=True
        ) as mock_checkpw:
            self.store.verify_key(api_key)
            # bcrypt.checkpw should be called (bcrypt uses constant-time comparison)
            self.assertTrue(mock_checkpw.called)


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


class TestDevModeSafety(unittest.TestCase):
    """Tests for dev mode safety checks to prevent accidental production bypass."""

    def setUp(self):
        """Set up test fixtures."""
        self.auth_module = get_auth_module()
        # Store original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_dev_mode_blocked_in_production(self):
        """DEV_MODE should be blocked when SENTRY_ENVIRONMENT is production."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "SENTRY_ENVIRONMENT": "production",
        }, clear=True):
            # Reimport to pick up new env
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

    def test_dev_mode_blocked_with_production_sentry(self):
        """DEV_MODE should be blocked when SENTRY_ENVIRONMENT indicates production."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "SENTRY_ENVIRONMENT": "PRODUCTION",  # Test case-insensitivity
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertFalse(result)

    def test_dev_mode_blocked_with_https_redirect_enabled(self):
        """DEV_MODE should be blocked when HTTPS redirect is enabled."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "HTTPS_REDIRECT_ENABLED": "true",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertFalse(result)

    def test_dev_mode_blocked_with_non_localhost_origins(self):
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

    def test_dev_mode_allowed_with_no_production_indicators(self):
        """DEV_MODE should be allowed when no production indicators are present."""
        with patch.dict(os.environ, {
            "DEV_MODE": "true",
        }, clear=True):
            auth_module = get_auth_module()
            result = auth_module._is_dev_mode_safe()
            self.assertTrue(result)


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

    async def test_verify_api_key_dependency_raises_401_for_missing_key(self):
        """verify_api_key should raise 401 when API key is missing."""
        from fastapi import HTTPException

        with patch.dict(os.environ, {"DEV_MODE": "false"}, clear=True):
            auth_module = get_auth_module()

            with self.assertRaises(HTTPException) as context:
                await auth_module.verify_api_key(api_key=None)

            self.assertEqual(context.exception.status_code, 401)
            self.assertEqual(context.exception.detail, "Missing API key")

    async def test_verify_api_key_dependency_raises_401_for_invalid_key(self):
        """verify_api_key should raise 401 for an invalid API key."""
        from fastapi import HTTPException

        with patch.dict(os.environ, {"DEV_MODE": "false"}, clear=True):
            auth_module = get_auth_module()

            # Create a store and ensure the invalid key doesn't exist
            auth_module.api_key_store = auth_module.APIKeyStore(
                storage_path=self.temp_storage
            )

            with self.assertRaises(HTTPException) as context:
                await auth_module.verify_api_key(api_key="invalid-key-12345")

            self.assertEqual(context.exception.status_code, 401)
            self.assertEqual(context.exception.detail, "Invalid API key")

    async def test_verify_api_key_dependency_returns_user_id_for_valid_key(self):
        """verify_api_key should return user_id for a valid API key."""
        with patch.dict(os.environ, {"DEV_MODE": "false"}, clear=True):
            auth_module = get_auth_module()

            # Create a store and add a valid key
            store = auth_module.APIKeyStore(storage_path=self.temp_storage)
            auth_module.api_key_store = store
            user_id = "test-user-123"
            api_key = store.create_key(user_id)

            result = await auth_module.verify_api_key(api_key=api_key)

            self.assertEqual(result, user_id)

    async def test_verify_api_key_dependency_returns_dev_user_in_safe_dev_mode(self):
        """verify_api_key should return 'dev_user' in safe dev mode."""
        with patch.dict(os.environ, {"DEV_MODE": "true"}, clear=True):
            auth_module = get_auth_module()
            # Reset the warning flag
            auth_module._dev_mode_warning_logged = False

            result = await auth_module.verify_api_key(api_key=None)

            self.assertEqual(result, "dev_user")

    async def test_verify_api_key_dependency_requires_key_when_dev_mode_blocked(self):
        """verify_api_key should require real key when dev mode is blocked."""
        from fastapi import HTTPException

        with patch.dict(os.environ, {
            "DEV_MODE": "true",
            "STRIPE_SECRET_KEY": "sk_live_production_key",
        }, clear=True):
            auth_module = get_auth_module()

            with self.assertRaises(HTTPException) as context:
                await auth_module.verify_api_key(api_key=None)

            self.assertEqual(context.exception.status_code, 401)


class TestAPIKeyPersistence(unittest.TestCase):
    """Tests for API key storage persistence."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_storage = os.path.join(self.temp_dir, "test_api_keys.json")
        self.auth_module = get_auth_module()

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_storage):
            os.remove(self.temp_storage)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_keys_persist_across_store_instances(self):
        """API keys should persist when creating new store instances."""
        user_id = "persistent-user"

        # Create key with first store instance
        store1 = self.auth_module.APIKeyStore(storage_path=self.temp_storage)
        api_key = store1.create_key(user_id)

        # Create new store instance (simulating app restart)
        store2 = self.auth_module.APIKeyStore(storage_path=self.temp_storage)

        # Key should still be verifiable
        result = store2.verify_key(api_key)
        self.assertEqual(result, user_id)

    def test_user_has_key_method(self):
        """user_has_key should correctly report key existence."""
        store = self.auth_module.APIKeyStore(storage_path=self.temp_storage)

        # Initially no key
        self.assertFalse(store.user_has_key("test-user"))

        # After creation
        store.create_key("test-user")
        self.assertTrue(store.user_has_key("test-user"))

        # After revocation
        store.revoke_key("test-user")
        self.assertFalse(store.user_has_key("test-user"))


class TestGetOrCreateAPIKey(unittest.TestCase):
    """Tests for the get_or_create_key convenience function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_storage = os.path.join(self.temp_dir, "test_api_keys.json")
        self.auth_module = get_auth_module()

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_storage):
            os.remove(self.temp_storage)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_get_or_create_returns_key_for_new_user(self):
        """get_or_create_key should return a key for new users."""
        store = self.auth_module.APIKeyStore(storage_path=self.temp_storage)

        result = store.get_or_create_key("new-user")

        self.assertIsNotNone(result)
        self.assertGreater(len(result), 30)

    def test_get_or_create_returns_none_for_existing_user(self):
        """get_or_create_key should return None for existing users."""
        store = self.auth_module.APIKeyStore(storage_path=self.temp_storage)

        # Create initial key
        store.create_key("existing-user")

        # Second call should return None
        result = store.get_or_create_key("existing-user")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
