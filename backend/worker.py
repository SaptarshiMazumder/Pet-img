from pathlib import Path

from prompt_generator import build_animal_edo_prompt
from runpod_client import run_job
from backend.job_store import job_store
from backend.storage import generate_presigned_url


def run_job_background(
    job_id: str,
    tmp_path: str,
    style: dict,
    style_key: str,
    template_key: str,
    overrides: dict,
) -> None:
    """
    Background thread entry point.
    Runs the full pipeline: Gemini → RunPod → R2 presigned URL.
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
        job_input.update(overrides)  # overrides can still override dimensions if passed

        # Step 3: Submit to RunPod and poll until done
        runpod_result = run_job(job_input)

        # Step 4: Generate presigned URL for the first output image
        images = runpod_result.get("images", [])
        presigned_url = None
        if images and images[0].get("key"):
            presigned_url = generate_presigned_url(images[0]["key"], expires=3600)

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
