import hashlib
import hmac
import os

from flask import Blueprint, g, jsonify, request

from backend.auth_middleware import require_auth
from backend.config.prices import get_framed_base_cost
from backend.firebase import get_db

payments_bp = Blueprint("payments", __name__)


def _razorpay_client():
    import razorpay
    return razorpay.Client(
        auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_KEY_SECRET"])
    )


@payments_bp.post("/orders/<order_id>/payment")
@require_auth
def create_payment(order_id: str):
    """Create a Razorpay order for this order and return the checkout params."""
    db = get_db()
    doc = db.collection("orders").document(order_id).get()

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

    client = _razorpay_client()
    rz_order = client.order.create({
        "amount": total_jpy,  # JPY has no subunits — pass face value directly
        "currency": "JPY",
        "receipt": order_id,
    })

    return jsonify({
        "razorpay_order_id": rz_order["id"],
        "amount": total_jpy,
        "total_jpy": total_jpy,
        "currency": "JPY",
        "key_id": os.environ["RAZORPAY_KEY_ID"],
    })


@payments_bp.post("/orders/<order_id>/payment/verify")
@require_auth
def verify_payment(order_id: str):
    """Verify Razorpay signature and mark order as paid."""
    db = get_db()
    doc_ref = db.collection("orders").document(order_id)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"error": "Order not found"}), 404
    if doc.to_dict().get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403

    body = request.get_json(silent=True) or {}
    rz_order_id = body.get("razorpay_order_id", "")
    rz_payment_id = body.get("razorpay_payment_id", "")
    rz_signature = body.get("razorpay_signature", "")

    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    msg = f"{rz_order_id}|{rz_payment_id}"
    expected = hmac.new(key_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, rz_signature):
        return jsonify({"error": "Invalid payment signature"}), 400

    from google.cloud import firestore
    doc_ref.update({
        "payment_status": "paid",
        "razorpay_payment_id": rz_payment_id,
        "razorpay_order_id": rz_order_id,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })

    return jsonify({"success": True})
