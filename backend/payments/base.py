"""Abstract base class for payment providers."""

from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    """
    Strategy interface for payment providers.

    To add a new provider:
      1. Subclass PaymentProvider and implement both methods.
      2. Register it in backend/payments/__init__.py under _PROVIDERS.
      3. Set PAYMENT_PROVIDER=<name> in your environment.
    """

    @abstractmethod
    def create_checkout(self, uid: str, price: dict, origin: str) -> dict:
        """
        Initiate a payment session for one credit pack.

        Args:
            uid:    Firebase user ID (used as customer reference / metadata).
            price:  Dict from get_credit_recharge_price_for_country(), e.g.:
                      {"amount": 1000, "currency": "JPY", "credits": 25, ...}
            origin: Frontend base URL for redirect construction.

        Returns:
            Provider-specific dict forwarded directly to the frontend.
            Redirect-based providers (Komoju) return {"url": "...", ...}.
            Modal-based providers (Razorpay) return {"order_id": "...", "key_id": "...", ...}.
        """
        ...

    @abstractmethod
    def handle_webhook(self, request) -> tuple[str, int] | None:
        """
        Verify and parse an inbound webhook from the payment provider.

        Args:
            request: Flask request object (raw body + headers available).

        Returns:
            (uid, credits_to_add) on a completed payment event.
            None if the event is not a credit-granting event (should return 200 OK).

        Raises:
            ValueError:  Invalid payload / unparseable body.
            PermissionError: Signature verification failed.
        """
        ...
