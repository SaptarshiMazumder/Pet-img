# Pet Generator — RunPod Serverless Worker (multi-workflow)

One Docker image, two ComfyUI workflows. Select at runtime via the `workflow_type` input field.

| `workflow_type` | Workflow | Model |
|---|---|---|
| `"zturbo"` *(default)* | ZTurboLoraPet — wetInk + ukiyoe LoRAs | `z_image_turbo_bf16` + Qwen3-4B CLIP |
| `"uso"` | Flux1-Dev USO — style/subject reference transfer | `flux1-dev-fp8` + USO LoRA + projector |

---

## Repository layout

```
runpod_workflows/
├── Dockerfile               # Container definition (both workflows)
├── handler.py               # RunPod serverless handler
├── workflow_api.json        # ZTurbo ComfyUI API workflow
├── workflow_api_uso.json    # Flux1-Dev USO ComfyUI API workflow
├── extra_model_paths.yaml   # ComfyUI model path config (network volume)
└── README.md                # This file
```

---

## 1 — Download models

### Network Volume setup (recommended)
> Create a Network Volume (≥ 80 GB), attach to a temporary pod, SSH in.
> Set `VOLUME_PATH=/workspace` on the serverless endpoint.

#### Create directories

```bash
mkdir -p /workspace/models/diffusion_models
mkdir -p /workspace/models/text_encoders
mkdir -p /workspace/models/vae
mkdir -p /workspace/models/loras
mkdir -p /workspace/models/clip_vision
mkdir -p /workspace/models/model_patches
mkdir -p /workspace/output
```

---

### ZTurbo workflow models

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
wget "https://civitai.com/api/download/models/2533715?type=Model&format=SafeTensor&token=<YOUR_CIVITAI_TOKEN>" \
  -O /workspace/models/loras/wetInkZTurbo.safetensors
```

#### LoRA 2 — ukiyoeZTurbo (trigger: `Ukiyo-e`, default strength 0.5)
```bash
wget "https://civitai.com/api/download/models/2457871?type=Model&format=SafeTensor&token=<YOUR_CIVITAI_TOKEN>" \
  -O /workspace/models/loras/ukiyoeZTurbo.safetensors
```

---

### USO workflow models

#### UNET — Flux1-Dev fp8
```bash
wget "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" \
  -O /workspace/models/diffusion_models/flux1-dev-fp8.safetensors
```

#### VAE — FLUX ae (shared with ZTurbo, already downloaded above)

#### CLIP — clip_l
```bash
wget "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" \
  -O /workspace/models/text_encoders/clip_l.safetensors
```

#### CLIP — T5-XXL fp8
```bash
wget "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" \
  -O /workspace/models/text_encoders/t5xxl_fp8_e4m3fn.safetensors
```

#### CLIP Vision — SigCLIP ViT-L/14-384
```bash
wget "https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors" \
  -O /workspace/models/clip_vision/sigclip_vision_patch14_384.safetensors
```

#### LoRA — USO Flux1 DiT
```bash
wget "https://huggingface.co/<USO_REPO>/resolve/main/uso-flux1-dit-lora-v1.safetensors" \
  -O /workspace/models/loras/uso-flux1-dit-lora-v1.safetensors
```

#### Model Patch — USO Flux1 Projector
```bash
wget "https://huggingface.co/<USO_REPO>/resolve/main/uso-flux1-projector-v1.safetensors" \
  -O /workspace/models/model_patches/uso-flux1-projector-v1.safetensors
```

---

## 2 — Build and push the Docker image

```bash
cd runpod_workflows/

