"""
Download pricing for the digital portrait file, by region.

All prices are set to be equivalent to ¥2,000 JPY.
  Japan  → ¥2,000 JPY
  India  → ₹1,100 INR  (~2000 JPY at ~0.55 INR/JPY)
  Others → $13 USD      (~2000 JPY at ~0.0065 USD/JPY)
"""

from flask import Blueprint, jsonify, request

digital_download_pricing_bp = Blueprint("digital_download_pricing", __name__)

# Country-code → (amount, currency_code, symbol, locale)
DIGITAL_DOWNLOAD_PRICE_BY_COUNTRY: dict[str, tuple[int, str, str, str]] = {
    "JP": (2000, "JPY", "¥",  "ja-JP"),
    "IN": (1100, "INR", "₹",  "en-IN"),
}

_DEFAULT_PRICE = (13, "USD", "$", "en-US")


def get_digital_download_price_for_country(country_code: str) -> dict:
    amount, currency, symbol, locale = DIGITAL_DOWNLOAD_PRICE_BY_COUNTRY.get(
        country_code.upper(), _DEFAULT_PRICE
    )
    return {
        "country":  country_code.upper(),
        "amount":   amount,
        "currency": currency,
        "symbol":   symbol,
        "locale":   locale,
        "label":    f"{symbol}{amount:,}",
    }


@digital_download_pricing_bp.get("/pricing")
def get_digital_download_price():
    """
    Returns the digital download price for the caller's region.

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
    return jsonify(get_digital_download_price_for_country(country))
