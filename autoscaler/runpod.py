"""RunPod GraphQL client — adjusts min/max workers on the serverless endpoint."""
import json
import os
import urllib.error
import urllib.request

_GRAPHQL_URL = "https://api.runpod.io/graphql"

_QUERY_ENDPOINT = """
query {
    myself {
        endpoints {
            id name templateId gpuIds gpuCount
            workersMin workersMax idleTimeout
            scalerType scalerValue locations
            networkVolumeId allowedCudaVersions
            env { key value }
        }
    }
}
"""

_QUERY_HEALTH = """
query {
    myself {
        endpoints {
            id
            workersMin
            workersMax
            workersStandby
            workerState(input: {}) {
                idle
                running
                throttled
            }
        }
    }
}
"""


def _gql(query: str) -> dict:
    api_key = os.environ.get("RUNPOD_API_KEY", "")
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        f"{_GRAPHQL_URL}?api_key={api_key}",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "python-runpod/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"RunPod GraphQL {e.code}: {body}") from e


def get_endpoint_health(endpoint_id: str) -> dict:
    """Returns current worker health for the endpoint.

    Returns: { healthy: int, throttled: int, workers_max: int }
    healthy = RUNNING + IDLE workers (able to accept jobs)
    throttled = workers in the penalty box (failing to start)
    """
    result = _gql(_QUERY_HEALTH)
    endpoints = result["data"]["myself"]["endpoints"]
    ep = next((e for e in endpoints if e["id"] == endpoint_id), None)
    if ep is None:
        return {"healthy": 0, "throttled": 0, "workers_max": 0}
    states = ep.get("workerState") or []
    healthy   = sum(s.get("idle", 0) + s.get("running", 0) for s in states)
    throttled = sum(s.get("throttled", 0) for s in states)
    return {
        "healthy": healthy,
        "throttled": throttled,
        "workers_max": ep.get("workersMax", 0),
    }


def set_workers(min_n: int, max_n: int) -> None:
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID", "")
    result = _gql(_QUERY_ENDPOINT)
    endpoints = result["data"]["myself"]["endpoints"]
    ep = next((e for e in endpoints if e["id"] == endpoint_id), None)
    if ep is None:
        raise RuntimeError(f"Endpoint {endpoint_id} not found")

    if ep.get("workersMin") == min_n and ep.get("workersMax") == max_n:
        print(f"[scale] already at min={min_n} max={max_n}, skipping")
        return

    env_str = ""
    if ep.get("env"):
        pairs = ", ".join(f'{{key: "{e["key"]}", value: "{e["value"]}"}}'for e in ep["env"])
        env_str = f"env: [{pairs}],"

    gpu_count_str = f'gpuCount: {ep["gpuCount"]},' if ep.get("gpuCount") else ""
    locations_str = f'locations: "{ep["locations"]}",' if ep.get("locations") else 'locations: "",'
    nv_str        = f'networkVolumeId: "{ep["networkVolumeId"]}",' if ep.get("networkVolumeId") else 'networkVolumeId: "",'
    cuda_str      = f'allowedCudaVersions: "{ep.get("allowedCudaVersions", "")}",' if ep.get("allowedCudaVersions") else ""

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
            id workersMin workersMax
        }}
    }}
    """
    _gql(mutation)
    print(f"[scale] workers set to min={min_n} max={max_n}")
