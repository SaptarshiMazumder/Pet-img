"""In-memory job store — owns all job state for in-flight and recently completed jobs."""
import threading

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def create(job_id: str) -> None:
    with _lock:
        _jobs[job_id] = {"status": "pending", "job_id": job_id}


def update(job_id: str, fields: dict) -> bool:
    with _lock:
        if job_id not in _jobs:
            return False
        _jobs[job_id].update(fields)
        return True


def get(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None
