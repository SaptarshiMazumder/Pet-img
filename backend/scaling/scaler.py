"""Periodic auto-scaler for RunPod workers.

Scale-up (event-driven, on job start):
  - 1-2 active jobs  → stay at 1/2 (warm state)
  - 3+ active jobs   → set max = active_count + 1  (always one spare slot)

Scale-down (periodic check every POLL_INTERVAL seconds):
  - active jobs > 0                → no action, reset idle clock
  - idle >= SCALE_DOWN (1 min)     → set 1/1  (keep one warm worker)
  - idle >= SCALE_ZERO (5 min)     → set 0/0  (full shutdown)

The scaler stays dormant on server startup until warm() is called or a job runs,
so idle browsing time before any activity doesn't trigger scale-down.
"""
import threading
import time

from backend.scaling.job_tracker import JobTracker

_POLL_INTERVAL = 60    # seconds between checks
_SCALE_DOWN = 60       # idle seconds before dropping to 1/1
_SCALE_ZERO = 300      # idle seconds before full shutdown to 0/0
_WARM_MAX = 2          # max workers in the normal warm state
_MAX_WORKERS = 3       # hard cap on concurrent workers


class ScalerService:
    def __init__(self) -> None:
        self._tracker = JobTracker()
        self._lock = threading.Lock()
        self._queue_empty_since: float | None = None
        self._has_had_activity = False  # stays False until warm() or first job

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def warm(self) -> None:
        """Called when a user visits — spin up a worker preemptively.

        No-op if jobs are already running (workers are already active).
        set_workers is idempotent, so concurrent warm() calls from multiple
        users are safe and won't thrash the API.
        """
        if self._tracker.active_count > 0:
            return  # workers already busy, nothing to do

        from backend.runpod_client import set_workers
        try:
            set_workers(min_n=1, max_n=_WARM_MAX)
            print(f"[scaler] warm → workers 1/{_WARM_MAX}")
        except Exception as exc:
            print(f"[scaler] warm failed: {exc}")
            return

        with self._lock:
            self._has_had_activity = True
            self._queue_empty_since = time.time()  # start idle clock from now

    def on_job_start(self) -> None:
        self._tracker.increment()
        with self._lock:
            self._has_had_activity = True
            self._queue_empty_since = None  # reset idle clock
        count = self._tracker.active_count
        # Always ensure enough capacity: at least WARM_MAX, plus one spare if busy,
        # capped at MAX_WORKERS. Idempotent — free no-op if already at the right value.
        desired_max = min(max(_WARM_MAX, count + 1), _MAX_WORKERS)
        threading.Thread(target=self._ensure_capacity, args=(desired_max,), daemon=True).start()

    def on_job_finish(self) -> None:
        self._tracker.decrement()

    @property
    def active_count(self) -> int:
        return self._tracker.active_count

    # ------------------------------------------------------------------
    # Scale-up helper
    # ------------------------------------------------------------------

    def _ensure_capacity(self, desired_max: int) -> None:
        from backend.runpod_client import set_workers
        try:
            set_workers(min_n=1, max_n=desired_max)
            print(f"[scaler] job started → workers 1/{desired_max}")
        except Exception as exc:
            print(f"[scaler] capacity update failed: {exc}")

    # ------------------------------------------------------------------
    # Background loop (scale-down)
    # ------------------------------------------------------------------

    def start(self) -> None:
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self) -> None:
        while True:
            time.sleep(_POLL_INTERVAL)
            self._check()

    def _check(self) -> None:
        if not self._has_had_activity:
            return  # server just started with no user activity yet — stay dormant

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

        if idle >= _SCALE_ZERO:
            try:
                set_workers(min_n=0, max_n=0)
                print(f"[scaler] idle {idle:.0f}s → workers 0/0")
            except Exception as exc:
                print(f"[scaler] scale-to-zero failed: {exc}")
        elif idle >= _SCALE_DOWN:
            try:
                set_workers(min_n=1, max_n=1)
                print(f"[scaler] idle {idle:.0f}s → workers 1/1")
            except Exception as exc:
                print(f"[scaler] scale-down failed: {exc}")


# Module-level singleton
scaler = ScalerService()
