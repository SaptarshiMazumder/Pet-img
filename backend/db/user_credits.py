"""
Data-access layer for user credit balances stored in Firestore.

Credits live on the user document:  users/{uid}/credits  (int)

Rules:
  - New users are initialized to INITIAL_CREDITS (25) on first access.
  - deduct_one_credit uses a Firestore transaction to prevent races.
  - add_credits is called after a successful payment.
"""
from __future__ import annotations

from google.cloud import firestore as gc_firestore

INITIAL_CREDITS = 25
"""Credits charged for a high-res digital download (vs 1 credit per generation)."""
DOWNLOAD_CREDIT_COST = 10
_CREDITS_FIELD = "credits"


def _db():
    from backend.firebase import get_db
    return get_db()


def get_credits(uid: str) -> int:
    """
    Return current credit balance.
    Initializes the balance to INITIAL_CREDITS for brand-new users.
    """
    doc_ref = _db().collection("users").document(uid)
    doc = doc_ref.get()
    data = doc.to_dict() if doc.exists else {}
    if _CREDITS_FIELD not in (data or {}):
        doc_ref.set({_CREDITS_FIELD: INITIAL_CREDITS}, merge=True)
        return INITIAL_CREDITS
    return data[_CREDITS_FIELD]


def deduct_one_credit(uid: str) -> int:
    """
    Atomically deduct 1 credit from the user's balance.

    Returns the new balance.
    Raises ValueError("Insufficient credits") if balance is already 0.
    Initializes balance to INITIAL_CREDITS for brand-new users, then deducts
    (so a first-time user leaves with INITIAL_CREDITS - 1).
    """
    db = _db()
    doc_ref = db.collection("users").document(uid)

    @gc_firestore.transactional
    def _txn(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}

        if _CREDITS_FIELD not in data:
            # Brand-new user — initialize and consume the first credit atomically
            new_balance = INITIAL_CREDITS - 1
            transaction.set(ref, {_CREDITS_FIELD: new_balance}, merge=True)
            return new_balance

        current = data[_CREDITS_FIELD]
        if current <= 0:
            raise ValueError("Insufficient credits")
        new_balance = current - 1
        transaction.update(ref, {_CREDITS_FIELD: new_balance})
        return new_balance

    return _txn(db.transaction(), doc_ref)


def deduct_credits(uid: str, amount: int) -> int:
    """
    Atomically deduct `amount` credits. Returns the new balance.
    Raises ValueError("Insufficient credits") if the balance is too low.
    New users are initialized to INITIAL_CREDITS before deducting.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    db = _db()
    doc_ref = db.collection("users").document(uid)

    @gc_firestore.transactional
    def _txn(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        data = (snapshot.to_dict() or {}) if snapshot.exists else {}

        if _CREDITS_FIELD not in data:
            current = INITIAL_CREDITS
        else:
            current = data[_CREDITS_FIELD]

        if current < amount:
            raise ValueError("Insufficient credits")
        new_balance = current - amount
        transaction.set(ref, {_CREDITS_FIELD: new_balance}, merge=True)
        return new_balance

    return _txn(db.transaction(), doc_ref)


def add_credits(uid: str, amount: int) -> int:
    """
    Add `amount` credits to the user's balance (called after payment success).
    Returns the new balance.
    """
    db = _db()
    doc_ref = db.collection("users").document(uid)

    @gc_firestore.transactional
    def _txn(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        current = ((snapshot.to_dict() or {}).get(_CREDITS_FIELD, 0)) if snapshot.exists else 0
        new_balance = current + amount
        transaction.set(ref, {_CREDITS_FIELD: new_balance}, merge=True)
        return new_balance

    return _txn(db.transaction(), doc_ref)
