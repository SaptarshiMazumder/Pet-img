# ---------------------------------------------------------------------------
# Credit packs & digital-product configuration
# ---------------------------------------------------------------------------
#
# The site sells CREDITS. Spending 1 credit permanently unlocks the HD,
# watermark-free download of one generated portrait. Credits are sold in packs
# purchased through Dodo Payments (Merchant of Record) — each pack maps to a
# Dodo *product* created in the Dodo dashboard.
#
# Dodo settles in USD; the price_usd here MUST match the price configured on the
# corresponding Dodo product. The `env_product_id` names the environment variable
# that holds that product's Dodo product id (prod_xxx). Keeping the id in env lets
# us ship this code before the Dodo account/products exist, and swap test-mode vs
# live-mode ids without code changes.
import os

# pack_id -> pack definition
CREDIT_PACKS: dict[str, dict] = {
    "pack_5": {
        "credits": 5,
        "price_usd": 18,
        "label": "5 credits",
        "env_product_id": "DODO_PRODUCT_PACK_5",
    },
    "pack_15": {
        "credits": 15,
        "price_usd": 48,
        "label": "15 credits",
        "env_product_id": "DODO_PRODUCT_PACK_15",
    },
    "pack_40": {
        "credits": 40,
        "price_usd": 120,
        "label": "40 credits",
        "env_product_id": "DODO_PRODUCT_PACK_40",
    },
}


def get_pack(pack_id: str) -> dict | None:
    return CREDIT_PACKS.get(pack_id)


def get_product_id(pack_id: str) -> str | None:
    """Resolve the Dodo product id for a pack from the environment."""
    pack = CREDIT_PACKS.get(pack_id)
    if not pack:
        return None
    return os.getenv(pack["env_product_id"]) or None


def public_catalog() -> list[dict]:
    """Pack list safe to expose to the client (no Dodo ids)."""
    return [
        {
            "pack_id": pid,
            "credits": p["credits"],
            "price_usd": p["price_usd"],
            "label": p["label"],
        }
        for pid, p in CREDIT_PACKS.items()
    ]
