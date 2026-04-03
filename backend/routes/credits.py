import json
import os

from flask import Blueprint, g, jsonify, request

from backend.auth_middleware import require_auth
from backend.db import user_credits
from backend.firebase import get_db
from backend.config.credit_recharge_prices_by_region import (
    get_credit_recharge_price_for_country,
)
from backend.payments import get_provider

credits_bp = Blueprint("credits", __name__, url_prefix="/credits")


@credits_bp.get("")
@require_auth
def get_credits():
    """Return the authenticated user's current credit balance and download pricing in credits."""
    balance = user_credits.get_credits(g.uid)
    return jsonify(
        {
            "credits": balance,
            "download_credit_cost": user_credits.DOWNLOAD_CREDIT_COST,
        }
    )


def _frontend_origin() -> str:
    o = request.headers.get("Origin") or request.headers.get("Referer", "")
    if o.startswith("http"):
        from urllib.parse import urlparse
        p = urlparse(o)
        return f"{p.scheme}://{p.netloc}"
    return os.environ.get("FRONTEND_PUBLIC_URL", "http://localhost:4200").rstrip("/")


def _country_from_request() -> str:
    body = request.get_json(silent=True) or {}
    return (
        body.get("country")
        or request.args.get("country")
        or request.headers.get("CF-IPCountry")
        or request.headers.get("X-Country-Code")
        or "US"
    )


@credits_bp.post("/checkout-session")
@require_auth
def create_checkout_session():
    """
    Initiate a credit pack checkout via the configured payment provider.

    Set PAYMENT_PROVIDER=komoju or PAYMENT_PROVIDER=razorpay (plus the provider's
    own env vars) to enable payments. Returns provider-specific JSON:
      - Komoju:   { "provider": "komoju",   "url": "<hosted checkout url>", ... }
      - Razorpay: { "provider": "razorpay", "order_id": "...", "key_id": "...", ... }
    """
    provider = get_provider()
    if provider is None:
        return jsonify(
            {"error": "payment_not_configured", "detail": "Set PAYMENT_PROVIDER on the server."}
        ), 503

    country = _country_from_request()
    price = get_credit_recharge_price_for_country(country)
    origin = _frontend_origin()

    try:
        result = provider.create_checkout(uid=g.uid, price=price, origin=origin)
    except EnvironmentError as e:
        return jsonify({"error": "payment_not_configured", "detail": str(e)}), 503
    except Exception as e:
        return jsonify({"error": "checkout_error", "detail": str(e)}), 502

    return jsonify(result)


@credits_bp.post("/webhook")
def payment_webhook():
    """
    Unified webhook endpoint — delegates to the active payment provider.

    Configure your provider's dashboard to POST to:
        POST /credits/webhook
    """
    provider = get_provider()
    if provider is None:
        return jsonify({"error": "not configured"}), 503

    try:
        result = provider.handle_webhook(request)
    except (ValueError, json.JSONDecodeError):
        return jsonify({"error": "invalid payload"}), 400
    except PermissionError:
        return jsonify({"error": "invalid signature"}), 400
    except Exception as e:
        return jsonify({"error": "webhook_error", "detail": str(e)}), 500

    if result is None:
        # Non-credit event — acknowledge and ignore
        return jsonify({"received": True}), 200

    uid, credits_add = result
    session_id = request.headers.get("X-Komoju-Delivery") or request.get_json(silent=True, force=True).get("id", "")

    # Idempotency: skip if this event was already processed
    if session_id:
        ref = get_db().collection("payment_webhook_events").document(session_id)
        if ref.get().exists:
            return jsonify({"received": True, "duplicate": True}), 200
        user_credits.add_credits(uid, credits_add)
        ref.set({"uid": uid, "credits_added": credits_add, "credited": True})
    else:
        user_credits.add_credits(uid, credits_add)

    return jsonify({"received": True}), 200


@credits_bp.post("/recharge")
@require_auth
def recharge_credits():
    """Deprecated — use POST /credits/checkout-session."""
    return jsonify({"error": "Use POST /credits/checkout-session"}), 400
