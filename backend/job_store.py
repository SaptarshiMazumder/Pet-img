"""Firestore-backed job store — survives backend restarts and scales across instances."""
from backend.firebase import get_db

_COLLECTION = "jobs"


class JobStore:
    def create(self, job_id: str) -> None:
        get_db().collection(_COLLECTION).document(job_id).set({
            "status": "pending",
            "job_id": job_id,
        })

    def update(self, job_id: str, **fields) -> None:
        get_db().collection(_COLLECTION).document(job_id).set(fields, merge=True)

    def get(self, job_id: str) -> dict | None:
        doc = get_db().collection(_COLLECTION).document(job_id).get()
        return doc.to_dict() if doc.exists else None


job_store = JobStore()
