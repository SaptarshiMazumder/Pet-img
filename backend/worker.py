from pathlib import Path

from prompt_generator import build_animal_edo_prompt
from runpod_client import run_job
from backend.job_store import job_store
from backend.storage import generate_presigned_url


def _save_to_firestore(uid: str, job_id: str, r2_key: str, template_key: str,
                       style_key: str, positive_prompt: str, seed=None) -> None:
    try:
        from backend.firebase_app import get_db
        from firebase_admin import firestore as fb_firestore
        get_db().collection("generations").document(job_id).set({
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
    """
    Background thread entry point.
    Runs the full pipeline: Gemini → RunPod → R2 presigned URL.
    If dry_run=True, skips RunPod and only prints prompts to console.
    Updates job_store at each stage.
    """
    try:
        job_store.update(job_id, status="processing")

        # Step 1: Analyse pet photo and compose prompt
        result = build_animal_edo_prompt(
            image_path=tmp_path,
            style=style,
            style_key=style_key,
            template_key=template_key,
        )

        # Step 2: Build RunPod input
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
            print("POSITIVE PROMPT:")
            print(result["positive_prompt"])
            print("-" * 60)
            print("NEGATIVE PROMPT:")
            print(result["negative_prompt"])
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

        # Step 3: Submit to RunPod and poll until done
        runpod_result = run_job(job_input)

        # Step 4: Generate presigned URL for the first output image
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
                positive_prompt=result["positive_prompt"],
                seed=runpod_result.get("seed"),
            )

        job_store.update(
            job_id,
            status="completed",
            presigned_url=presigned_url,
            positive_prompt=result["positive_prompt"],
            negative_prompt=result["negative_prompt"],
            animal_data=result["animal_data"],
            template=template_key,
            style=style_key,
            seed=runpod_result.get("seed"),
            prompt_id=runpod_result.get("prompt_id"),
        )

    except Exception as exc:
        job_store.update(job_id, status="failed", error=str(exc))

    finally:
        Path(tmp_path).unlink(missing_ok=True)
