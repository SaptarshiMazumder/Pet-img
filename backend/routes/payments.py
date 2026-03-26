import os

import requests as http_client
from flask import Blueprint, g, jsonify, request

from backend.auth_middleware import require_auth
from backend.firebase import get_db

payments_bp = Blueprint("payments", __name__)


def _send_order_confirmation(order_data: dict, order_id: str, user_email: str, lang: str = 'en') -> None:
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
    is_ja = lang == 'ja'

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

    if is_ja:
        heading = f"ご注文ありがとうございます、{first_name}様！"
        order_label = "注文ID"
        items_label = "ご注文内容"
        col_portrait = "ポートレート"
        col_details = "詳細"
        col_qty = "数量"
        shipping_label = "配送先"
        delivery_msg = "ご注文を承りました。<strong>お支払い確認後、10〜14営業日以内</strong>にお届けいたします。江戸風ポートレートの印刷・額装は提携パートナーが行います。"
        contact_msg = "ご不明な点は <a href='mailto:contact@nakamaai.co'>contact@nakamaai.co</a> までお問い合わせください。"
        subject = f"ご注文確認 — 注文 {order_id}"
    else:
        heading = f"Thank you for your order, {first_name}!"
        order_label = "Order ID"
        items_label = "Items ordered"
        col_portrait = "Portrait"
        col_details = "Details"
        col_qty = "Qty"
        shipping_label = "Shipping to"
        delivery_msg = "Your order has been placed and will be delivered within <strong>10–14 days after payment confirmation</strong>. Our fulfillment partner will handle printing and framing of your Edo-era portrait."
        contact_msg = "Questions? Contact us at <a href='mailto:contact@nakamaai.co'>contact@nakamaai.co</a>"
        subject = f"Your pet portrait order has been confirmed — Order {order_id}"

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
        "personalizations": [{"to": [{"email": to_email}]}],
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
        print(f"[email] Failed to send order confirmation to {to_email}: {exc}")


@payments_bp.post("/orders/<order_id>/payment")
@require_auth
def create_payment(order_id: str):
    return jsonify({"error": "Payment is currently disabled"}), 503


@payments_bp.post("/orders/<order_id>/payment/verify")
@require_auth
def verify_payment(order_id: str):
    return jsonify({"error": "Payment is currently disabled"}), 503
