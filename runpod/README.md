# ZTurboLoraPet — RunPod Serverless Worker

ComfyUI serverless API wrapping the **ZTurboLoraPet** workflow.
Stack: `z_image_turbo_bf16` UNET · Qwen3-4B CLIP (lumina2) · FLUX VAE · sketchZTurbo LoRA.

---

## Repository layout

```
runpod/
├── Dockerfile           # Container definition
├── handler.py           # RunPod serverless handler
├── workflow_api.json    # ComfyUI API-format workflow
└── README.md            # This file
```

---

## 1 — Prepare the RunPod Network Volume

Create a Network Volume in the RunPod console (≥ 50 GB recommended) and attach it to a
**temporary** GPU pod first so you can SSH in and download the models.

The volume will be mounted at `/runpod-volume` in the serverless worker.

### 1a — Directory structure

```bash
mkdir -p /runpod-volume/models/unet
mkdir -p /runpod-volume/models/vae
mkdir -p /runpod-volume/models/clip
mkdir -p /runpod-volume/models/loras
mkdir -p /runpod-volume/output
```

### 1b — Download models

> **Tip:** `wget -c` resumes interrupted downloads.
> You may need a Hugging Face token for gated repos: `--header="Authorization: Bearer $HF_TOKEN"`

#### UNET — Z-Image Turbo (bf16)

```bash
# Replace <REPO> with the actual HuggingFace repo for this model.
# e.g. https://huggingface.co/<author>/z-image-turbo/resolve/main/z_image_turbo_bf16.safetensors
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors" \
  -O /workspace/models/diffusion_models/z_image_turbo_bf16.safetensors
```

#### VAE — FLUX ae.safetensors

```bash
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors" \
  -O /workspace/models/vae/ae.safetensors
```

#### CLIP — Qwen3 4B (lumina2 format)

```bash
# Replace <REPO> with the actual HuggingFace repo that hosts qwen_3_4b.safetensors.
# Likely a converted/merged CLIP export from the Lumina2 / Z-Image project.
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" \
  -O /workspace/models/text_encoders/qwen_3_4b.safetensors
```

#### LoRA — sketchZTurbo

```bash
# Replace <REPO> with the actual HuggingFace repo or CivitAI download URL.
wget -c -O /runpod-volume/models/loras/sketchZTurbo.safetensors \
    "https://huggingface.co/<AUTHOR>/<REPO>/resolve/main/sketchZTurbo.safetensors"
```

### 1c — Verify

```bash
ls -lh /runpod-volume/models/unet/
ls -lh /runpod-volume/models/vae/
ls -lh /runpod-volume/models/clip/
ls -lh /runpod-volume/models/loras/
```

---

## 2 — Build and push the Docker image

```bash
cd runpod/

docker build -t your-dockerhub-user/zturbolorapet:latest .
docker push your-dockerhub-user/zturbolorapet:latest
```

---

## 3 — Deploy on RunPod Serverless

1. **New Endpoint** → select *Serverless*
2. Container image: `your-dockerhub-user/zturbolorapet:latest`
3. Container disk: **20 GB** (ComfyUI + Python — models live on the volume)
4. Attach the Network Volume you prepared in step 1
5. Environment variable: `VOLUME_PATH=/runpod-volume` (already set in Dockerfile, but confirm here)
6. Set GPU type, min/max workers, idle timeout as desired

---

## 4 — API reference

### Endpoint

```
POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
Authorization: Bearer <RUNPOD_API_KEY>
Content-Type: application/json
```

### Input schema

All fields are **optional**. Omitting a field keeps the workflow default.

| Field | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | *(long Shiba Inu prompt)* | Positive text prompt. Include the `w3t1nk` token to activate the LoRA. |
| `negative_prompt` | string | `""` | Negative text prompt |
| `width` | int | `1024` | Output width in pixels |
| `height` | int | `1024` | Output height in pixels |
| `steps` | int | `15` | KSampler denoising steps |
| `cfg` | float | `1.0` | Classifier-free guidance scale |
| `seed` | int | random | RNG seed (`-1` = random) |
| `lora_name` | string | `sketchZTurbo.safetensors` | LoRA filename (must exist in `models/loras/`) |
| `lora_strength` | float | `0.5` | LoRA strength applied to both model and CLIP |
| `batch_size` | int | `1` | Number of images per request |

### Example request

```json
{
  "input": {
    "prompt": "w3t1nk A golden retriever wearing a knight's armor, dramatic lighting, ink wash style",
    "negative_prompt": "blurry, watermark, text",
    "width": 1024,
    "height": 1024,
    "steps": 15,
    "cfg": 1.0,
    "seed": 42
  }
}
```

### Example response

```json
{
  "id": "...",
  "status": "COMPLETED",
  "output": {
    "images": [
      {
        "index": 0,
        "data": "<base64-encoded PNG>",
        "format": "png"
      }
    ],
    "prompt_id": "...",
    "seed": 42
  }
}
```

Decode the image in Python:

```python
import base64, json, requests

resp = requests.post(
    "https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync",
    headers={"Authorization": "Bearer <KEY>", "Content-Type": "application/json"},
    json={"input": {"prompt": "w3t1nk a fluffy corgi astronaut", "seed": 1234}},
)
result = resp.json()
for img in result["output"]["images"]:
    with open(f"out_{img['index']}.png", "wb") as f:
        f.write(base64.b64decode(img["data"]))
```

---

## 5 — Notes

- **`w3t1nk` trigger token** — the `sketchZTurbo` LoRA is activated by including `w3t1nk` in the prompt. Keep it at the start.
- **LoRA wiring** — in this workflow the LoRA model output feeds `ModelSamplingAuraFlow` (shift=3), which currently has no downstream connection. The LoRA CLIP output feeds the *negative* encoder. This matches the original workflow exactly and is intentional.
- **`res_multistep` sampler** — built into ComfyUI core as of v0.2+; no custom nodes required.
- **Custom nodes** — none required. All nodes use `comfy-core`.
- The `output/` folder on the volume accumulates generated images; clean it periodically if disk space is a concern.
