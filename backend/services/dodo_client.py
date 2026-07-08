"""
Thin wrapper around the Dodo Payments Python SDK.

Dodo is used as the Merchant of Record for DIGITAL credit-pack purchases only.
The account/keys are created by the merchant; until DODO_PAYMENTS_API_KEY is set
the payment endpoints degrade gracefully (is_configured() == False) so the rest
of the site keeps working and we can ship this code before the account exists.

Environment:
  DODO_PAYMENTS_API_KEY   API (bearer) key from Dodo dashboard
  DODO_WEBHOOK_KEY        Webhook signing secret from Dodo dashboard
  DODO_ENV                "test_mode" (default) or "live_mode"
"""
from __future__ import annotations

import os
import threading

_client = None
_lock = threading.Lock()


def is_configured() -> bool:
    return bool(os.getenv("DODO_PAYMENTS_API_KEY"))


def _get_client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                from dodopayments import DodoPayments

                _client = DodoPayments(
                    bearer_token=os.getenv("DODO_PAYMENTS_API_KEY"),
                    environment=os.getenv("DODO_ENV", "test_mode"),
                )
    return _client


def create_checkout_session(
    *,
    product_id: str,
    email: str,
    name: str,
    return_url: str,
    metadata: dict,
) -> dict:
    """Create a hosted checkout session and return {checkout_url, session_id}."""
    session = _get_client().checkout_sessions.create(
        product_cart=[{"product_id": product_id, "quantity": 1}],
        customer={"email": email, "name": name or email},
        return_url=return_url,
        metadata=metadata,
    )
    return {
        "checkout_url": getattr(session, "checkout_url", None),
        "session_id": getattr(session, "session_id", None),
    }


def unwrap_webhook(payload: bytes, headers: dict):
    """Verify a Dodo webhook (Standard Webhooks spec) and return the event.

    Raises if the signature is invalid.
    """
    return _get_client().webhooks.unwrap(payload, headers=headers)
