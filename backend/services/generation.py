"""
Generation service — orchestrates the full portrait generation pipeline:
  build prompt → submit to RunPod → poll for result → review (Gemini) → fix if needed (Gemini) → persist + return
"""
import os
import time
from pathlib import Path

from backend.services.prompt_builder import build_animal_edo_prompt
from backend.runpod import submit_job, poll_job
from backend.job_store import job_store
from backend.storage import public_url, download_object, upload_object
from backend.autoscaler_client import autoscaler
from backend.db import active_jobs as active_jobs_db
from backend.db import portrait_generation as portrait_generation_db


def process_runpod_result(
    job_id: str,
    runpod_result: dict,
    style_key: str,
    template_key: str,
    uid: str | None,
    positive_prompt: str = "",
    negative_prompt: str = "",
    animal_data: dict | None = None,
    duration_seconds: float | None = None,
    source_r2_key: str | None = None,
) -> None:
    """Convert a RunPod result into a presigned URL, persist to Firestore, update job store."""
    images = runpod_result.get("images", [])
    r2_key = images[0]["key"] if images and images[0].get("key") else None
    presigned_url = public_url(r2_key) if r2_key else None

    if uid and r2_key:
        portrait_generation_db.save(
            uid=uid,
            job_id=job_id,
            r2_key=r2_key,
            template_key=template_key,
            style_key=style_key,
            positive_prompt=positive_prompt,
            seed=runpod_result.get("seed"),
            duration_seconds=duration_seconds,
            source_r2_key=source_r2_key,
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
        duration_seconds=duration_seconds,
    )


def _review_and_fix_if_needed(job_id: str, runpod_result: dict) -> dict:
    """
    Review the generated image with Gemini. If defects are found, fix with Gemini image edit
    and upload the fixed image to R2. Returns the (possibly modified) runpod_result.
    """
    if not os.getenv("GEMINI_API_KEY"):
        return runpod_result  # Skip review when Gemini not configured

    images = runpod_result.get("images", [])
    if not images or not images[0].get("key"):
        return runpod_result

    job_store.update(job_id, status="fixing")

    r2_key = images[0]["key"]
    try:
        image_bytes = download_object(r2_key)
    except Exception as exc:
        print(f"[review] failed to download {r2_key}: {exc}")
        return runpod_result

    try:
        from backend.services.image_quality import review_image, fix_image

        fix_prompt = review_image(image_bytes)
        if not fix_prompt:
            return runpod_result  # No issues found

        print(f"[review] issues found, fix prompt: {fix_prompt[:80]}...")
        fixed_bytes = fix_image(image_bytes, fix_prompt)
        if not fixed_bytes:
            print("[review] fix failed, using original image")
            return runpod_result

        # Upload fixed image to R2 (new key: original_fixed.png)
        base, ext = r2_key.rsplit(".", 1) if "." in r2_key else (r2_key, "png")
        fixed_key = f"{base}_fixed.{ext}"
        upload_object(fixed_key, fixed_bytes)
        print(f"[review] uploaded fixed image to {fixed_key}")

        # Use fixed image as the final result
        runpod_result = dict(runpod_result)
        runpod_result["images"] = [{**images[0], "key": fixed_key}]
        return runpod_result

    except Exception as exc:
        print(f"[review] error during review/fix: {exc}")
        return runpod_result


def run_job_background(
    job_id: str,
    tmp_path: str,
    style: dict,
    style_key: str,
    template_key: str,
    overrides: dict,
    dry_run: bool = False,
    uid: str | None = None,
    source_r2_key: str | None = None,
) -> None:
    autoscaler.on_job_start()
    active_jobs_db.persist(job_id, style_key, template_key, uid)
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
        active_jobs_db.update_runpod_id(job_id, runpod_job_id)

        t_submit = time.time()
        runpod_result = poll_job(runpod_job_id)
        duration = time.time() - t_submit

        # Review with Gemini; fix defects (mangled paws, extra limbs, etc.) if found
        runpod_result = _review_and_fix_if_needed(job_id, runpod_result)

        process_runpod_result(
            job_id=job_id,
            runpod_result=runpod_result,
            style_key=style_key,
            template_key=template_key,
            uid=uid,
            positive_prompt=result["positive_prompt"],
            negative_prompt=result["negative_prompt"],
            animal_data=result["animal_data"],
            duration_seconds=duration,
            source_r2_key=source_r2_key,
        )

    except Exception as exc:
        job_store.update(job_id, status="failed", error=str(exc))

    finally:
        Path(tmp_path).unlink(missing_ok=True)
        active_jobs_db.remove(job_id)
        autoscaler.on_job_finish()
