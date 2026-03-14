"""Data-access layer for the Firestore `samples` collection."""
from __future__ import annotations


def _db():
    from backend.firebase import get_db
    return get_db()


def save(sample_id: str, r2_key: str, uploaded_by: str) -> None:
    from firebase_admin import firestore as fb_firestore
    _db().collection("samples").document(sample_id).set({
        "r2_key": r2_key,
        "uploaded_by": uploaded_by,
        "created_at": fb_firestore.SERVER_TIMESTAMP,
    })


def list_all(limit: int = 200):
    """Return a stream of all sample documents, newest first."""
    return (
        _db()
        .collection("samples")
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
        .stream()
    )


def delete(sample_id: str) -> None:
    _db().collection("samples").document(sample_id).delete()
