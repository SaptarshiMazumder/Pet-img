"""
RunPod serverless client.
Submits a job and polls until complete, then returns the result.
"""

import os
import time
import urllib.request
import urllib.error
import json

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")

BASE_URL = "https://api.runpod.io/v2"
POLL_INTERVAL = 2   # seconds between status checks
TIMEOUT = 300       # max seconds to wait for a job


def _request(method: str, url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
        },
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def run_job(job_input: dict) -> dict:
    """
    Submit a job to the RunPod endpoint and poll until done.
    Returns the completed job output dict.
    """
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise RuntimeError("RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set in .env")

    # Submit
    submit_url = f"{BASE_URL}/{RUNPOD_ENDPOINT_ID}/run"
    resp = _request("POST", submit_url, {"input": job_input})
    job_id = resp.get("id")
    if not job_id:
        raise RuntimeError(f"RunPod did not return a job ID: {resp}")

    # Poll
    status_url = f"{BASE_URL}/{RUNPOD_ENDPOINT_ID}/status/{job_id}"
    start = time.time()
    while True:
        if time.time() - start > TIMEOUT:
            raise TimeoutError(f"RunPod job {job_id} timed out after {TIMEOUT}s")

        status_resp = _request("GET", status_url)
        status = status_resp.get("status")

        if status == "COMPLETED":
            return status_resp.get("output", {})
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"RunPod job {job_id} ended with status: {status}")

        time.sleep(POLL_INTERVAL)
