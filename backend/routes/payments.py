"""
Payment & credit routes (Dodo Payments — digital credit packs only).

  GET  /credits                 -> current balance + purchasable packs
  POST /credits/checkout        -> create a Dodo hosted checkout session for a pack
  POST /webhooks/dodo           -> Dodo webhook: grant credits on payment.succeeded

Dodo is the Merchant of Record and handles global tax/VAT. Physical prints never
touch this rail (prohibited MoR category) — see config.py PRINTS_ENABLED.
"""
import os

from flask import Blueprint, request, jsonify, g

from backend.auth_middleware import require_auth
from backend.config import credits as credits_cfg
from backend.db import credits as credits_db
from backend.services import dodo_client

payments_bp = Blueprint("payments", __name__)

_SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://pet-to.com")


def _attr(obj, name, default=None):
    """Read an attribute from a pydantic model OR a key from a dict."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@payments_bp.get("/credits")
@require_auth
def get_credits():
    return jsonify({
        "credits": credits_db.get_credits(g.uid),
        "packs": credits_cfg.public_catalog(),
        "payments_enabled": dodo_client.is_configured(),
    })


@payments_bp.post("/credits/checkout")
@require_auth
def create_checkout():
    if not dodo_client.is_configured():
        return jsonify({"error": "Payments are not available yet.", "code": "payments_disabled"}), 503

    body = request.get_json(silent=True) or {}
    pack_id = body.get("pack_id")
    pack = credits_cfg.get_pack(pack_id)
    if not pack:
        return jsonify({"error": "Unknown credit pack"}), 400

    product_id = credits_cfg.get_product_id(pack_id)
    if not product_id:
        return jsonify({"error": "This pack is not configured for sale yet.", "code": "product_unconfigured"}), 503

    return_url = body.get("return_url") or f"{_SITE_BASE_URL}/?checkout=success"

    try:
        session = dodo_client.create_checkout_session(
            product_id=product_id,
            email=g.user_email or "",
            name=g.user_email or "Customer",
            return_url=return_url,
            metadata={
                "uid": g.uid,
                "pack_id": pack_id,
                "credits": str(pack["credits"]),
            },
        )
    except Exception as exc:
        print(f"[dodo] checkout creation failed: {exc}")
        return jsonify({"error": "Could not start checkout. Please try again."}), 502

    if not session.get("checkout_url"):
        return jsonify({"error": "Checkout session did not return a URL."}), 502
    return jsonify(session)


@payments_bp.post("/webhooks/dodo")
def dodo_webhook():
    """Verify the Dodo webhook signature and grant credits on successful payment."""
    if not dodo_client.is_configured():
        return "", 503

    payload = request.get_data()  # raw bytes — required for signature verification
    headers = {
        "webhook-id": request.headers.get("webhook-id", ""),
        "webhook-signature": request.headers.get("webhook-signature", ""),
        "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
    }

    try:
        event = dodo_client.unwrap_webhook(payload, headers)
    except Exception as exc:
        print(f"[dodo] webhook verification failed: {exc}")
        return "Invalid signature", 400

    event_type = _attr(event, "type")
    data = _attr(event, "data")

    # Only one-time payments matter for credit packs.
    if event_type == "payment.succeeded":
        metadata = _attr(data, "metadata", {}) or {}
        uid = _attr(metadata, "uid")
        payment_id = _attr(data, "payment_id") or _attr(data, "id")
        try:
            credits = int(_attr(metadata, "credits", 0) or 0)
        except (TypeError, ValueError):
            credits = 0

        if uid and payment_id and credits > 0:
            try:
                new_balance = credits_db.add_credits(uid, credits, str(payment_id))
                print(f"[dodo] +{credits} credits for {uid} (payment {payment_id}) -> {new_balance}")
            except Exception as exc:
                # Return 500 so Dodo retries delivery (add_credits is idempotent).
                print(f"[dodo] failed to grant credits for payment {payment_id}: {exc}")
                return "Error granting credits", 500
        else:
            print(f"[dodo] payment.succeeded missing uid/credits metadata (payment {payment_id})")

    return "", 200
