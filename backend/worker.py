import threading
import time
from pathlib import Path

from prompt_generator import build_animal_edo_prompt
from runpod_client import submit_job, poll_job, set_workers
from backend.job_store import job_store
from backend.storage import generate_presigned_url

_IDLE_TIMEOUT = 120  # seconds of zero-job inactivity before full scale-down

_active_jobs = 0
_active_lock = threading.Lock()
_idle_timer: threading.Timer | None = None
_idle_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Scale helpers
# ---------------------------------------------------------------------------

def _cancel_idle_timer() -> None:
    global _idle_timer
    with _idle_lock:
        if _idle_timer is not None:
            _idle_timer.cancel()
            _idle_timer = None


def _start_idle_timer() -> None:
    global _idle_timer
    with _idle_lock:
        if _idle_timer is not None:
            _idle_timer.cancel()
        _idle_timer = threading.Timer(_IDLE_TIMEOUT, _scale_to_zero)
        _idle_timer.daemon = True
        _idle_timer.start()


def _scale_to_zero() -> None:
    try:
        set_workers(min_n=0, max_n=0)
    except Exception as exc:
        print(f"[scale] failed to scale to zero: {exc}")


def _on_job_start() -> None:
    global _active_jobs
    with _active_lock:
        _active_jobs += 1
    _cancel_idle_timer()


def _on_job_finish() -> None:
    global _active_jobs
    with _active_lock:
        _active_jobs -= 1
        remaining = _active_jobs
    if remaining == 0:
        threading.Thread(target=_set_max_one, daemon=True).start()
        _start_idle_timer()


def _set_max_one() -> None:
    try:
        set_workers(min_n=1, max_n=1)
    except Exception as exc:
        print(f"[scale] failed to set max=1: {exc}")


# ---------------------------------------------------------------------------
# Firestore active_jobs persistence
# ---------------------------------------------------------------------------

def _get_db():
    from backend.firebase_app import get_db
    return get_db()


