import os

from flask import Blueprint, g, jsonify, request

from backend.auth_middleware import require_auth
from backend.db import user_credits
from backend.firebase import get_db
from backend.config.credit_recharge_prices_by_region import (
    CREDITS_PER_PACK,
    get_credit_recharge_price_for_country,
)
from backend.stripe_helpers import checkout_unit_amount

try:
    import stripe
except ImportError:
    stripe = None

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
        # strip path
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
    Stripe Checkout for one credit pack (CREDITS_PER_PACK credits).
    Returns { "url": "<stripe hosted checkout url>" }.
    Requires STRIPE_SECRET_KEY. Webhook STRIPE_WEBHOOK_SECRET credits the balance.
    """
    if not stripe or not os.environ.get("STRIPE_SECRET_KEY"):
        return jsonify(
            {"error": "payment_not_configured", "detail": "Set STRIPE_SECRET_KEY on the server."}
        ), 503

    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    country = _country_from_request()
    price = get_credit_recharge_price_for_country(country)
    origin = _frontend_origin()
    unit = checkout_unit_amount(price["amount"], price["currency"])

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": price["currency"].lower(),
                        "product_data": {
                            "name": f"Pet Generator — {CREDITS_PER_PACK} credits",
                            "description": "Credit pack for portrait generations",
                        },
                        "unit_amount": unit,
                    },
                    "quantity": 1,
                }
            ],
            success_url=origin + "/?recharge=success&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=origin + "/?recharge=cancel",
            client_reference_id=g.uid,
            metadata={
                "uid": g.uid,
                "credits": str(CREDITS_PER_PACK),
                "currency": price["currency"],
            },
        )
    except Exception as e:
        return jsonify({"error": "stripe_error", "detail": str(e)}), 502

    return jsonify({"url": session.url})


@credits_bp.post("/stripe-webhook")
def stripe_webhook():
    """Stripe sends raw body; verify signature and add credits once per session."""
    if not stripe or not os.environ.get("STRIPE_SECRET_KEY"):
        return jsonify({"error": "not configured"}), 503

    wh_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not wh_secret:
        return jsonify({"error": "STRIPE_WEBHOOK_SECRET not set"}), 503

    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig, wh_secret)
    except ValueError:
        return jsonify({"error": "invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "invalid signature"}), 400

    if event.get("type") != "checkout.session.completed":
        return jsonify({"received": True}), 200

    obj = event["data"]["object"]
    session_id = obj.get("id")
    meta = obj.get("metadata") or {}
    uid = meta.get("uid")
    credits_add = int(meta.get("credits", CREDITS_PER_PACK))

    if not uid or not session_id:
        return jsonify({"error": "missing metadata"}), 400

    if obj.get("payment_status") != "paid":
        return jsonify({"received": True}), 200

    ref = get_db().collection("stripe_checkout_sessions").document(session_id)
    if ref.get().exists:
        return jsonify({"received": True, "duplicate": True}), 200

    user_credits.add_credits(uid, credits_add)
    ref.set({"uid": uid, "credits_added": credits_add, "credited": True})

    return jsonify({"received": True}), 200


@credits_bp.post("/recharge")
@require_auth
def recharge_credits():
    """Deprecated — use POST /credits/checkout-session."""
    return jsonify({"error": "Use POST /credits/checkout-session"}), 400
