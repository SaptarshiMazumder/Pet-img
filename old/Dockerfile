# ---- Base image ----
FROM python:3.11-slim

# ---- System deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Working directory ----
WORKDIR /app

# ---- Python deps ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- App files ----
COPY prompt_generator.py .
COPY handler.py .
COPY lora_templates.json .

# ---- Workflows folder (optional — only needed if your code reads workflow files) ----
COPY Workflows/ ./Workflows/

# ---- RunPod serverless entry point ----
CMD ["python", "-u", "handler.py"]
