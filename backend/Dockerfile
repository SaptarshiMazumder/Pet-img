# ============================================================
# Pet Generator — Backend API
# Flask app on port 5000
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Build context: repo root
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --timeout 120 backend.app:app"]
