"""HTTP client for the job store in the scaler service.

Interface is identical to the old in-memory JobStore — callers don't change.
"""
import json
import os
import urllib.request
from urllib.error import URLError


def _scaler_url(path: str) -> str:
    return os.environ.get("AUTOSCALER_URL", "http://localhost:5001") + path


def _req(method: str, path: str, body: dict | None = None) -> dict | None:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(
        _scaler_url(path),
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except URLError as exc:
        print(f"[job-store] {method} {path} failed: {exc}")
        return None


class JobStore:
    def create(self, job_id: str) -> None:
        _req("POST", "/job", {"job_id": job_id})

    def update(self, job_id: str, **fields) -> None:
        _req("PATCH", f"/job/{job_id}", fields)

    def get(self, job_id: str) -> dict | None:
        return _req("GET", f"/job/{job_id}")


# Module-level singleton — drop-in replacement for the old in-memory store
job_store = JobStore()
