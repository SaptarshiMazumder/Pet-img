"""HTTP client for the autoscaler service.

Notifies the autoscaler of scaling events. The autoscaler owns all
scaling state and decisions — this is just the messenger.
"""
import os
import urllib.request
from urllib.error import URLError


def _post(path: str) -> None:
    url = os.environ.get("AUTOSCALER_URL", "http://localhost:5001") + path
    try:
        req = urllib.request.Request(
            url,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except URLError as exc:
        print(f"[autoscaler-client] {path} failed: {exc}")


class AutoscalerClient:
    def warm(self) -> None:
        _post("/warm")

    def on_job_start(self) -> None:
        _post("/job/start")

    def on_job_finish(self) -> None:
        _post("/job/finish")

    def start(self) -> None:
        pass  # autoscaler service manages its own lifecycle


autoscaler = AutoscalerClient()
