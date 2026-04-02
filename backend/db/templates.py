"""Templates DAL — one Firestore document per template key."""
from __future__ import annotations


def _db():
    from backend.firebase import get_db
    return get_db()


def get(template_key: str) -> dict | None:
    doc = _db().collection("templates").document(template_key).get()
    return doc.to_dict() if doc.exists else None


def get_uso(template_key: str) -> dict | None:
    doc = _db().collection("templates_uso").document(template_key).get()
    return doc.to_dict() if doc.exists else None


def list_all() -> dict[str, dict]:
    return {doc.id: doc.to_dict() for doc in _db().collection("templates").stream()}


def list_all_uso() -> dict[str, dict]:
    return {doc.id: doc.to_dict() for doc in _db().collection("templates_uso").stream()}
