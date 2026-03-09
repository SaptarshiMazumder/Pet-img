# ZTurboLoraPet — RunPod Serverless Worker

ComfyUI serverless API wrapping the **ZTurboLoraPet** workflow.
Stack: `z_image_turbo_bf16` UNET · Qwen3-4B CLIP (lumina2) · FLUX VAE · two chained LoRAs.

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
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors" \
  -O /runpod-volume/models/unet/z_image_turbo_bf16.safetensors
```

#### VAE — FLUX ae.safetensors

```bash
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors" \
  -O /runpod-volume/models/vae/ae.safetensors
```

#### CLIP — Qwen3 4B (lumina2 format)

```bash
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" \
  -O /runpod-volume/models/clip/qwen_3_4b.safetensors
```

#### LoRA 1 — wetInkZTurbo (style, strength 0.3)

Applied first in the chain. Provides the wet ink / sumi-e base style. Trigger token: `w3t1nk`.

```bash
wget -c -O /runpod-volume/models/loras/wetInkZTurbo.safetensors \
    "https://huggingface.co/<AUTHOR>/<REPO>/resolve/main/wetInkZTurbo.safetensors"
```

#### LoRA 2 — ukiyoeZTurbo (style, strength 0.5)

Applied second, on top of LoRA 1. Adds ukiyo-e woodblock print aesthetics.
Its CLIP output feeds the positive encoder; wetInkZTurbo CLIP feeds the negative encoder.

```bash
wget -c -O /runpod-volume/models/loras/ukiyoeZTurbo.safetensors \
    "https://huggingface.co/<AUTHOR>/<REPO>/resolve/main/ukiyoeZTurbo.safetensors"
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

docker build -t raj1145/pet-generator-worker:latest .
docker push raj1145/pet-generator-worker:latest
```

Or trigger the GitHub Action: **Actions → Build Pet Generator Worker → Run workflow**.

---

## 3 — Deploy on RunPod Serverless

1. **New Endpoint** → select *Serverless*
2. Container image: `raj1145/pet-generator-worker:<tag>`
3. Container disk: **20 GB** (ComfyUI + Python — models live on the volume)
4. Attach the Network Volume you prepared in step 1
5. Set the following environment variables:

| Variable | Description |
|---|---|
| `VOLUME_PATH` | `/runpod-volume` |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | R2 API token key ID |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret |
| `R2_BUCKET_NAME` | R2 bucket name |
| `R2_PUBLIC_BASE_URL` | *(optional)* custom public domain, e.g. `https://images.yourdomain.com` |

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
| `prompt` | string | *(Shiba Inu scholar prompt)* | Positive prompt. Must include `w3t1nk` to activate the wet ink LoRA. |
| `negative_prompt` | string | `""` | Negative text prompt |
| `width` | int | `1024` | Output width in pixels |
| `height` | int | `1024` | Output height in pixels |
| `steps` | int | `15` | Pass 1 denoising steps |
| `cfg` | float | `1.0` | Classifier-free guidance scale |
| `seed` | int | random | RNG seed (`-1` = random) |
| `batch_size` | int | `1` | Number of images per request |
| `lora_name` | string | `wetInkZTurbo.safetensors` | LoRA 1 filename (wet ink style) |
| `lora_strength` | float | `0.3` | LoRA 1 strength (model + clip) |
| `lora2_name` | string | `ukiyoeZTurbo.safetensors` | LoRA 2 filename (ukiyo-e style) |
| `lora2_strength` | float | `0.5` | LoRA 2 strength (model + clip) |
| `upscale_factor` | float | `1.25` | Latent upscale multiplier |
| `upscale_steps` | int | `8` | Pass 2 refine steps |
| `upscale_denoise` | float | `0.7` | Pass 2 denoise strength |
| `upscale_sampler` | string | `dpmpp_sde` | Pass 2 sampler |
| `upscale_scheduler` | string | `beta` | Pass 2 scheduler |

### Example request

```json
{
  "input": {
    "prompt": "w3t1nk A golden retriever wearing a shogun helmet, moonlit garden, cherry blossoms",
    "negative_prompt": "blurry, watermark, text",
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
        "url": "https://your-bucket.r2.cloudflarestorage.com/pet-generator/<prompt_id>/42_0.png",
        "key": "pet-generator/<prompt_id>/42_0.png"
      }
    ],
    "prompt_id": "...",
    "seed": 42,
    "upscale_denoise": 0.7,
    "upscale_sampler": "dpmpp_sde",
    "upscale_scheduler": "beta"
  }
}
```

---

## 5 — Notes

- **`w3t1nk` trigger token** — required in the prompt to activate `wetInkZTurbo`. Keep it at the start.
- **LoRA chain** — `wetInkZTurbo (0.3)` → `ukiyoeZTurbo (0.5)` → `ModelSamplingAuraFlow (shift=3)` → both KSamplers. `ukiyoeZTurbo` CLIP feeds the positive encoder; `wetInkZTurbo` CLIP feeds the negative encoder.
- **`res_multistep` sampler** — built into ComfyUI core; no custom nodes required.
- **Custom nodes** — none. All nodes use `comfy-core`.
- The `output/` folder on the volume accumulates generated images; clean it periodically if disk space is a concern.
