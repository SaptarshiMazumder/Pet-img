"""Komoju payment provider (hosted checkout page)."""

import hashlib
import hmac
import json
import os

import requests as http_client

from .base import PaymentProvider

_API_BASE = "https://komoju.com/api/v1"


class KomojuProvider(PaymentProvider):
    """
    Komoju hosted checkout.

    Required env vars:
        KOMOJU_SECRET_KEY       — secret key (used as Basic-auth username)
        KOMOJU_WEBHOOK_SECRET   — webhook signing secret
    """

    def _secret_key(self) -> str:
        key = os.environ.get("KOMOJU_SECRET_KEY", "")
        if not key:
            raise EnvironmentError("KOMOJU_SECRET_KEY is not set")
        return key

    def _webhook_secret(self) -> str:
        secret = os.environ.get("KOMOJU_WEBHOOK_SECRET", "")
        if not secret:
            raise EnvironmentError("KOMOJU_WEBHOOK_SECRET is not set")
        return secret

    def create_checkout(self, uid: str, price: dict, origin: str) -> dict:
        secret_key = self._secret_key()

        payload = {
            "return_url": origin + "/?recharge=success",
            "cancel_url": origin + "/?recharge=cancel",
            "currency": price["currency"].upper(),
            "amount": price["amount"],
            "payment_types": ["credit_card"],
            "metadata": {
                "uid": uid,
                "credits": str(price["credits"]),
                "currency": price["currency"],
            },
        }

        resp = http_client.post(
            f"{_API_BASE}/sessions",
            auth=(secret_key, ""),
            json=payload,
            timeout=10,
        )

        if not resp.ok:
            raise RuntimeError(f"Komoju session creation failed: {resp.status_code} {resp.text}")

        data = resp.json()
        return {
            "provider": "komoju",
            "url": data["payment_url"],
            "session_id": data["id"],
        }

    def handle_webhook(self, request) -> tuple[str, int] | None:
        webhook_secret = self._webhook_secret()
        payload = request.get_data()

        sig = request.headers.get("X-Komoju-Signature", "")
        expected = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(sig, expected):
            raise PermissionError("Komoju webhook signature mismatch")

        event = json.loads(payload)

        # Only handle completed payments
        if event.get("type") != "payment.captured":
            return None

        resource = event.get("data", {})
        meta = resource.get("metadata", {})
        uid = meta.get("uid")
        credits_add = int(meta.get("credits", 0))

        if not uid or not credits_add:
            raise ValueError("Webhook missing uid or credits in metadata")

        return uid, credits_add