def _persist_active_job(job_id: str, style_key: str, template_key: str, uid: str | None) -> None:
    try:
        from firebase_admin import firestore as fb_firestore
        _get_db().collection("active_jobs").document(job_id).set({
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


def _update_runpod_job_id(job_id: str, runpod_job_id: str) -> None:
    try:
        _get_db().collection("active_jobs").document(job_id).update({
            "runpod_job_id": runpod_job_id,
        })
    except Exception as exc:
        print(f"[active_jobs] failed to update runpod_job_id for {job_id}: {exc}")


def _remove_active_job(job_id: str) -> None:
    try:
        _get_db().collection("active_jobs").document(job_id).delete()
    except Exception as exc:
        print(f"[active_jobs] failed to remove {job_id}: {exc}")


# ---------------------------------------------------------------------------
# Firestore generations persistence
# ---------------------------------------------------------------------------

def _save_to_firestore(uid: str, job_id: str, r2_key: str, template_key: str,
                       style_key: str, positive_prompt: str, seed=None) -> None:
    try:
        from firebase_admin import firestore as fb_firestore
        _get_db().collection("generations").document(job_id).set({
            "uid": uid,
            "r2_key": r2_key,
            "template_key": template_key,
            "style_key": style_key,
            "positive_prompt": positive_prompt,
            "seed": seed,
            "created_at": fb_firestore.SERVER_TIMESTAMP,
        })
    except Exception as exc:
        print(f"[Firestore] Failed to save generation {job_id}: {exc}")


# ---------------------------------------------------------------------------
# Result processing (shared between normal and recovery paths)
# ---------------------------------------------------------------------------

def _process_runpod_result(job_id: str, runpod_result: dict, style_key: str,
                            template_key: str, uid: str | None,
                            positive_prompt: str = "", negative_prompt: str = "",
                            animal_data: dict | None = None) -> None:
    images = runpod_result.get("images", [])
    r2_key = images[0]["key"] if images and images[0].get("key") else None
    presigned_url = generate_presigned_url(r2_key, expires=3600) if r2_key else None

    if uid and r2_key:
        _save_to_firestore(
            uid=uid,
            job_id=job_id,
            r2_key=r2_key,
            template_key=template_key,
            style_key=style_key,
            positive_prompt=positive_prompt,
            seed=runpod_result.get("seed"),
        )

    job_store.update(
        job_id,
        status="completed",
        presigned_url=presigned_url,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        animal_data=animal_data,
        template=template_key,
        style=style_key,
        seed=runpod_result.get("seed"),
        prompt_id=runpod_result.get("prompt_id"),
    )


# ---------------------------------------------------------------------------
# Main background job
# ---------------------------------------------------------------------------

def run_job_background(
    job_id: str,
    tmp_path: str,
    style: dict,
    style_key: str,
    template_key: str,
    overrides: dict,
    dry_run: bool = False,
    uid: str | None = None,
) -> None:
    _on_job_start()
    _persist_active_job(job_id, style_key, template_key, uid)
    try:
        job_store.update(job_id, status="processing")

        result = build_animal_edo_prompt(
            image_path=tmp_path,
            style=style,
            style_key=style_key,
            template_key=template_key,
        )

        lora_cfg = style.get("lora", {})
        job_input = {
            "prompt": result["positive_prompt"],
            "negative_prompt": result["negative_prompt"],
            "lora_name": lora_cfg.get("lora_name", "wetInkZTurbo.safetensors"),
            "lora_strength": lora_cfg.get("lora_strength", 0.3),
            "lora2_name": lora_cfg.get("lora2_name", "ukiyoeZTurbo.safetensors"),
            "lora2_strength": lora_cfg.get("lora2_strength", 0.0),
            "width": 1216,
            "height": 832,
        }
        job_input.update(overrides)

        if dry_run:
            print("\n" + "=" * 60)
            print(f"[DRY RUN] job_id={job_id}  template={template_key}  style={style_key}")
            print("-" * 60)
            print(result["positive_prompt"])
            print("=" * 60 + "\n")
            job_store.update(
                job_id,
                status="completed",
                positive_prompt=result["positive_prompt"],
                negative_prompt=result["negative_prompt"],
                animal_data=result["animal_data"],
                template=template_key,
                style=style_key,
                dry_run=True,
            )
            return

        runpod_job_id = submit_job(job_input)
        _update_runpod_job_id(job_id, runpod_job_id)

        runpod_result = poll_job(runpod_job_id)
        _process_runpod_result(
            job_id=job_id,
            runpod_result=runpod_result,
            style_key=style_key,
            template_key=template_key,
            uid=uid,
            positive_prompt=result["positive_prompt"],
            negative_prompt=result["negative_prompt"],
            animal_data=result["animal_data"],
        )

    except Exception as exc:
        job_store.update(job_id, status="failed", error=str(exc))

    finally:
        Path(tmp_path).unlink(missing_ok=True)
        _remove_active_job(job_id)
        _on_job_finish()


# ---------------------------------------------------------------------------
# Recovery on server restart
# ---------------------------------------------------------------------------

def recover_active_jobs() -> None:
    """Called on startup — resumes polling for any jobs that were in-flight."""
    try:
        docs = _get_db().collection("active_jobs").stream()
        recovered = 0
        for doc in docs:
            data = doc.to_dict()
            job_id = data.get("job_id")
            runpod_job_id = data.get("runpod_job_id")

            if not runpod_job_id:
                # Job never reached RunPod (server died during Gemini step) — mark failed
                job_store.create(job_id)
                job_store.update(job_id, status="failed", error="Server restarted before job was submitted to RunPod")
                _remove_active_job(job_id)
                continue

            # Resume polling in a background thread
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
    _on_job_start()
    try:
        runpod_result = poll_job(runpod_job_id)
        _process_runpod_result(
            job_id=job_id,
            runpod_result=runpod_result,
            style_key=style_key,
            template_key=template_key,
            uid=uid,
        )
    except Exception as exc:
        job_store.update(job_id, status="failed", error=str(exc))
    finally:
        _remove_active_job(job_id)
        _on_job_finish()
