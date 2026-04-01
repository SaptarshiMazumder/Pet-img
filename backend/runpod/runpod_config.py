"""
RunPod API configuration — credentials and job polling constants.
"""
import os

RUNPOD_API_KEY     = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")

RUNPOD_API_BASE_URL = "https://api.runpod.ai/v2"

# Job status polling: how often we check if a submitted job is done
JOB_STATUS_POLL_INTERVAL_SEC = 2
# Max time to wait for a job before giving up (image gen + upscale can take 10+ min)
JOB_MAX_WAIT_SEC = int(os.environ.get("RUNPOD_JOB_MAX_WAIT_SEC", "900"))  # default 15 min
