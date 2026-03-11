from flask import Blueprint, request, jsonify

import requests as req_lib

from backend.print_on_demand import gelato

print_orders_bp = Blueprint("print_orders", __name__, url_prefix="/print")


@print_orders_bp.post("/order")
def place_order():
    """POST /print/order — place a Gelato print-on-demand order."""
    data = request.get_json(silent=True) or {}

    # Validate required fields
    missing = [f for f in ("image_url", "product_uid", "shipping_address") if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    image_url = data["image_url"]
    product_uid = data["product_uid"]
    shipping_address = data["shipping_address"]
    quantity = int(data.get("quantity", 1))
    currency = data.get("currency", "JPY")
    order_type = data.get("order_type", "draft")

    try:
        gelato_resp = gelato.create_order(
            image_url=image_url,
            shipping_address=shipping_address,
            product_uid=product_uid,
            quantity=quantity,
            currency=currency,
            order_type=order_type,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 500
    except req_lib.HTTPError as exc:
        body = ""
        try:
            body = exc.response.json()
        except Exception:
            body = exc.response.text if exc.response is not None else str(exc)
        return jsonify({"error": "Gelato API error", "detail": body}), 502
    except Exception as exc:
        return jsonify({"error": f"Unexpected error: {exc}"}), 500

    return (
        jsonify(
            {
                "order_id": gelato_resp.get("id", gelato_resp.get("orderId", "")),
                "status": gelato_resp.get("status", ""),
                "gelato_response": gelato_resp,
            }
        ),
        201,
    )


@print_orders_bp.get("/order/<order_id>")
def get_order(order_id: str):
    """GET /print/order/<order_id> — retrieve order status from Gelato."""
    try:
        gelato_resp = gelato.get_order(order_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 500
    except req_lib.HTTPError as exc:
        body = ""
        try:
            body = exc.response.json()
        except Exception:
            body = exc.response.text if exc.response is not None else str(exc)
        return jsonify({"error": "Gelato API error", "detail": body}), 502
    except Exception as exc:
        return jsonify({"error": f"Unexpected error: {exc}"}), 500

    return jsonify(gelato_resp)


@print_orders_bp.get("/products")
def list_products():
    """GET /print/products — list product UIDs from a Gelato catalog."""
    catalog_uid = request.args.get("catalog", "framed-posters")

    try:
        gelato_resp = gelato.list_products(catalog_uid)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 500
    except req_lib.HTTPError as exc:
        body = ""
        try:
            body = exc.response.json()
        except Exception:
            body = exc.response.text if exc.response is not None else str(exc)
        return jsonify({"error": "Gelato API error", "detail": body}), 502
    except Exception as exc:
        return jsonify({"error": f"Unexpected error: {exc}"}), 500

    return jsonify(gelato_resp)
