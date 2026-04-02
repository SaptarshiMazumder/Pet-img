"""Stripe Checkout line-item amounts (smallest currency unit)."""


def checkout_unit_amount(amount_major: int, currency: str) -> int:
    """
    `amount_major` is the human price from our config (e.g. 7 USD, 1000 JPY, 550 INR).
    Returns Stripe unit_amount.
    """
    c = currency.upper()
    # Zero-decimal currencies (Stripe docs)
    if c in (
        "BIF",
        "CLP",
        "DJF",
        "GNF",
        "JPY",
        "KMF",
        "KRW",
        "MGA",
        "PYG",
        "RWF",
        "UGX",
        "VND",
        "VUV",
        "XAF",
        "XOF",
        "XPF",
    ):
        return int(amount_major)
    if c == "INR":
        return int(amount_major * 100)  # paise
    # USD, EUR, GBP, etc. — major units → cents/pence
    return int(amount_major * 100)
