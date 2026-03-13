"""
RunPod endpoint scaler — adjust min/max workers on the serverless endpoint.
"""
import json
import urllib.error
import urllib.request

from backend.runpod.runpod_config import RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID

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


def _gql(query: str) -> dict:
    import os
    api_key = os.environ.get("RUNPOD_API_KEY", "") or RUNPOD_API_KEY
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


def set_workers(min_n: int, max_n: int) -> None:
    """Set both min and max workers on the endpoint."""
    result = _gql(_QUERY_ENDPOINT)
    endpoints = result["data"]["myself"]["endpoints"]
    ep = next((e for e in endpoints if e["id"] == RUNPOD_ENDPOINT_ID), None)
    if ep is None:
        raise RuntimeError(f"Endpoint {RUNPOD_ENDPOINT_ID} not found")

    if ep.get("workersMin") == min_n and ep.get("workersMax") == max_n:
        print(f"[scale] already at min={min_n} max={max_n}, skipping")
        return

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
    _gql(mutation)
    print(f"[scale] workers set to min={min_n} max={max_n}")
