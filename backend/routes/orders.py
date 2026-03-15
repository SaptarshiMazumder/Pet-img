from flask import Blueprint, request, jsonify, g
from google.cloud import firestore

from backend.auth_middleware import require_auth
from backend.firebase import get_db

orders_bp = Blueprint("orders", __name__)


@orders_bp.post("/orders")
@require_auth
def create_order():
    data = request.get_json(silent=True) or {}

    items = data.get("items", [])
    if not items:
        return jsonify({"error": "No items provided"}), 400

    db = get_db()
    doc_ref = db.collection("orders").document()
    doc_ref.set(
        {
            "uid": g.uid,
            "items": items,
            "shipping": data.get("shipping", {}),
            "notes": data.get("notes", ""),
            "payment_status": "unpaid",
            "status": "draft",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return jsonify({"order_id": doc_ref.id}), 201


@orders_bp.get("/orders")
@require_auth
def get_orders():
    db = get_db()
    docs = (
        db.collection("orders")
        .where("uid", "==", g.uid)
        .limit(50)
        .stream()
    )

    results = []
    for doc in docs:
        data = doc.to_dict()
        created_at = data.get("created_at")
        results.append(
            {
                "id": doc.id,
                "items": data.get("items", []),
                "shipping": data.get("shipping", {}),
                "notes": data.get("notes", ""),
                "payment_status": data.get("payment_status", "unpaid"),
                "status": data.get("status", "draft"),
                "created_at": created_at.isoformat() if created_at else None,
            }
        )

    results.sort(key=lambda o: o["created_at"] or "", reverse=True)
    return jsonify({"orders": results})


@orders_bp.patch("/orders/<order_id>")
@require_auth
def update_order(order_id):
    db = get_db()
    doc_ref = db.collection("orders").document(order_id)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"error": "Order not found"}), 404

    if doc.to_dict().get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    updates = {"updated_at": firestore.SERVER_TIMESTAMP}

    for field in ("shipping", "notes", "items"):
        if field in data:
            updates[field] = data[field]

    doc_ref.update(updates)
    return jsonify({"success": True})
