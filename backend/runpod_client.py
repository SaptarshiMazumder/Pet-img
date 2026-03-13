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

BASE_URL = "https://api.runpod.ai/v2"
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


def set_workers(min_n: int, max_n: int) -> None:
    """Set both min and max workers on the endpoint."""
    import runpod as _runpod
    from runpod.api.graphql import run_graphql_query
    from runpod.api.queries.endpoints import QUERY_ENDPOINT

    _runpod.api_key = RUNPOD_API_KEY

    result = run_graphql_query(QUERY_ENDPOINT)
    endpoints = result["data"]["myself"]["endpoints"]
    ep = next((e for e in endpoints if e["id"] == RUNPOD_ENDPOINT_ID), None)
    if ep is None:
        raise RuntimeError(f"Endpoint {RUNPOD_ENDPOINT_ID} not found")

    env_str = ""
    if ep.get("env"):
        pairs = ", ".join(f'{{key: "{e["key"]}", value: "{e["value"]}"}}'for e in ep["env"])
        env_str = f"env: [{pairs}],"

    gpu_count_str = f'gpuCount: {ep["gpuCount"]},' if ep.get("gpuCount") else ""
    locations_str = f'locations: "{ep["locations"]}",' if ep.get("locations") else 'locations: "",'
    nv_str = f'networkVolumeId: "{ep["networkVolumeId"]}",' if ep.get("networkVolumeId") else 'networkVolumeId: "",'
    cuda_str = f'allowedCudaVersions: "{ep.get("allowedCudaVersions", "")}",' if ep.get("allowedCudaVersions") else ""

    mutation = f"""
    mutation {{
        saveEndpoint(input: {{
            id: "{ep["id"]}",
            name: "{ep["name"]}",
            templateId: "{ep["templateId"]}",
            gpuIds: "{ep["gpuIds"]}",
            {nv_str}
            {locations_str}
            idleTimeout: {ep["idleTimeout"]},
            scalerType: "{ep["scalerType"]}",
            scalerValue: {ep["scalerValue"]},
            workersMin: {min_n},
            workersMax: {max_n},
            {gpu_count_str}
            {cuda_str}
            {env_str}
        }}) {{
            id
            workersMin
            workersMax
        }}
    }}
    """
    run_graphql_query(mutation)
    print(f"[scale] workers set to min={min_n} max={max_n}")


def submit_job(job_input: dict) -> str:
    """Submit a job to RunPod and return the RunPod job ID."""
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise RuntimeError("RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set in .env")
    submit_url = f"{BASE_URL}/{RUNPOD_ENDPOINT_ID}/run"
    resp = _request("POST", submit_url, {"input": job_input})
    runpod_job_id = resp.get("id")
    if not runpod_job_id:
        raise RuntimeError(f"RunPod did not return a job ID: {resp}")
    return runpod_job_id


def poll_job(runpod_job_id: str) -> dict:
    """Poll a RunPod job until complete and return its output."""
    status_url = f"{BASE_URL}/{RUNPOD_ENDPOINT_ID}/status/{runpod_job_id}"
    start = time.time()
    while True:
        if time.time() - start > TIMEOUT:
            raise TimeoutError(f"RunPod job {runpod_job_id} timed out after {TIMEOUT}s")
        status_resp = _request("GET", status_url)
        status = status_resp.get("status")
        if status == "COMPLETED":
            return status_resp.get("output", {})
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"RunPod job {runpod_job_id} ended with status: {status}")
        time.sleep(POLL_INTERVAL)
