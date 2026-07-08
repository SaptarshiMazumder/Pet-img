"""
Generation service — orchestrates the full portrait generation pipeline:
  build prompt → submit to RunPod → poll for result → review (Gemini) → fix if needed (Gemini) → persist + return
"""
import os
import secrets
import threading
import time
from pathlib import Path

from backend.services.prompt_builder import build_animal_edo_prompt
from backend.services.watermark import make_preview
from backend.runpod import submit_job, poll_job
from backend.job_store import job_store
from backend.storage import public_url, download_object, upload_object
from backend.storage.r2 import delete_object
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
    orientation: str = "portrait",
) -> None:
    """Turn a RunPod result into a WATERMARKED public preview + a PRIVATE HD file.

    The full-resolution HD is never served publicly: it is copied to a secret,
    unguessable key and the RunPod-produced public object is deleted. Only the
    watermarked preview URL is returned to the client. Spending a credit later
    unlocks the HD (see routes/user.py + db/credits.py).
    """
    images = runpod_result.get("images", [])
    hd_public_key = images[0]["key"] if images and images[0].get("key") else None

    preview_url = None
    preview_key = None
    hd_secret_key = None

    if hd_public_key:
        try:
            hd_bytes = download_object(hd_public_key)
        except Exception as exc:
            print(f"[preview] failed to download HD {hd_public_key}: {exc}")
            hd_bytes = None

        if hd_bytes is not None:
            # 1. Build the watermarked, downscaled public preview.
            try:
                preview_bytes = make_preview(hd_bytes)
                preview_key = f"previews/{job_id}.jpg"
                upload_object(preview_key, preview_bytes, content_type="image/jpeg")
                preview_url = public_url(preview_key)
            except Exception as exc:
                print(f"[preview] failed to build/upload preview for {job_id}: {exc}")

            # 2. Copy the clean HD to a secret key (only revealed after unlock).
            #    Only retained for signed-in users, who alone can unlock/download it.
            if uid:
                try:
                    ext = hd_public_key.rsplit(".", 1)[1].lower() if "." in hd_public_key else "png"
                    content_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                    hd_secret_key = f"hd/{job_id}-{secrets.token_urlsafe(16)}.{ext}"
                    upload_object(hd_secret_key, hd_bytes, content_type=content_type)
                except Exception as exc:
                    print(f"[preview] failed to store private HD for {job_id}: {exc}")
                    hd_secret_key = None

            # 3. Delete the publicly-reachable HD object(s) RunPod produced.
            _delete_public_hd(hd_public_key)

    if uid and hd_secret_key and preview_key:
        portrait_generation_db.save(
            uid=uid,
            job_id=job_id,
            template_key=template_key,
            style_key=style_key,
            positive_prompt=positive_prompt,
            hd_r2_key=hd_secret_key,
            preview_r2_key=preview_key,
            seed=runpod_result.get("seed"),
            duration_seconds=duration_seconds,
            source_r2_key=source_r2_key,
            orientation=orientation,
            unlocked=False,
        )

    # Mark job complete with the watermarked preview URL so the UI shows it right away.
    job_store.update(
        job_id,
        status="completed",
        presigned_url=preview_url,
        unlocked=False,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        animal_data=animal_data,
        template=template_key,
        style=style_key,
        seed=runpod_result.get("seed"),
        prompt_id=runpod_result.get("prompt_id"),
        duration_seconds=duration_seconds,
        orientation=orientation,
    )


def _delete_public_hd(key: str) -> None:
    """Remove the public HD object(s) so only the watermarked preview stays public.

    If Gemini produced a ``*_fixed`` variant, the pre-fix original is still public
    at the base key, so delete that too.
    """
    keys = [key]
    if "_fixed." in key:
        keys.append(key.replace("_fixed.", ".", 1))
    for k in keys:
        try:
            delete_object(k)
        except Exception as exc:
            print(f"[preview] failed to delete public HD object {k}: {exc}")


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
    orientation: str = "portrait",
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
            orientation=orientation,
        )

    except Exception as exc:
        job_store.update(job_id, status="failed", error=str(exc))

    finally:
        Path(tmp_path).unlink(missing_ok=True)
        active_jobs_db.remove(job_id)
        autoscaler.on_job_finish()
