import base64
import os

import requests as http_client
from flask import Blueprint, g, jsonify, request

from backend.auth_middleware import require_auth
from backend.config.prices import get_framed_base_cost
from backend.firebase import get_db

payments_bp = Blueprint("payments", __name__)

KOMOJU_API_BASE = "https://komoju.com/api/v1"


def _komoju_headers():
    secret = os.environ["KOMOJU_SECRET_KEY"]
    token = base64.b64encode(f"{secret}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def _send_order_confirmation(order_data: dict, order_id: str, user_email: str) -> None:
    """Send an order confirmation email via SendGrid. Silently skips if API key is not set."""
    api_key = os.environ.get("SEND_GRID_API_KEY")
    if not api_key:
        print("[email] SEND_GRID_API_KEY not set — skipping confirmation email")
        return

    if not user_email:
        print(f"[email] No user email for order {order_id} — skipping")
        return

    to_email = user_email
    shipping = order_data.get("shipping", {})
    print(f"[email] Sending order confirmation for {order_id} to {to_email}")

    first_name = shipping.get("firstName", "")
    items = order_data.get("items", [])

    items_html = "".join(
        f"<tr><td style='padding:4px 8px'>{item.get('template_key','')}</td>"
        f"<td style='padding:4px 8px'>{item.get('category','')} · {item.get('size','')}"
        f"{' · ' + item.get('color','') if item.get('color') else ''}</td>"
        f"<td style='padding:4px 8px;text-align:center'>×{item.get('quantity',1)}</td></tr>"
        for item in items
    )

    address_parts = [
        shipping.get("addressLine1", ""),
        shipping.get("addressLine2", ""),
        shipping.get("city", ""),
        shipping.get("postCode", ""),
        shipping.get("country", ""),
    ]
    address_str = ", ".join(p for p in address_parts if p)

    html = f"""
<html><body style="font-family:sans-serif;color:#1a1a1a;max-width:580px;margin:auto;padding:24px">
  <h2 style="font-size:1.25rem;margin-bottom:4px">Thank you for your order, {first_name}!</h2>
  <p style="color:#666;margin-top:0">Order ID: <code>{order_id}</code></p>

  <h3 style="font-size:0.95rem;margin-bottom:8px">Items ordered</h3>
  <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
    <thead>
      <tr style="background:#f5f0e8">
        <th style="padding:4px 8px;text-align:left">Portrait</th>
        <th style="padding:4px 8px;text-align:left">Details</th>
        <th style="padding:4px 8px;text-align:center">Qty</th>
      </tr>
    </thead>
    <tbody>{items_html}</tbody>
  </table>

  <h3 style="font-size:0.95rem;margin-top:20px;margin-bottom:4px">Shipping to</h3>
  <p style="font-size:0.9rem;color:#444;margin:0">{address_str}</p>

  <p style="margin-top:20px;font-size:0.9rem;color:#444;line-height:1.6">
    Your order has been placed and will be delivered within <strong>10–14 days after payment confirmation</strong>.
    Our fulfillment partner will handle printing and framing of your Edo-era portrait.
  </p>

  <p style="font-size:0.85rem;color:#888;margin-top:20px">
    Questions? Contact us at <a href="mailto:contact@nakamaai.co">contact@nakamaai.co</a>
  </p>
</body></html>
"""

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": "noreply@pet-to.com", "name": "Nakama AI"},
        "subject": f"Your pet portrait order has been confirmed — Order {order_id}",
        "content": [{"type": "text/html", "value": html}],
    }

    try:
        resp = http_client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        if resp.status_code >= 400:
            print(f"[email] SendGrid error {resp.status_code}: {resp.text}")
    except Exception as exc:
        print(f"[email] Failed to send order confirmation to {to_email}: {exc}")


