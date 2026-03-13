"""
RunPod job client — submit jobs and poll for results.
"""
import json
import time
import urllib.request

from backend.runpod.runpod_config import (
    RUNPOD_API_KEY,
    RUNPOD_ENDPOINT_ID,
    RUNPOD_API_BASE_URL,
    JOB_STATUS_POLL_INTERVAL_SEC,
    JOB_MAX_WAIT_SEC,
)


def _request(method: str, url: str, payload: dict | None = None) -> dict:
    import os
    api_key = os.environ.get("RUNPOD_API_KEY", "") or RUNPOD_API_KEY
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def submit_job(job_input: dict) -> str:
    """Submit a job to RunPod and return the RunPod job ID."""
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise RuntimeError("RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set in .env")
    submit_url = f"{RUNPOD_API_BASE_URL}/{RUNPOD_ENDPOINT_ID}/run"
    resp = _request("POST", submit_url, {"input": job_input})
    runpod_job_id = resp.get("id")
    if not runpod_job_id:
        raise RuntimeError(f"RunPod did not return a job ID: {resp}")
    return runpod_job_id


def poll_job(runpod_job_id: str) -> dict:
    """Poll a RunPod job until complete and return its output."""
    status_url = f"{RUNPOD_API_BASE_URL}/{RUNPOD_ENDPOINT_ID}/status/{runpod_job_id}"
    start = time.time()
    while True:
        if time.time() - start > JOB_MAX_WAIT_SEC:
            raise TimeoutError(f"RunPod job {runpod_job_id} timed out after {JOB_MAX_WAIT_SEC}s")
        status_resp = _request("GET", status_url)
        status = status_resp.get("status")
        if status == "COMPLETED":
            return status_resp.get("output", {})
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"RunPod job {runpod_job_id} ended with status: {status}")
        time.sleep(JOB_STATUS_POLL_INTERVAL_SEC)
