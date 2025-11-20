"""
Shared Stripe mock setup for tests.

Multiple test modules need to mock Stripe consistently. Keeping a single shared
mock avoids cross-test interference from competing `sys.modules["stripe"]`
assignments.
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock

mock_stripe = MagicMock()
mock_stripe.api_key = None
mock_stripe.Customer = MagicMock()
mock_stripe.Subscription = MagicMock()
mock_stripe.checkout = MagicMock()
mock_stripe.billing_portal = MagicMock()
mock_stripe.Webhook = MagicMock()


class MockSignatureVerificationError(Exception):
    pass


class MockStripeError(Exception):
    pass


mock_stripe.error = MagicMock()
mock_stripe.error.SignatureVerificationError = MockSignatureVerificationError
mock_stripe.error.StripeError = MockStripeError

# Reload the service module at most once per process. importlib.reload creates a
# fresh stripe_service singleton; doing it more than once would leave different
# test modules bound to different instances and break patch.object()-based tests.
_service_reloaded = False


def install_mock_stripe() -> None:
    """Install the shared Stripe mock into sys.modules.

    If the Stripe service module was already imported (e.g. by an earlier test
    that transitively imports it while the real ``stripe`` was still in
    sys.modules), reload it once so it rebinds to the mock. Without this, the
    mock is silently ignored under test orderings where the service is imported
    first, causing webhook/signature tests to fail intermittently.
    """
    global _service_reloaded
    sys.modules["stripe"] = mock_stripe
    sys.modules["stripe.error"] = mock_stripe.error

    already_imported = sys.modules.get("src.payments.stripe_service")
    if already_imported is not None and not _service_reloaded:
        importlib.reload(already_imported)
        _service_reloaded = True
