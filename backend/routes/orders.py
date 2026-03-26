import os
from pathlib import Path

from flask import Blueprint, request, jsonify, g, send_from_directory
from google.cloud import firestore

from backend.auth_middleware import require_auth
from backend.config.prices import FRAME_CATALOG
from backend.config.prices_india import FRAME_CATALOG_INDIA
from backend.firebase import get_db
from backend.storage.r2 import public_url as r2_public_url

orders_bp = Blueprint("orders", __name__)

_PREVIEW_DIR = Path(__file__).parent.parent / "config" / "config_preview_images"



@orders_bp.get("/orders/catalog/images/<path:filename>")
def serve_catalog_image(filename: str):
    """Serve frame preview images from the config directory."""
    return send_from_directory(_PREVIEW_DIR, filename)


def _catalog_image_url(key: str, region: str) -> str:
    """India frames are served locally; JP frames come from R2."""
    if region == "IN":
        return f"/orders/catalog/images/{key}"
    return r2_public_url(key)


@orders_bp.get("/orders/catalog")
def get_catalog():
    """Return the full frame catalog for the order flow UI (no auth required)."""
    region = request.args.get("region", "JP").upper()
    catalog = FRAME_CATALOG_INDIA if region == "IN" else FRAME_CATALOG
    categories = []
    for name, cat in catalog.items():
        variants = [
            {
                "color": v["color"],
                "preview_img_landscape": _catalog_image_url(v["preview_img_landscape"], region),
                "preview_img_portrait": _catalog_image_url(v["preview_img_portrait"], region),
            }
            for v in cat.get("variants", [])
        ]
        sizes = {
            size_key: {"price": size_data.get("price", 0)}
            for size_key, size_data in cat.get("sizes", {}).items()
        }
        categories.append({
            "name": name,
            "overlay_inset": cat.get("overlay_inset", 10),
            "variants": variants,
            "sizes": sizes,
        })
    return jsonify({"categories": categories})


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
            "user_email": g.user_email,
            "region": data.get("region", "JP"),
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
        updated_at = data.get("updated_at")
        payment_status = data.get("payment_status", "unpaid")
        results.append(
            {
                "id": doc.id,
                "items": data.get("items", []),
                "shipping": data.get("shipping", {}),
                "notes": data.get("notes", ""),
                "payment_status": payment_status,
                "status": data.get("status", "draft"),
                "created_at": created_at.isoformat() if created_at else None,
                "paid_at": updated_at.isoformat() if (payment_status == "paid" and updated_at) else None,
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

    for field in ("shipping", "notes", "items", "region"):
        if field in data:
            updates[field] = data[field]

    doc_ref.update(updates)
    return jsonify({"success": True})
