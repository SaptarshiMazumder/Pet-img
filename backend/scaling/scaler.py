"""Periodic auto-scaler for RunPod workers.

Every POLL_INTERVAL seconds:
  - active jobs > 0              → no action
  - active jobs == 0             → set min=0, max=1
  - active jobs == 0 for >= IDLE_TIMEOUT → set min=0, max=0
"""
import threading
import time

from backend.scaling.job_tracker import JobTracker

_POLL_INTERVAL = 60   # seconds between checks
_IDLE_TIMEOUT = 120   # seconds of empty queue before scaling to zero


class ScalerService:
    def __init__(self) -> None:
        self._tracker = JobTracker()
        self._lock = threading.Lock()
        self._queue_empty_since: float | None = None

    # ------------------------------------------------------------------
    # Job lifecycle hooks (called by worker)
    # ------------------------------------------------------------------

    def on_job_start(self) -> None:
        self._tracker.increment()
        with self._lock:
            self._queue_empty_since = None  # reset idle clock

    def on_job_finish(self) -> None:
        self._tracker.decrement()

    @property
    def active_count(self) -> int:
        return self._tracker.active_count

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def start(self) -> None:
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self) -> None:
        while True:
            time.sleep(_POLL_INTERVAL)
            self._check()

    def _check(self) -> None:
        # Lazy import avoids circular dependency at module load time
        from backend.runpod_client import set_workers

        count = self._tracker.active_count
        now = time.time()

        if count > 0:
            with self._lock:
                self._queue_empty_since = None
            return

        # Queue is empty — track how long
        with self._lock:
            if self._queue_empty_since is None:
                self._queue_empty_since = now
            idle = now - self._queue_empty_since

        if idle >= _IDLE_TIMEOUT:
            try:
                set_workers(min_n=0, max_n=0)
                print(f"[scaler] idle {idle:.0f}s → workers 0/0")
            except Exception as exc:
                print(f"[scaler] scale-to-zero failed: {exc}")
        else:
            try:
                set_workers(min_n=0, max_n=1)
                print(f"[scaler] queue empty → workers 0/1")
            except Exception as exc:
                print(f"[scaler] set 0/1 failed: {exc}")


# Module-level singleton
scaler = ScalerService()
