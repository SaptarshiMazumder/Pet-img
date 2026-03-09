FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt deploy/requirements.txt
RUN pip install --no-cache-dir -r deploy/requirements.txt

COPY prompt_generator.py .
COPY deploy/handler.py .
COPY lora_templates.json .
COPY Workflows/ ./Workflows/

# Copy .env for local testing — in production set env vars via RunPod UI instead
COPY .env .

CMD ["python", "-u", "handler.py"]
