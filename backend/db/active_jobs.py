"""
Data-access layer for the Firestore `active_jobs` collection.

One document per in-flight generation job. Used for crash recovery
on server restart (see worker.recover_active_jobs).
"""
from __future__ import annotations


def _db():
    from backend.firebase import get_db
    return get_db()


def persist(job_id: str, style_key: str, template_key: str, uid: str | None) -> None:
    """Create the active_jobs document when a job is first submitted."""
    try:
        from firebase_admin import firestore as fb_firestore
        _db().collection("active_jobs").document(job_id).set({
            "job_id": job_id,
            "runpod_job_id": None,
            "style_key": style_key,
            "template_key": template_key,
            "uid": uid,
            "status": "processing",
            "created_at": fb_firestore.SERVER_TIMESTAMP,
        })
    except Exception as exc:
        print(f"[active_jobs] failed to persist {job_id}: {exc}")


def update_runpod_id(job_id: str, runpod_job_id: str) -> None:
    """Stamp the RunPod-assigned job ID onto the document once received."""
    try:
        _db().collection("active_jobs").document(job_id).update({
            "runpod_job_id": runpod_job_id,
        })
    except Exception as exc:
        print(f"[active_jobs] failed to update runpod_job_id for {job_id}: {exc}")


def remove(job_id: str) -> None:
    """Delete the active_jobs document when a job finishes (success or failure)."""
    try:
        _db().collection("active_jobs").document(job_id).delete()
    except Exception as exc:
        print(f"[active_jobs] failed to remove {job_id}: {exc}")


def stream_all():
    """Yield all active_jobs documents — used by the startup recovery path."""
    return _db().collection("active_jobs").stream()
