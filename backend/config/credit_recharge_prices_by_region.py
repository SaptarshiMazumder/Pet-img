"""
Pricing for credit recharge packs, by region.

1 pack = 25 credits.
All prices are set to be equivalent to ¥1,000 JPY.
  Japan  → ¥1,000 JPY
  India  → ₹550  INR  (~1000 JPY at ~0.55 INR/JPY)
  Others → $7    USD  (~1000 JPY at ~0.007 USD/JPY)
"""

from flask import Blueprint, jsonify, request
from backend.config.digital_download_prices_by_region import get_digital_download_price_for_country

credit_recharge_pricing_bp = Blueprint("credit_recharge_pricing", __name__)

CREDITS_PER_PACK = 25

# Country-code → (amount, currency_code, symbol, locale)
CREDIT_RECHARGE_PRICE_BY_COUNTRY: dict[str, tuple[int, str, str, str]] = {
    "JP": (1000, "JPY", "¥",  "ja-JP"),
    "IN": (550,  "INR", "₹",  "en-IN"),
}

_DEFAULT_RECHARGE_PRICE = (7, "USD", "$", "en-US")


def get_credit_recharge_price_for_country(country_code: str) -> dict:
    amount, currency, symbol, locale = CREDIT_RECHARGE_PRICE_BY_COUNTRY.get(
        country_code.upper(), _DEFAULT_RECHARGE_PRICE
    )
    return {
        "country":       country_code.upper(),
        "amount":        amount,
        "currency":      currency,
        "symbol":        symbol,
        "locale":        locale,
        "label":         f"{symbol}{amount:,}",
        "credits":       CREDITS_PER_PACK,
    }


@credit_recharge_pricing_bp.get("/credits/recharge-price")
def get_credit_recharge_price():
    """
    Returns the recharge pack price for the caller's region.

    Detection order:
      1. ?country=XX  query param (client override / testing)
      2. CF-IPCountry header (set by Cloudflare)
      3. X-Country-Code header (set by other proxies)
      4. Default → USD
    """
    country = (
        request.args.get("country")
        or request.headers.get("CF-IPCountry")
        or request.headers.get("X-Country-Code")
        or "US"
    )
    return jsonify(get_credit_recharge_price_for_country(country))
