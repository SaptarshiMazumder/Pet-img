"""
Payment provider factory.

Set the PAYMENT_PROVIDER environment variable to select a provider:

    PAYMENT_PROVIDER=komoju    → KomojuProvider (hosted checkout page, redirect flow)
    PAYMENT_PROVIDER=razorpay  → RazorpayProvider (client-side modal, frontend must use Razorpay.js)

If PAYMENT_PROVIDER is unset or unrecognised, get_provider() returns None and the
checkout endpoint will respond with a 503 payment_not_configured error.
"""

import os

from .base import PaymentProvider
from .komoju import KomojuProvider
from .razorpay import RazorpayProvider

_PROVIDERS: dict[str, type[PaymentProvider]] = {
    "komoju": KomojuProvider,
    "razorpay": RazorpayProvider,
}


def get_provider() -> PaymentProvider | None:
    """Return the configured provider instance, or None if not configured."""
    name = os.environ.get("PAYMENT_PROVIDER", "").strip().lower()
    cls = _PROVIDERS.get(name)
    return cls() if cls else None
