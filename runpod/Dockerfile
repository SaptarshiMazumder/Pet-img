# ============================================================
# ZTurboLoraPet — RunPod Serverless Worker
# Base: runpod/worker-comfyui (ComfyUI + Python + CUDA pre-installed)
# ============================================================
FROM runpod/worker-comfyui:5.7.1-base

# R2 client (runpod SDK already in base image)
RUN pip install --no-cache-dir boto3 requests

# App code — handler at root so base image entrypoint can find it
COPY workflow_api.json /workflow_api.json
COPY handler.py /handler.py
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

WORKDIR /comfyui

ENV PYTHONUNBUFFERED=1
