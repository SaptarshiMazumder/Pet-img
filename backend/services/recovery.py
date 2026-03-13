"""
Recovery service — resumes polling for any jobs that were in-flight when the
server last restarted.  Called once at startup from app.py.
"""
import threading

from backend.job_store import job_store
from backend.scaling import scaler
from backend.db import active_jobs as active_jobs_db
from backend.services.generation import process_runpod_result, _review_and_fix_if_needed
from runpod_client import poll_job


def recover_active_jobs() -> None:
    """Called on startup — resumes polling for any jobs that were in-flight."""
    try:
        docs = active_jobs_db.stream_all()
        recovered = 0
        for doc in docs:
            data = doc.to_dict()
            job_id = data.get("job_id")
            runpod_job_id = data.get("runpod_job_id")

            if not runpod_job_id:
                job_store.create(job_id)
                job_store.update(job_id, status="failed", error="Server restarted before job was submitted to RunPod")
                active_jobs_db.remove(job_id)
                continue

            job_store.create(job_id)
            job_store.update(job_id, status="processing")
            thread = threading.Thread(
                target=_recover_job,
                args=(job_id, runpod_job_id, data.get("style_key", ""), data.get("template_key", ""), data.get("uid")),
                daemon=True,
            )
            thread.start()
            recovered += 1

        if recovered:
            print(f"[recovery] resumed {recovered} in-flight job(s)")
    except Exception as exc:
        print(f"[recovery] failed to recover jobs: {exc}")


def _recover_job(job_id: str, runpod_job_id: str, style_key: str, template_key: str, uid: str | None) -> None:
    scaler.on_job_start()
    try:
        runpod_result = poll_job(runpod_job_id)
        runpod_result = _review_and_fix_if_needed(runpod_result)
        process_runpod_result(
            job_id=job_id,
            runpod_result=runpod_result,
            style_key=style_key,
            template_key=template_key,
            uid=uid,
        )
    except Exception as exc:
        job_store.update(job_id, status="failed", error=str(exc))
    finally:
        active_jobs_db.remove(job_id)
        scaler.on_job_finish()
