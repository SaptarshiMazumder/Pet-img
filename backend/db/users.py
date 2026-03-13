"""
Data-access layer for the Firestore `users` collection.

Stub — ready for the user profiles feature.
"""
from __future__ import annotations
from typing import Any


def _db():
    from backend.firebase import get_db
    return get_db()


def get_profile(uid: str) -> dict[str, Any] | None:
    """Return the user profile document, or None if it does not exist yet."""
    doc = _db().collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def upsert_profile(uid: str, data: dict[str, Any]) -> None:
    """Create or merge-update the user profile document."""
    _db().collection("users").document(uid).set(data, merge=True)
