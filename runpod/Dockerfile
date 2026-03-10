# ============================================================
# ZTurboLoraPet — RunPod Serverless Worker
# Base: runpod/worker-comfyui (ComfyUI + Python + CUDA pre-installed)
# ============================================================
FROM runpod/worker-comfyui:5.7.1-base

# R2 client + RunPod SDK
RUN pip install --no-cache-dir boto3 runpod==1.7.3

# App code
COPY workflow_api.json /app/workflow_api.json
COPY handler.py /app/handler.py
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

WORKDIR /comfyui

ENV PYTHONUNBUFFERED=1
ENV VOLUME_PATH=/workspace

CMD ["python3", "-u", "/app/handler.py"]
