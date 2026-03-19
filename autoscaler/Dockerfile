# ============================================================
# Pet Generator — Autoscaler
# RunPod scaling + Flask dashboard on port 5001
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Build context: repo root
COPY autoscaler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY autoscaler/ ./autoscaler/
COPY backend/*.json ./backend/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 5001

CMD ["python", "-m", "autoscaler.run"]
