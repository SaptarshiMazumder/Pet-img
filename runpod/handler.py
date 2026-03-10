"""
RunPod Serverless Handler for ZTurboLoraPet ComfyUI workflow.

The base image (runpod/worker-comfyui) starts ComfyUI automatically.
This handler waits for it to be ready, then serves RunPod jobs.
Generated images are uploaded to Cloudflare R2.
"""

import json
import os
import random
import time
import urllib.parse
import urllib.request

import boto3
from botocore.config import Config
import requests
import runpod

# ---------------------------------------------------------------------------
# Paths & config
# ---------------------------------------------------------------------------
WORKFLOW_PATH = "/workflow_api.json"
COMFYUI_URL = "http://127.0.0.1:8188"

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "")
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
# ComfyUI helpers
# ---------------------------------------------------------------------------
def wait_for_comfyui(timeout: int = 300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=2)
            if r.status_code == 200:
                print("[comfyui] server is ready")
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("ComfyUI did not start within the timeout period")


def queue_prompt(workflow: dict) -> str:
    r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow, "client_id": "runpod-worker"})
    r.raise_for_status()
    return r.json()["prompt_id"]


def poll_until_done(prompt_id: str) -> None:
    while True:
        r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
        history = r.json()
        if prompt_id in history:
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI job failed: {status.get('messages', [])}")
            return
        time.sleep(1)


def get_images(prompt_id: str) -> list[bytes]:
    r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
    outputs = r.json().get(prompt_id, {}).get("outputs", {})

    images = []
    for node_output in outputs.values():
        for img_info in node_output.get("images", []):
            resp = requests.get(
                f"{COMFYUI_URL}/view",
                params={
                    "filename": img_info["filename"],
                    "subfolder": img_info.get("subfolder", ""),
                    "type": img_info.get("type", "output"),
                },
                timeout=120,
            )
            resp.raise_for_status()
            images.append(resp.content)
    return images


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------
def build_workflow(job_input: dict) -> dict:
    with open(WORKFLOW_PATH) as f:
        wf = json.load(f)

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

    if "lora_name" in job_input:
        wf["30"]["inputs"]["lora_name"] = str(job_input["lora_name"])
    if "lora_strength" in job_input:
        s = float(job_input["lora_strength"])
        wf["30"]["inputs"]["strength_model"] = s
        wf["30"]["inputs"]["strength_clip"] = s

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
# Entrypoint — base image starts ComfyUI, we just wait then serve
# ---------------------------------------------------------------------------
print("Waiting for ComfyUI to be ready...")
wait_for_comfyui()
print("ComfyUI is ready. Starting RunPod serverless handler.")
runpod.serverless.start({"handler": handler})
