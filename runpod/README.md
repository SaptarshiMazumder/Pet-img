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

## 1 — Download models

Models can go on a **Network Volume** (recommended for serverless — persists across cold starts)
or directly onto a **RunPod Pod** (faster to test, lost when the pod is deleted).
Commands below are written out in full for both locations.

---

### Option A — Network Volume
> Create a Network Volume (≥ 50 GB) in the RunPod console, attach it to a temporary GPU pod,
> SSH in, and run these commands. Set `VOLUME_PATH=/workspace` on the serverless endpoint.

#### Create directories

```bash
mkdir -p /workspace/models/diffusion_models
mkdir -p /workspace/models/text_encoders
mkdir -p /workspace/models/unet
mkdir -p /workspace/models/vae
mkdir -p /workspace/models/clip
mkdir -p /workspace/models/loras
mkdir -p /workspace/output
```

#### UNET — Z-Image Turbo (bf16)

```bash
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors" \
  -O /workspace/models/diffusion_models/z_image_turbo_bf16.safetensors
```

#### VAE — FLUX ae

```bash
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors" \
  -O /workspace/models/vae/ae.safetensors
```

#### CLIP — Qwen3 4B (lumina2)

```bash
wget "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" \
  -O /workspace/models/text_encoders/qwen_3_4b.safetensors
```

#### LoRA 1 — wetInkZTurbo (trigger: `w3t1nk`, default strength 0.3)

```bash
wget "https://civitai.com/api/download/models/2533715?type=Model&format=SafeTensor&token=32935a7da15c304c648fd5d1633002fd" \
  -O workspace/models/loras/wetInkZTurbo.safetensors"
```

#### LoRA 2 — ukiyoeZTurbo (trigger: `Ukiyo-e`, default strength 0.5)

```bash
wget "https://civitai.com/api/download/models/2457871?type=Model&format=SafeTensor&token=32935a7da15c304c648fd5d1633002fd" \
  -O workspace/models/loras/ukiyoeZTurbo.safetensors
```

#### Verify

```bash
ls -lh /workspace/models/unet/
ls -lh /workspace/models/diffusion_models
ls -lh /workspace/models/text_encoders
ls -lh /workspace/models/vae/
ls -lh /workspace/models/clip/
ls -lh /workspace/models/loras/
```

---

### Option B — RunPod Pod (direct, no network volume)
> SSH into your running pod. ComfyUI lives at `/workspace/runpod-slim/ComfyUI/`.
> Models downloaded here are lost when the pod is terminated.

#### Create directories

```bash
mkdir -p /workspace/runpod-slim/ComfyUI/models/unet
mkdir -p /workspace/runpod-slim/ComfyUI/models/vae
mkdir -p /workspace/runpod-slim/ComfyUI/models/clip
mkdir -p /workspace/runpod-slim/ComfyUI/models/loras
mkdir -p /workspace/runpod-slim/ComfyUI/output
```

#### UNET — Z-Image Turbo (bf16)

```bash
wget -c -O /workspace/runpod-slim/ComfyUI/models/unet/z_image_turbo_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors"
```

#### VAE — FLUX ae

```bash
wget -c -O /workspace/runpod-slim/ComfyUI/models/vae/ae.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors"
```

#### CLIP — Qwen3 4B (lumina2)

```bash
wget -c -O /workspace/runpod-slim/ComfyUI/models/clip/qwen_3_4b.safetensors \
  "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors"
```

#### LoRA 1 — wetInkZTurbo (trigger: `w3t1nk`, default strength 0.3)

```bash
wget -c -O /workspace/runpod-slim/ComfyUI/models/loras/wetInkZTurbo.safetensors \
  "https://huggingface.co/<AUTHOR>/<REPO>/resolve/main/wetInkZTurbo.safetensors"
```

#### LoRA 2 — ukiyoeZTurbo (trigger: `Ukiyo-e`, default strength 0.5)

```bash
wget -c -O /workspace/runpod-slim/ComfyUI/models/loras/ukiyoeZTurbo.safetensors \
  "https://huggingface.co/<AUTHOR>/<REPO>/resolve/main/ukiyoeZTurbo.safetensors"
```

#### Verify

```bash
ls -lh /workspace/runpod-slim/ComfyUI/models/unet/
ls -lh /workspace/runpod-slim/ComfyUI/models/vae/
ls -lh /workspace/runpod-slim/ComfyUI/models/clip/
ls -lh /workspace/runpod-slim/ComfyUI/models/loras/
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
| `VOLUME_PATH` | `/workspace` |
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