docker build -t raj1145/pet-generator-worker:latest .
docker push raj1145/pet-generator-worker:latest
```

---

## 3 — Deploy on RunPod Serverless

1. **New Endpoint** → select *Serverless*
2. Container image: `raj1145/pet-generator-worker:<tag>`
3. Container disk: **20 GB**
4. Attach the Network Volume from step 1
5. Set environment variables:

| Variable | Description |
|---|---|
| `VOLUME_PATH` | `/workspace` |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | R2 API token key ID |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret |
| `R2_BUCKET_NAME` | R2 bucket name |
| `R2_PUBLIC_BASE_URL` | *(optional)* custom public domain |

---

## 4 — API reference

### Endpoint

```
POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
Authorization: Bearer <RUNPOD_API_KEY>
Content-Type: application/json
```

---

### ZTurbo workflow (`workflow_type: "zturbo"`)

All fields optional. Omitting keeps the workflow default.

| Field | Type | Default | Description |
|---|---|---|---|
| `workflow_type` | string | `"zturbo"` | Set to `"zturbo"` or omit |
| `prompt` | string | *(Shiba Inu scholar prompt)* | Must include `w3t1nk` to activate the wet ink LoRA |
| `negative_prompt` | string | `""` | Negative text prompt |
| `width` | int | `1024` | Output width |
| `height` | int | `1024` | Output height |
| `steps` | int | `15` | Pass 1 denoising steps |
| `cfg` | float | `1.0` | Guidance scale |
| `seed` | int | random | RNG seed (`-1` = random) |
| `batch_size` | int | `1` | Images per request |
| `lora_name` | string | `wetInkZTurbo.safetensors` | LoRA 1 filename |
| `lora_strength` | float | `0.3` | LoRA 1 strength |
| `lora2_name` | string | `ukiyoeZTurbo.safetensors` | LoRA 2 filename |
| `lora2_strength` | float | `0.5` | LoRA 2 strength |
| `upscale_factor` | float | `1.25` | Latent upscale multiplier |
| `upscale_steps` | int | `8` | Pass 2 refine steps |
| `upscale_denoise` | float | `0.7` | Pass 2 denoise strength |
| `upscale_sampler` | string | `dpmpp_sde` | Pass 2 sampler |
| `upscale_scheduler` | string | `beta` | Pass 2 scheduler |

**Example:**
```json
{
  "input": {
    "workflow_type": "zturbo",
    "prompt": "w3t1nk A golden retriever wearing a shogun helmet",
    "seed": 42
  }
}
```

---

### USO workflow (`workflow_type: "uso"`)

All fields optional except reference images (the defaults are placeholder filenames).

| Field | Type | Default | Description |
|---|---|---|---|
| `workflow_type` | string | — | **Required**: `"uso"` |
| `prompt` | string | `"dog sitting under a tree"` | Generation prompt |
| `width` | int | `1024` | Output width |
| `height` | int | `1024` | Output height |
| `steps` | int | `20` | Denoising steps |
| `cfg` | float | `1.0` | Guidance scale |
| `guidance` | float | `2.0` | FluxGuidance strength |
| `seed` | int | random | RNG seed (`-1` = random) |
| `batch_size` | int | `1` | Images per request |
| `lora_name` | string | `uso-flux1-dit-lora-v1.safetensors` | USO DiT LoRA filename |
| `lora_strength` | float | `1.0` | USO LoRA strength |
| `style_image_1` | string (URL) | — | Style reference image URL |
| `subject_image` | string (URL) | — | Subject reference image URL (encoded as reference latent) |

**Example:**
```json
{
  "input": {
    "workflow_type": "uso",
    "prompt": "a cat lounging in a sunny garden",
    "style_image_1": "https://example.com/style.png",
    "subject_image": "https://example.com/my_pet.jpg",
    "seed": 99
  }
}
```

---

### Response (both workflows)

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
    "workflow_type": "uso"
  }
}
```

ZTurbo responses also include `upscale_denoise`, `upscale_sampler`, `upscale_scheduler`.

---

## 5 — Notes

### ZTurbo
- **`w3t1nk` trigger** — required in the prompt to activate `wetInkZTurbo`.
- **Custom nodes** — none. All nodes use `comfy-core`.

### USO
- **Reference images** — pass public URLs via `style_image_1`, `style_image_2`, `subject_image`. The handler downloads them and uploads to ComfyUI's input directory before queuing.
- **Subject reference** — `subject_image` is VAE-encoded as a `ReferenceLatent` and fed through `FluxKontextMultiReferenceLatentMethod` (method: `uxo/uno`).
- **Required custom nodes** — `USOStyleReference`, `ModelPatchLoader`, `ReferenceLatent`, `FluxKontextMultiReferenceLatentMethod` must be installed in the ComfyUI base image.
