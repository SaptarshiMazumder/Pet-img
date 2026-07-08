"""
Data-access layer for the credit system.

Collections:
  user_credits/{uid}          -> { credits: int, updated_at }
  credit_purchases/{payment_id} -> { uid, credits, created_at }   (webhook idempotency)
  generations/{job_id}.unlocked  -> bool                          (per-portrait HD entitlement)

All balance mutations run inside Firestore transactions to prevent double-credit
(webhook retries) and double-spend (concurrent unlock requests).
"""
from __future__ import annotations


class InsufficientCredits(Exception):
    pass


class NotFound(Exception):
    pass


class Forbidden(Exception):
    pass


def _db():
    from backend.firebase import get_db
    return get_db()


def get_credits(uid: str) -> int:
    snap = _db().collection("user_credits").document(uid).get()
    if not snap.exists:
        return 0
    return int(snap.to_dict().get("credits", 0))


def add_credits(uid: str, credits: int, payment_id: str) -> int:
    """Idempotently add credits for a completed purchase. Returns the new balance.

    If `payment_id` was already processed, this is a no-op and returns the
    current balance (safe against webhook redelivery).
    """
    from firebase_admin import firestore

    db = _db()
    transaction = db.transaction()
    user_ref = db.collection("user_credits").document(uid)
    purchase_ref = db.collection("credit_purchases").document(payment_id)

    @firestore.transactional
    def _txn(txn) -> int:
        # Reads first (Firestore requirement)
        purchase_snap = purchase_ref.get(transaction=txn)
        user_snap = user_ref.get(transaction=txn)
        current = int(user_snap.to_dict().get("credits", 0)) if user_snap.exists else 0

        if purchase_snap.exists:
            return current  # already processed — do not double-credit

        new_balance = current + int(credits)
        txn.set(
            user_ref,
            {"credits": new_balance, "updated_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )
        txn.set(
            purchase_ref,
            {
                "uid": uid,
                "credits": int(credits),
                "created_at": firestore.SERVER_TIMESTAMP,
            },
        )
        return new_balance

    return _txn(transaction)


def spend_credit_to_unlock(uid: str, job_id: str) -> dict:
    """Spend 1 credit to unlock a portrait's HD download.

    Returns {"unlocked": True, "credits_remaining": int, "already": bool}.
    Raises NotFound / Forbidden / InsufficientCredits.
    Idempotent: if the portrait is already unlocked, no credit is charged.
    """
    from firebase_admin import firestore

    db = _db()
    transaction = db.transaction()
    gen_ref = db.collection("generations").document(job_id)
    user_ref = db.collection("user_credits").document(uid)

    @firestore.transactional
    def _txn(txn) -> dict:
        gen_snap = gen_ref.get(transaction=txn)
        if not gen_snap.exists:
            raise NotFound()
        gen = gen_snap.to_dict()
        if gen.get("uid") != uid:
            raise Forbidden()

        user_snap = user_ref.get(transaction=txn)
        current = int(user_snap.to_dict().get("credits", 0)) if user_snap.exists else 0

        if gen.get("unlocked"):
            return {"unlocked": True, "credits_remaining": current, "already": True}

        if current < 1:
            raise InsufficientCredits()

        txn.update(user_ref, {"credits": current - 1, "updated_at": firestore.SERVER_TIMESTAMP})
        txn.update(gen_ref, {"unlocked": True})
        return {"unlocked": True, "credits_remaining": current - 1, "already": False}

    return _txn(transaction)
