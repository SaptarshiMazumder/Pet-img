"""Razorpay payment provider (client-side modal checkout)."""

import hashlib
import hmac
import json
import os

import requests as http_client

from .base import PaymentProvider

_API_BASE = "https://api.razorpay.com/v1"


class RazorpayProvider(PaymentProvider):
    """
    Razorpay order-based checkout.

    The frontend receives order details and opens the Razorpay.js modal.
    Payment verification happens via the /credits/webhook endpoint.

    Required env vars:
        RAZORPAY_KEY_ID         — publishable key (e.g. rzp_live_...)
        RAZORPAY_KEY_SECRET     — secret key
        RAZORPAY_WEBHOOK_SECRET — webhook signing secret
    """

    def _creds(self) -> tuple[str, str]:
        key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
        if not key_id or not key_secret:
            raise EnvironmentError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set")
        return key_id, key_secret

    def _webhook_secret(self) -> str:
        secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
        if not secret:
            raise EnvironmentError("RAZORPAY_WEBHOOK_SECRET is not set")
        return secret

    def create_checkout(self, uid: str, price: dict, origin: str) -> dict:
        key_id, key_secret = self._creds()

        # Razorpay amounts are always in smallest currency unit
        currency = price["currency"].upper()
        amount = price["amount"]
        # INR uses paise (multiply by 100); JPY is already smallest unit
        zero_decimal = {"JPY", "KRW", "VND"}
        unit_amount = amount if currency in zero_decimal else amount * 100

        payload = {
            "amount": int(unit_amount),
            "currency": currency,
            "receipt": f"credits_{uid[:16]}",
            "notes": {
                "uid": uid,
                "credits": str(price["credits"]),
            },
        }

        resp = http_client.post(
            f"{_API_BASE}/orders",
            auth=(key_id, key_secret),
            json=payload,
            timeout=10,
        )

        if not resp.ok:
            raise RuntimeError(f"Razorpay order creation failed: {resp.status_code} {resp.text}")

        data = resp.json()
        return {
            "provider": "razorpay",
            "order_id": data["id"],
            "key_id": key_id,
            "amount": data["amount"],
            "currency": data["currency"],
            "credits": price["credits"],
        }

    def handle_webhook(self, request) -> tuple[str, int] | None:
        webhook_secret = self._webhook_secret()
        payload = request.get_data()

        sig = request.headers.get("X-Razorpay-Signature", "")
        expected = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(sig, expected):
            raise PermissionError("Razorpay webhook signature mismatch")

        event = json.loads(payload)

        if event.get("event") != "payment.captured":
            return None

        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment.get("notes", {})
        uid = notes.get("uid")
        credits_add = int(notes.get("credits", 0))

        if not uid or not credits_add:
            raise ValueError("Webhook missing uid or credits in notes")

        return uid, credits_add
