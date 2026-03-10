"""
RunPod Serverless Handler for ZTurboLoraPet ComfyUI workflow.

Starts ComfyUI as a subprocess, then accepts RunPod jobs and routes them
through ComfyUI's HTTP API. Generated images are uploaded to Cloudflare R2
and the public URLs are returned.
"""

import base64
import json
import os
import random
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import boto3
from botocore.config import Config
import runpod

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
COMFYUI_DIR = Path("/comfyui")
WORKFLOW_PATH = Path(__file__).parent / "workflow_api.json"
COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8188
COMFYUI_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

VOLUME_ROOT = Path(os.environ.get("VOLUME_PATH", "/runpod-volume"))

# ---------------------------------------------------------------------------
# R2 config  (set these as env vars on the RunPod endpoint)
# ---------------------------------------------------------------------------
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "")
# Optional: set to your bucket's public domain if you have one configured,
# e.g. "https://images.yourdomain.com". Falls back to the R2 public URL.
R2_PUBLIC_BASE_URL = os.environ.get("R2_PUBLIC_BASE_URL", "").rstrip("/")

_r2_client = None


def get_r2_client():
    global _r2_client
    if _r2_client is None:
        _r2_client = boto3.client(
            "s3",
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _r2_client


def upload_to_r2(image_bytes: bytes, key: str) -> str:
    """Upload PNG bytes to R2 and return the public URL."""
    client = get_r2_client()
    client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=key,
        Body=image_bytes,
        ContentType="image/png",
    )
    if R2_PUBLIC_BASE_URL:
        return f"{R2_PUBLIC_BASE_URL}/{key}"
    return f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{R2_BUCKET_NAME}/{key}"


# ---------------------------------------------------------------------------
# Model symlinks
# ---------------------------------------------------------------------------
MODEL_SYMLINKS = {
    COMFYUI_DIR / "models" / "diffusion_models": VOLUME_ROOT / "models" / "diffusion_models",
    COMFYUI_DIR / "models" / "text_encoders": VOLUME_ROOT / "models" / "text_encoders",
    COMFYUI_DIR / "models" / "vae": VOLUME_ROOT / "models" / "vae",
    COMFYUI_DIR / "models" / "loras": VOLUME_ROOT / "models" / "loras",
    COMFYUI_DIR / "output": VOLUME_ROOT / "output",
}


def create_symlinks():
    for link, target in MODEL_SYMLINKS.items():
        target.mkdir(parents=True, exist_ok=True)
        if link.exists() or link.is_symlink():
            if not link.is_symlink():
                import shutil
                shutil.rmtree(link)
            else:
                link.unlink()
        link.symlink_to(target)
        print(f"[symlink] {link} -> {target}")


# ---------------------------------------------------------------------------
# ComfyUI lifecycle
# ---------------------------------------------------------------------------
_comfyui_proc: subprocess.Popen | None = None


def start_comfyui():
    global _comfyui_proc
    print("[comfyui] starting server …")
    _comfyui_proc = subprocess.Popen(
        [
            sys.executable,
            "main.py",
            "--listen",
            COMFYUI_HOST,
            "--port",
            str(COMFYUI_PORT),
            "--disable-auto-launch",
            "--disable-metadata",
        ],
        cwd=str(COMFYUI_DIR),
    )
    wait_for_comfyui()


def wait_for_comfyui(timeout: int = 120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=2)
            print("[comfyui] server is ready")
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("ComfyUI did not start within the timeout period")


# ---------------------------------------------------------------------------
# ComfyUI API helpers
# ---------------------------------------------------------------------------
def _http_json(method: str, path: str, payload: dict | None = None) -> dict:
    url = f"{COMFYUI_URL}{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def queue_prompt(workflow: dict) -> str:
    payload = {"prompt": workflow, "client_id": "runpod-worker"}
    resp = _http_json("POST", "/prompt", payload)
    return resp["prompt_id"]


def poll_until_done(prompt_id: str, poll_interval: float = 0.5) -> None:
    while True:
        queue = _http_json("GET", "/queue")
        running_ids = [item[1] for item in queue.get("queue_running", [])]
        pending_ids = [item[1] for item in queue.get("queue_pending", [])]
        if prompt_id not in running_ids and prompt_id not in pending_ids:
            return
        time.sleep(poll_interval)


def get_images(prompt_id: str) -> list[bytes]:
    history = _http_json("GET", f"/history/{prompt_id}")
    prompt_history = history.get(prompt_id, {})
    outputs = prompt_history.get("outputs", {})

    images: list[bytes] = []
    for node_output in outputs.values():
        for img_info in node_output.get("images", []):
            params = urllib.parse.urlencode(
                {
                    "filename": img_info["filename"],
                    "subfolder": img_info.get("subfolder", ""),
                    "type": img_info.get("type", "output"),
                }
            )
            with urllib.request.urlopen(f"{COMFYUI_URL}/view?{params}") as resp:
                images.append(resp.read())
    return images


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------
def load_workflow() -> dict:
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


