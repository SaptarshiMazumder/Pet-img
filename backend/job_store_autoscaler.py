"""Autoscaler HTTP job store — used as fallback when Firestore doesn't have the job."""
import json
import os
import urllib.request
from urllib.error import URLError


def _scaler_url(path: str) -> str:
    return os.environ.get("AUTOSCALER_URL", "http://localhost:5001") + path


def _req(method: str, path: str, body: dict | None = None) -> dict | None:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(_scaler_url(path), data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except URLError as exc:
        print(f"[job-store-autoscaler] {method} {path} failed: {exc}")
        return None


class AutoscalerJobStore:
    def get(self, job_id: str) -> dict | None:
        return _req("GET", f"/job/{job_id}")


job_store = AutoscalerJobStore()
