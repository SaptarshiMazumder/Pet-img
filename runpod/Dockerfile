# ============================================================
# ZTurboLoraPet — RunPod Serverless Worker
# Base: CUDA 12.1, Python 3.11
# ============================================================
FROM runpod/base:0.6.2-cuda12.1.0

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# ------------------------------------------------------------
# System packages
# ------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        wget \
        curl \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# PyTorch (CUDA 12.1)
# ------------------------------------------------------------
RUN pip install --no-cache-dir \
    torch==2.3.1 \
    torchvision==0.18.1 \
    torchaudio==2.3.1 \
    --index-url https://download.pytorch.org/whl/cu121

# ------------------------------------------------------------
# ComfyUI
# ------------------------------------------------------------
RUN git clone https://github.com/comfyanonymous/ComfyUI /comfyui
WORKDIR /comfyui
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# RunPod SDK + R2 upload
# ------------------------------------------------------------
RUN pip install --no-cache-dir runpod==1.7.3 boto3==1.34.69

# ------------------------------------------------------------
# Create model directory stubs (real content lives on the
# network volume; handler.py replaces these with symlinks)
# ------------------------------------------------------------
RUN mkdir -p \
    /comfyui/models/unet \
    /comfyui/models/vae \
    /comfyui/models/clip \
    /comfyui/models/loras \
    /comfyui/output

# ------------------------------------------------------------
# Copy worker files
# ------------------------------------------------------------
COPY workflow_api.json /app/workflow_api.json
COPY handler.py /app/handler.py

# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------
ENV PYTHONUNBUFFERED=1
ENV VOLUME_PATH=/runpod-volume

# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------
CMD ["python", "-u", "/app/handler.py"]