def build_workflow(job_input: dict) -> dict:
    """
    Apply API inputs onto the base workflow.

    Pass 1 — generation (KSampler node 31):
      prompt            str   Positive text prompt
      negative_prompt   str   Negative text prompt (default: "")
      width             int   Image width  (default: 1024)
      height            int   Image height (default: 1024)
      steps             int   Denoising steps (default: 15)
      cfg               float CFG scale (default: 1.0)
      seed              int   RNG seed; -1 or omitted → random
      batch_size        int   Number of images (default: 1)

    LoRA stack (two loaders chained):
      lora_name         str   Style LoRA — node 30 (default: wetInkZTurbo.safetensors, strength 0.3)
      lora_strength     float Strength for lora_name, applied to model + clip (default: 0.3)
      lora2_name        str   Style LoRA — node 44 (default: ukiyoeZTurbo.safetensors, strength 0.5)
      lora2_strength    float Strength for lora2_name, applied to model + clip (default: 0.5)

    Pass 2 — latent upscale refinement (KSampler node 38):
      upscale_factor    float LatentUpscaleBy scale (default: 1.25)
      upscale_steps     int   Refine steps (default: 8)
      upscale_denoise   float Refine denoise strength (default: 0.7)
      upscale_sampler   str   Sampler name (default: dpmpp_sde)
      upscale_scheduler str   Scheduler name (default: beta)
    """
    wf = load_workflow()

    if "prompt" in job_input:
        wf["28"]["inputs"]["text"] = str(job_input["prompt"])

    if "negative_prompt" in job_input:
        wf["29"]["inputs"]["text"] = str(job_input["negative_prompt"])

    if "width" in job_input:
        wf["23"]["inputs"]["width"] = int(job_input["width"])
    if "height" in job_input:
        wf["23"]["inputs"]["height"] = int(job_input["height"])
    if "batch_size" in job_input:
        wf["23"]["inputs"]["batch_size"] = int(job_input["batch_size"])

    if "steps" in job_input:
        wf["31"]["inputs"]["steps"] = int(job_input["steps"])
    if "cfg" in job_input:
        wf["31"]["inputs"]["cfg"] = float(job_input["cfg"])

    seed = job_input.get("seed", -1)
    if seed is None or int(seed) < 0:
        seed = random.randint(0, 2**32 - 1)
    wf["31"]["inputs"]["seed"] = int(seed)
    wf["31"]["inputs"]["control_after_generate"] = "fixed"

    # LoRA 1 — node 30 (wetInkZTurbo, default 0.3)
    if "lora_name" in job_input:
        wf["30"]["inputs"]["lora_name"] = str(job_input["lora_name"])
    if "lora_strength" in job_input:
        s = float(job_input["lora_strength"])
        wf["30"]["inputs"]["strength_model"] = s
        wf["30"]["inputs"]["strength_clip"] = s

    # LoRA 2 — node 44 (ukiyoeZTurbo, default 0.5)
    if "lora2_name" in job_input:
        wf["44"]["inputs"]["lora_name"] = str(job_input["lora2_name"])
    if "lora2_strength" in job_input:
        s = float(job_input["lora2_strength"])
        wf["44"]["inputs"]["strength_model"] = s
        wf["44"]["inputs"]["strength_clip"] = s

    if "upscale_factor" in job_input:
        wf["37"]["inputs"]["scale_by"] = float(job_input["upscale_factor"])

    if "upscale_steps" in job_input:
        wf["38"]["inputs"]["steps"] = int(job_input["upscale_steps"])
    if "upscale_denoise" in job_input:
        wf["38"]["inputs"]["denoise"] = float(job_input["upscale_denoise"])
    if "upscale_sampler" in job_input:
        wf["38"]["inputs"]["sampler_name"] = str(job_input["upscale_sampler"])
    if "upscale_scheduler" in job_input:
        wf["38"]["inputs"]["scheduler"] = str(job_input["upscale_scheduler"])

    return wf


# ---------------------------------------------------------------------------
# RunPod handler
# ---------------------------------------------------------------------------
def handler(job: dict) -> dict:
    job_input: dict = job.get("input", {})

    try:
        workflow = build_workflow(job_input)
    except Exception as exc:
        return {"error": f"Failed to build workflow: {exc}"}

    try:
        prompt_id = queue_prompt(workflow)
        print(f"[job] queued prompt {prompt_id}")
        poll_until_done(prompt_id)
        print(f"[job] prompt {prompt_id} finished")
        raw_images = get_images(prompt_id)
    except Exception as exc:
        return {"error": f"ComfyUI execution failed: {exc}"}

    if not raw_images:
        return {"error": "No images were produced"}

    seed = workflow["31"]["inputs"]["seed"]
    uploaded = []
    for i, img_bytes in enumerate(raw_images):
        key = f"pet-generator/{prompt_id}/{seed}_{i}.png"
        try:
            url = upload_to_r2(img_bytes, key)
            print(f"[r2] uploaded {key}")
        except Exception as exc:
            print(f"[r2] upload failed for {key}: {exc}")
            url = None
        uploaded.append({"index": i, "url": url, "key": key})

    return {
        "images": uploaded,
        "prompt_id": prompt_id,
        "seed": seed,
        "upscale_denoise": workflow["38"]["inputs"]["denoise"],
        "upscale_sampler": workflow["38"]["inputs"]["sampler_name"],
        "upscale_scheduler": workflow["38"]["inputs"]["scheduler"],
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    create_symlinks()
    start_comfyui()
    runpod.serverless.start({"handler": handler})
