"""
Data-access layer for the Firestore `generations` collection.

One document per completed, user-attributed portrait generation.
"""
from __future__ import annotations


def _db():
    from backend.firebase import get_db
    return get_db()


def save(
    uid: str,
    job_id: str,
    r2_key: str,
    template_key: str,
    style_key: str,
    positive_prompt: str,
    seed=None,
    duration_seconds: float | None = None,
    source_r2_key: str | None = None,
) -> None:
    """Persist a completed portrait generation result. No-op on Firestore errors (logged)."""
    try:
        from firebase_admin import firestore as fb_firestore
        doc = {
            "uid": uid,
            "r2_key": r2_key,
            "template_key": template_key,
            "style_key": style_key,
            "positive_prompt": positive_prompt,
            "seed": seed,
            "created_at": fb_firestore.SERVER_TIMESTAMP,
        }
        if duration_seconds is not None:
            doc["duration_seconds"] = round(duration_seconds, 1)
        if source_r2_key:
            doc["source_r2_key"] = source_r2_key
        _db().collection("generations").document(job_id).set(doc)
    except Exception as exc:
        print(f"[Firestore] Failed to save portrait generation {job_id}: {exc}")


def delete(job_id: str) -> None:
    """Delete a portrait generation document from Firestore."""
    _db().collection("generations").document(job_id).delete()


def get_by_uid(uid: str, limit: int = 100):
    """Return a Firestore stream of portrait generation documents for the given user."""
    return (
        _db()
        .collection("generations")
        .where("uid", "==", uid)
        .limit(limit)
        .stream()
    )