@payments_bp.post("/orders/<order_id>/payment")
@require_auth
def create_payment(order_id: str):
    """Create a Komoju session for this order and return checkout params."""
    db = get_db()
    doc_ref = db.collection("orders").document(order_id)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"error": "Order not found"}), 404

    data = doc.to_dict()
    if data.get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403
    if data.get("payment_status") == "paid":
        return jsonify({"error": "Already paid"}), 400

    items = data.get("items", [])
    if os.environ.get("DEV_PRICE_1YEN"):
        total_jpy = 100 * len(items)
    else:
        total_jpy = sum(
            get_framed_base_cost(item.get("category", ""), item.get("size", ""))
            * item.get("quantity", 1)
            for item in items
        )

    body = request.get_json(silent=True) or {}
    return_url = body.get("return_url", "")

    resp = http_client.post(
        f"{KOMOJU_API_BASE}/sessions",
        headers=_komoju_headers(),
        json={
            "amount": total_jpy,
            "currency": "JPY",
            "default_locale": "ja",
            "return_url": return_url,
            "metadata": {"order_id": order_id},
        },
    )
    resp.raise_for_status()
    session = resp.json()

    doc_ref.update({"komoju_session_id": session["id"]})

    return jsonify({
        "session_id": session["id"],
        "session_url": session["session_url"],
        "amount": total_jpy,
        "total_jpy": total_jpy,
        "currency": "JPY",
    })


@payments_bp.post("/orders/<order_id>/payment/verify")
@require_auth
def verify_payment(order_id: str):
    """Verify Komoju session status and mark order as paid."""
    db = get_db()
    doc_ref = db.collection("orders").document(order_id)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"error": "Order not found"}), 404

    data = doc.to_dict()
    if data.get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403

    session_id = data.get("komoju_session_id")
    if not session_id:
        return jsonify({"error": "No payment session found"}), 400

    resp = http_client.get(
        f"{KOMOJU_API_BASE}/sessions/{session_id}",
        headers=_komoju_headers(),
    )
    if resp.status_code != 200:
        return jsonify({"error": "Failed to retrieve payment session"}), 400

    session = resp.json()
    if session.get("status") != "completed":
        return jsonify({"error": "Payment not completed"}), 400

    payment = session.get("payment") or {}
    komoju_payment_id = payment.get("id", "")

    from google.cloud import firestore
    doc_ref.update({
        "payment_status": "paid",
        "komoju_payment_id": komoju_payment_id,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })

    _send_order_confirmation(data, order_id, g.user_email)

    return jsonify({"success": True})


# ── Razorpay (disabled — kept for reference) ──────────────────────────────────
#
# import hashlib
# import hmac
#
# def _razorpay_client():
#     import razorpay
#     return razorpay.Client(
#         auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_KEY_SECRET"])
#     )
#
# @payments_bp.post("/orders/<order_id>/payment")
# @require_auth
# def create_payment(order_id: str):
#     """Create a Razorpay order for this order and return the checkout params."""
#     ...
#     client = _razorpay_client()
#     rz_order = client.order.create({
#         "amount": total_jpy,  # JPY has no subunits — pass face value directly
#         "currency": "JPY",
#         "receipt": order_id,
#     })
#     return jsonify({
#         "razorpay_order_id": rz_order["id"],
#         "amount": total_jpy,
#         "total_jpy": total_jpy,
#         "currency": "JPY",
#         "key_id": os.environ["RAZORPAY_KEY_ID"],
#     })
#
# @payments_bp.post("/orders/<order_id>/payment/verify")
# @require_auth
# def verify_payment(order_id: str):
#     """Verify Razorpay signature and mark order as paid."""
#     ...
#     rz_order_id = body.get("razorpay_order_id", "")
#     rz_payment_id = body.get("razorpay_payment_id", "")
#     rz_signature = body.get("razorpay_signature", "")
#     key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
#     msg = f"{rz_order_id}|{rz_payment_id}"
#     expected = hmac.new(key_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
#     if not hmac.compare_digest(expected, rz_signature):
#         return jsonify({"error": "Invalid payment signature"}), 400
#     doc_ref.update({
#         "payment_status": "paid",
#         "razorpay_payment_id": rz_payment_id,
#         "razorpay_order_id": rz_order_id,
#         "updated_at": firestore.SERVER_TIMESTAMP,
#     })
#     return jsonify({"success": True})
