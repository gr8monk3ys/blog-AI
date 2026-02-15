"""
Shared Stripe mock setup for tests.

Multiple test modules need to mock Stripe consistently. Keeping a single shared
mock avoids cross-test interference from competing `sys.modules["stripe"]`
assignments.
"""

from __future__ import annotations

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


def install_mock_stripe() -> None:
    """Install the shared Stripe mock into sys.modules."""
    sys.modules["stripe"] = mock_stripe
    sys.modules["stripe.error"] = mock_stripe.error

