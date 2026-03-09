# Pet Generator — ComfyUI Prompt Generator

Analyzes an animal image with Gemini Vision and generates ComfyUI-ready prompts based on LoRA templates.

---

## Project Structure

```
Pet-generator/
├── prompt_generator.py     # Core logic — run locally
├── lora_templates.json     # LoRA template config
├── .env                    # API keys (local only)
├── Workflows/
│   ├── flux_redux_workflow.json           # FLUX1 + Redux + LoRA workflow
│   ├── king_cat_sdxl_workflow.json        # SDXL + IPAdapter workflow
│   └── king_cat_oilpainting_workflow.json # FLUX1 + Redux oil painting workflow
└── deploy/
    ├── Dockerfile          # Container for RunPod serverless
    ├── handler.py          # RunPod serverless entry point
    └── requirements.txt    # Python dependencies
```

---

## Local Usage

### 1. Install dependencies
```bash
pip install google-generativeai requests python-dotenv
```

### 2. Set your API key in `.env`
```
GEMINI_API_KEY=your_key_here
```

### 3. Configure `prompt_generator.py`
```python
IMAGE_PATH = r"C:\Users\you\Downloads\your_pet.jpg"
TEMPLATE_INDEX = None   # None = interactive, or set an int e.g. 0
ALL_TEMPLATES = False   # True = generate for every template
```

### 4. Run
```bash
python prompt_generator.py
```

---

## RunPod Serverless Deployment

### 1. Build the Docker image (run from project root)
```bash
docker build -f deploy/Dockerfile -t your-dockerhub-user/pet-generator:latest .
docker push your-dockerhub-user/pet-generator:latest
```

### 2. Create RunPod Serverless endpoint
1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click **New Endpoint**
3. Set Docker image: `your-dockerhub-user/pet-generator:latest`
4. Under **Environment Variables**, add: `GEMINI_API_KEY = your_key`
5. GPU: **None (CPU)** — no GPU needed, this only calls Gemini API
6. Deploy

### 3. API Input / Output

**Input:**
```json
{
  "input": {
    "image_url": "https://example.com/dog.jpg",
    "template_index": 1,
    "example_prompt_index": 0
  }
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `image_url` | string | — | Public URL of the animal image |
| `image_base64` | string | — | Base64-encoded image (alternative to url) |
| `image_mime_type` | string | `image/jpeg` | Required with `image_base64` |
| `template_index` | int | — | Run single template by index. Omit to run all. |
| `all_templates` | bool | `false` | Explicitly run all templates |
| `example_prompt_index` | int | `0` | Which example prompt to use when multiple exist |

**Output:**
```json
{
  "animal_description": "A golden retriever with dense honey-gold fur...",
  "results": [
    {
      "lora": "Japanese Ink-Wash",
      "baseModel": "FLUX1",
      "workflow": "Workflows/flux_redux_workflow.json",
      "triggerWord": "",
      "prompt": "A golden retriever with dense honey-gold fur sits regally..."
    }
  ]
}
```

---

## Workflow Setup — Model Downloads

Run all commands on your ComfyUI server (e.g. RunPod). Replace `/workspace/runpod-slim/ComfyUI` with your actual ComfyUI path.

---

### Workflow 1 — FLUX1 Redux (`flux_redux_workflow.json`)

Used by: **eastern painting**, **Japanese Ink-Wash**, **Oil Painting Style**

**Models required:**
| File | Folder | Source |
|---|---|---|
| `flux1-dev-fp8.safetensors` | `models/unet/` | HuggingFace (requires token) |
| `clip_l.safetensors` | `models/clip/` | HuggingFace |
| `t5xxl_fp8_e4m3fn.safetensors` | `models/clip/` | HuggingFace |
| `ae.safetensors` | `models/vae/` | HuggingFace (requires token) |
| `sigclip_vision_patch14_384.safetensors` | `models/clip_vision/` | HuggingFace |
| `flux1-redux-dev.safetensors` | `models/style_models/` | HuggingFace (requires token) |
| `inkPaintFlux.safetensors` *(or your LoRA)* | `models/loras/` | CivitAI |

**Download commands:**

```bash
# Set your HuggingFace token (required for FLUX gated models)
export HF_TOKEN=your_huggingface_token_here

COMFY=/workspace/runpod-slim/ComfyUI

# Create folders
mkdir -p $COMFY/models/unet
mkdir -p $COMFY/models/clip
mkdir -p $COMFY/models/vae
mkdir -p $COMFY/models/clip_vision
mkdir -p $COMFY/models/style_models
mkdir -p $COMFY/models/loras

# FLUX1 dev (fp8) — UNet
wget -q --header="Authorization: Bearer $HF_TOKEN" \
  -O $COMFY/models/unet/flux1-dev-fp8.safetensors \
  "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors"

# CLIP encoders
wget -q -O $COMFY/models/clip/clip_l.safetensors \
  "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors"

wget -q -O $COMFY/models/clip/t5xxl_fp8_e4m3fn.safetensors \
  "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors"

# VAE
wget -q --header="Authorization: Bearer $HF_TOKEN" \
  -O $COMFY/models/vae/ae.safetensors \
  "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors"

# SigCLIP vision encoder (for Redux)
wget -q -O $COMFY/models/clip_vision/sigclip_vision_patch14_384.safetensors \
  "https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors"

# FLUX Redux style model
wget -q --header="Authorization: Bearer $HF_TOKEN" \
  -O $COMFY/models/style_models/flux1-redux-dev.safetensors \
  "https://huggingface.co/black-forest-labs/FLUX.1-Redux-dev/resolve/main/flux1-redux-dev.safetensors"

