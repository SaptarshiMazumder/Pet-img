"""
Gelato Print-on-Demand API client.

Requires the environment variable:
    GELATO_API_KEY=your_key_here

Obtain your API key from https://dashboard.gelato.com/account/api-access
"""

import os
import uuid

import requests

GELATO_API_BASE = "https://order.gelatoapis.com"
GELATO_PRODUCT_API_BASE = "https://product.gelatoapis.com"


def _api_key() -> str:
    # key = os.getenv("GELATO_API_KEY")
    key = "e552edbe-b0de-493c-9bc9-4ff1da3385da-d1a22b02-2832-45cf-8b69-b2bd5e788e85:e4bbcd1e-1be2-4cde-820d-758458bf7642"
    if not key:
        raise ValueError(
            "GELATO_API_KEY environment variable is not set. "
            "Add it to your .env file: GELATO_API_KEY=your_key_here"
        )
    return key


def _headers() -> dict:
    return {
        "X-API-KEY": _api_key(),
        "Content-Type": "application/json",
    }


def create_order(
    image_url: str,
    shipping_address: dict,
    product_uid: str,
    quantity: int = 1,
    currency: str = "JPY",
    order_type: str = "draft",
) -> dict:
    """Place a new Gelato print order.

    Args:
        image_url: Publicly accessible URL to the image file to print.
        shipping_address: Gelato shipping address dict (firstName, lastName,
            addressLine1, city, postCode, country, email, etc.).
        product_uid: Gelato product UID string (e.g. framed poster UID).
        quantity: Number of copies to order (default 1).
        currency: ISO 4217 currency code (default 'JPY').

    Returns:
        Parsed JSON response dict from the Gelato Orders API.

    Raises:
        ValueError: If GELATO_API_KEY is not configured.
        requests.HTTPError: If the Gelato API returns a non-2xx response.
    """
    payload = {
        "orderType": order_type,
        "orderReferenceId": str(uuid.uuid4()),
        "customerReferenceId": str(uuid.uuid4()),
        "currency": currency,
        "items": [
            {
                "itemReferenceId": str(uuid.uuid4()),
                "productUid": product_uid,
                "files": [{"type": "default", "url": image_url}],
                "quantity": quantity,
            }
        ],
        "shipmentMethodUid": "standard",
        "shippingAddress": shipping_address,
    }

    response = requests.post(
        f"{GELATO_API_BASE}/v4/orders",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_order(order_id: str) -> dict:
    """Retrieve the status and details of an existing Gelato order.

    Args:
        order_id: The Gelato order ID returned when the order was created.

    Returns:
        Parsed JSON response dict from the Gelato Orders API.

    Raises:
        ValueError: If GELATO_API_KEY is not configured.
        requests.HTTPError: If the Gelato API returns a non-2xx response.
    """
    response = requests.get(
        f"{GELATO_API_BASE}/v4/orders/{order_id}",
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def list_products(catalog_uid: str = "framed-posters") -> dict:
    """List products in a Gelato catalog (useful for discovering product UIDs).

    Args:
        catalog_uid: The catalog identifier (default 'framed-posters').
            Other examples: 'posters', 'canvas', 'photo-books'.

    Returns:
        Parsed JSON response dict from the Gelato Product API.

    Raises:
        ValueError: If GELATO_API_KEY is not configured.
        requests.HTTPError: If the Gelato API returns a non-2xx response.
    """
    response = requests.get(
        f"{GELATO_PRODUCT_API_BASE}/v3/catalogs/{catalog_uid}/products",
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
