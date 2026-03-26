# ============================================================
# Pet Generator — RunPod Serverless Worker (multi-workflow)
# Base: runpod/worker-comfyui (ComfyUI + Python + CUDA pre-installed)
# Supports: zturbo (ZTurboLoraPet) and uso (Flux1-Dev USO)
# ============================================================
FROM runpod/worker-comfyui:5.7.1-base

# R2 client (runpod SDK already in base image)
RUN pip install --no-cache-dir boto3 requests

# App code
COPY workflow_api.json     /workflow_api.json
COPY workflow_api_uso.json /workflow_api_uso.json
COPY handler.py            /handler.py
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

WORKDIR /comfyui

ENV PYTHONUNBUFFERED=1