# LoRA — inkPaintFlux (download from CivitAI, replace URL with actual model page download link)
# wget -q -O $COMFY/models/loras/inkPaintFlux.safetensors "https://civitai.com/api/download/models/YOUR_MODEL_ID"
```

> **Note:** For FLUX gated models, get your HF token at https://huggingface.co/settings/tokens and accept the FLUX.1-dev license at https://huggingface.co/black-forest-labs/FLUX.1-dev

---

### Workflow 2 — SDXL + IPAdapter (`king_cat_sdxl_workflow.json`)

Used by: **glass ink painting**

**Models required:**
| File | Folder | Source |
|---|---|---|
| `dreamshaperXL_v21TurboDPMSDE.safetensors` | `models/checkpoints/` | CivitAI |
| `INK_Glass_XL.safetensors` | `models/loras/` | CivitAI |
| `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` | `models/clip_vision/` | HuggingFace |
| `ip-adapter-plus_sdxl_vit-h.safetensors` | `models/ipadapter/` | HuggingFace |

**Download commands:**

```bash
COMFY=/workspace/runpod-slim/ComfyUI

# Create folders
mkdir -p $COMFY/models/checkpoints
mkdir -p $COMFY/models/loras
mkdir -p $COMFY/models/clip_vision
mkdir -p $COMFY/models/ipadapter

# CLIP Vision (for IPAdapter)
wget -q -O $COMFY/models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors \
  "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors"

# IPAdapter PLUS for SDXL
wget -q -O $COMFY/models/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors \
  "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors"

# DreamShaper XL (download from CivitAI — replace URL with actual download link)
# Model page: https://civitai.com/models/112902/dreamshaper-xl
# wget -q -O $COMFY/models/checkpoints/dreamshaperXL_v21TurboDPMSDE.safetensors "https://civitai.com/api/download/models/YOUR_MODEL_ID"

# INK Glass XL LoRA (download from CivitAI — replace URL with actual download link)
# wget -q -O $COMFY/models/loras/INK_Glass_XL.safetensors "https://civitai.com/api/download/models/YOUR_MODEL_ID"
```

> **CivitAI downloads:** Go to the model page, click Download, copy the link (you may need a CivitAI API token). Add `--header="Authorization: Bearer $CIVITAI_TOKEN"` if required.

---

### Workflow 3 — FLUX Oil Painting (`king_cat_oilpainting_workflow.json`)

Used by: **Oil Painting Style**

**Models required:**
| File | Folder | Source |
|---|---|---|
| `renaissanceOilPaintingFlux.safetensors` | `models/unet/` | CivitAI |
| `clip_l.safetensors` | `models/clip/` | HuggingFace |
| `t5xxl_fp8_e4m3fn.safetensors` | `models/clip/` | HuggingFace |
| `ae.safetensors` | `models/vae/` | HuggingFace (requires token) |
| `sigclip_vision_patch14_384.safetensors` | `models/clip_vision/` | HuggingFace |
| `flux1-redux-dev.safetensors` | `models/style_models/` | HuggingFace (requires token) |

> **Note:** `clip_l`, `t5xxl_fp8_e4m3fn`, `ae`, `sigclip_vision_patch14_384`, and `flux1-redux-dev` are shared with Workflow 1. Skip any already downloaded.

**Download commands:**

```bash
export HF_TOKEN=your_huggingface_token_here

COMFY=/workspace/runpod-slim/ComfyUI

# Create folders
mkdir -p $COMFY/models/unet
mkdir -p $COMFY/models/clip
mkdir -p $COMFY/models/vae
mkdir -p $COMFY/models/clip_vision
mkdir -p $COMFY/models/style_models

# CLIP encoders (shared with Workflow 1 — skip if already downloaded)
wget -q -O $COMFY/models/clip/clip_l.safetensors \
  "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors"

wget -q -O $COMFY/models/clip/t5xxl_fp8_e4m3fn.safetensors \
  "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors"

# VAE (shared with Workflow 1 — skip if already downloaded)
wget -q --header="Authorization: Bearer $HF_TOKEN" \
  -O $COMFY/models/vae/ae.safetensors \
  "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors"

# SigCLIP vision encoder (shared with Workflow 1 — skip if already downloaded)
wget -q -O $COMFY/models/clip_vision/sigclip_vision_patch14_384.safetensors \
  "https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors"

# FLUX Redux style model (shared with Workflow 1 — skip if already downloaded)
wget -q --header="Authorization: Bearer $HF_TOKEN" \
  -O $COMFY/models/style_models/flux1-redux-dev.safetensors \
  "https://huggingface.co/black-forest-labs/FLUX.1-Redux-dev/resolve/main/flux1-redux-dev.safetensors"

# Renaissance Oil Painting FLUX UNet (download from CivitAI — replace URL with actual download link)
# wget -q -O $COMFY/models/unet/renaissanceOilPaintingFlux.safetensors "https://civitai.com/api/download/models/YOUR_MODEL_ID"
```

---

## Adding / Editing Templates (`lora_templates.json`)

```json
{
  "baseModel": "FLUX1",
  "loraName": "My LoRA",
  "workflow": "Workflows/flux_redux_workflow.json",
  "triggerWord": "my trigger",
  "examplePrompts": [
    "An example prompt written in the exact style this LoRA produces..."
  ]
}
```

| Field | Notes |
|---|---|
| `examplePrompts` | Empty `[]` = generate tags from scratch. One entry = auto-used. Multiple = user picks at runtime. |
| `triggerWord` | Leave blank if the LoRA has no trigger word |
| `workflow` | Path to the ComfyUI workflow JSON, relative to project root |
