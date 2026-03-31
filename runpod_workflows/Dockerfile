# ============================================================
# Pet Generator — RunPod Serverless Worker (multi-workflow)
# Base: runpod/worker-comfyui (ComfyUI + Python + CUDA pre-installed)
# Supports: zturbo (ZTurboLoraPet) and uso (Flux1-Dev USO)
# ============================================================
FROM runpod/worker-comfyui:5.7.1-base

# R2 client (runpod SDK already in base image)
RUN pip install --no-cache-dir boto3 requests

# Update ComfyUI to get nodes_model_patch.py (USOStyleReference, ModelPatchLoader,
# FluxKontextMultiReferenceLatentMethod, ReferenceLatent — added in v0.3.52+)
RUN cd /comfyui && git fetch origin master && git reset --hard FETCH_HEAD && \
    pip install --no-cache-dir -r requirements.txt

# App code
COPY workflow_api.json     /workflow_api.json
COPY workflow_api_uso.json /workflow_api_uso.json
COPY handler.py            /handler.py
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

WORKDIR /comfyui

ENV PYTHONUNBUFFERED=1
