import os
from pathlib import Path

import requests as http_client
from flask import Blueprint, request, jsonify, g, send_from_directory
from google.cloud import firestore

from backend.auth_middleware import require_auth
from backend.config.prices import FRAME_CATALOG, convert_price
from backend.firebase import get_db
from backend.storage.r2 import public_url as r2_public_url

orders_bp = Blueprint("orders", __name__)

_PREVIEW_DIR = Path(__file__).parent.parent / "config" / "config_preview_images"


def _send_order_confirmation(order_data: dict, order_id: str, user_email: str, lang: str = "en") -> None:
    """Send an order confirmation email via SendGrid when configured."""
    api_key = os.environ.get("SEND_GRID_API_KEY")
    if not api_key:
        print("[email] SEND_GRID_API_KEY not set - skipping confirmation email")
        return

    if not user_email:
        print(f"[email] No email for order {order_id} - skipping")
        return

    shipping = order_data.get("shipping", {})
    first_name = shipping.get("firstName", "")
    items = order_data.get("items", [])
    is_ja = lang == "ja"

    items_html = "".join(
        f"<tr><td style='padding:4px 8px'>{item.get('template_key', '')}</td>"
        f"<td style='padding:4px 8px'>{item.get('category', '')} · {item.get('size', '')}"
        f"{' · ' + item.get('color', '') if item.get('color') else ''}</td>"
        f"<td style='padding:4px 8px;text-align:center'>×{item.get('quantity', 1)}</td></tr>"
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

    if is_ja:
        heading = f"{first_name}様、ご注文ありがとうございます。"
        order_label = "注文ID"
        items_label = "ご注文内容"
        col_portrait = "ポートレート"
        col_details = "詳細"
        col_qty = "数量"
        shipping_label = "配送先"
        delivery_msg = "ご注文を受け付けました。発送までの詳細は追ってご案内します。"
        contact_msg = "ご不明な点は <a href='mailto:contact@nakamaai.co'>contact@nakamaai.co</a> までお問い合わせください。"
        subject = f"ご注文受付 - 注文 {order_id}"
    else:
        heading = f"Thanks for your order, {first_name}!"
        order_label = "Order ID"
        items_label = "Items ordered"
        col_portrait = "Portrait"
        col_details = "Details"
        col_qty = "Qty"
        shipping_label = "Shipping to"
        delivery_msg = "Your order has been received. We will follow up with fulfillment details shortly."
        contact_msg = "Questions? Contact us at <a href='mailto:contact@nakamaai.co'>contact@nakamaai.co</a>."
        subject = f"Order received - Order {order_id}"

    html = f"""
<html><body style="font-family:sans-serif;color:#1a1a1a;max-width:580px;margin:auto;padding:24px">
  <h2 style="font-size:1.25rem;margin-bottom:4px">{heading}</h2>
  <p style="color:#666;margin-top:0">{order_label}: <code>{order_id}</code></p>

  <h3 style="font-size:0.95rem;margin-bottom:8px">{items_label}</h3>
  <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
    <thead>
      <tr style="background:#f5f0e8">
        <th style="padding:4px 8px;text-align:left">{col_portrait}</th>
        <th style="padding:4px 8px;text-align:left">{col_details}</th>
        <th style="padding:4px 8px;text-align:center">{col_qty}</th>
      </tr>
    </thead>
    <tbody>{items_html}</tbody>
  </table>

  <h3 style="font-size:0.95rem;margin-top:20px;margin-bottom:4px">{shipping_label}</h3>
  <p style="font-size:0.9rem;color:#444;margin:0">{address_str}</p>

  <p style="margin-top:20px;font-size:0.9rem;color:#444;line-height:1.6">{delivery_msg}</p>

  <p style="font-size:0.85rem;color:#888;margin-top:20px">{contact_msg}</p>
</body></html>
"""

    payload = {
        "personalizations": [{"to": [{"email": user_email}]}],
        "from": {"email": "noreply@pet-to.com", "name": "Nakama AI"},
        "subject": subject,
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
        print(f"[email] Failed to send order confirmation to {user_email}: {exc}")

@orders_bp.get("/geo")
def detect_geo():
    """Return the caller's country code for region-based pricing.

    Checks Cloudflare's ``CF-IPCountry`` header first (free, no API call).
    Falls back to a lightweight free IP-API lookup when not behind Cloudflare.
    """
    country = request.headers.get("CF-IPCountry", "").upper()
    if not country or country == "XX":
        # Fallback: try ip-api.com (free for non-commercial / low-volume)
        try:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            if ip:
                ip = ip.split(",")[0].strip()
            resp = http_client.get(
                f"http://ip-api.com/json/{ip}?fields=countryCode",
                timeout=3,
            )
            if resp.status_code == 200:
                country = resp.json().get("countryCode", "UNKNOWN")
            else:
                country = "UNKNOWN"
        except Exception:
            country = "UNKNOWN"
    if not country or country in {"UNKNOWN", "XX"}:
        return jsonify({"error": "Unable to determine country"}), 503
    return jsonify({"country": country})


@orders_bp.get("/orders/catalog/images/<path:filename>")
def serve_catalog_image(filename: str):
    """Serve frame preview images from the config directory."""
    return send_from_directory(_PREVIEW_DIR, filename)


@orders_bp.get("/orders/catalog")
def get_catalog():
    """Return the full frame catalog for the order flow UI (no auth required).

    Accepts optional ``?currency=INR|JPY|USD`` to return prices converted from
    the base JPY values.  Defaults to JPY when omitted.
    """
    currency = request.args.get("currency", "JPY").upper()
    if currency not in ("JPY", "INR", "USD"):
        currency = "JPY"

    categories = []
    for name, cat in FRAME_CATALOG.items():
        variants = [
            {
                "color": v["color"],
                "preview_img_landscape": r2_public_url(v["preview_img_landscape"]),
                "preview_img_portrait": r2_public_url(v["preview_img_portrait"]),
            }
            for v in cat.get("variants", [])
        ]
        sizes = {
            size_key: {"price": convert_price(size_data.get("price", 0), currency)}
            for size_key, size_data in cat.get("sizes", {}).items()
        }
        categories.append({
            "name": name,
            "overlay_inset": cat.get("overlay_inset", 10),
            "variants": variants,
            "sizes": sizes,
        })
    return jsonify({"categories": categories, "currency": currency})


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
            "items": items,
            "shipping": data.get("shipping", {}),
            "notes": data.get("notes", ""),
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
        status = data.get("status", "draft")
        submitted_at = data.get("submitted_at") or (updated_at if status == "submitted" else None)
        results.append(
            {
                "id": doc.id,
                "items": data.get("items", []),
                "shipping": data.get("shipping", {}),
                "notes": data.get("notes", ""),
                "status": status,
                "created_at": created_at.isoformat() if created_at else None,
                "submitted_at": submitted_at.isoformat() if submitted_at else None,
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


@orders_bp.post("/orders/<order_id>/submit")
@require_auth
def submit_order(order_id: str):
    db = get_db()
    doc_ref = db.collection("orders").document(order_id)
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({"error": "Order not found"}), 404

    data = doc.to_dict()
    if data.get("uid") != g.uid:
        return jsonify({"error": "Forbidden"}), 403

    items = data.get("items", [])
    if not items:
        return jsonify({"error": "No items provided"}), 400

    shipping = data.get("shipping", {})
    required_fields = ("firstName", "lastName", "email", "addressLine1", "city", "postCode")
    missing_fields = [field for field in required_fields if not str(shipping.get(field, "")).strip()]
    if missing_fields:
        return jsonify({"error": "Missing required shipping details"}), 400

    doc_ref.update({
        "status": "submitted",
        "submitted_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })

    body = request.get_json(silent=True) or {}
    lang = body.get("lang", "en")
    recipient = shipping.get("email") or data.get("user_email") or g.user_email
    _send_order_confirmation(data, order_id, recipient, lang)

    return jsonify({"success": True})
