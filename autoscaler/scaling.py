"""Autoscaling logic — owns worker count state and all scaling decisions.

Scale-up (event-driven, on job start):
  - 1-2 active jobs  → stay at 1/2 (warm state)
  - 3+ active jobs   → max = min(active_count + 1, MAX_WORKERS)

Scale-down (periodic check every POLL_INTERVAL seconds):
  - active jobs > 0                → no action, reset idle clock
  - idle >= SCALE_DOWN (1 min)     → 1/1  (keep one warm worker)
  - idle >= SCALE_ZERO (5 min)     → 0/0  (full shutdown)

Stays dormant on startup until warm() is called or a job runs.
"""
import threading
import time

from autoscaler.runpod import set_workers, get_endpoint_health

_POLL_INTERVAL   = 60   # seconds between periodic checks
_SCALE_DOWN      = 60   # idle seconds before dropping to 1/1
_SCALE_ZERO      = 300  # idle seconds before full shutdown to 0/0
_WARM_MAX        = 2    # max workers in the normal warm state
_MAX_WORKERS     = 3    # hard cap on concurrent workers
_STUCK_THRESHOLD = 2    # consecutive stuck checks before recovery action

_lock              = threading.Lock()
_active_count      = 0
_queue_empty_since: float | None = None
_has_had_activity  = False
_stuck_checks      = 0   # consecutive checks: jobs in flight but zero healthy workers
_paused            = False


def pause() -> None:
    global _paused
    with _lock:
        _paused = True
    print("[autoscaler] paused — scaling decisions suspended")


def resume() -> None:
    global _paused
    with _lock:
        _paused = False
    print("[autoscaler] resumed — scaling decisions active")


def _increment() -> int:
    global _active_count
    with _lock:
        _active_count += 1
        return _active_count


def _decrement() -> int:
    global _active_count
    with _lock:
        _active_count = max(0, _active_count - 1)
        return _active_count


def warm() -> None:
    global _has_had_activity, _queue_empty_since
    with _lock:
        if _paused:
            return
        if _active_count > 0:
            return  # workers already busy, nothing to do
    try:
        set_workers(min_n=1, max_n=_WARM_MAX)
        print(f"[autoscaler] warm → workers 1/{_WARM_MAX}")
    except Exception as exc:
        print(f"[autoscaler] warm failed: {exc}")
        return
    with _lock:
        _has_had_activity = True
        _queue_empty_since = time.time()


def on_job_start() -> None:
    global _has_had_activity, _queue_empty_since
    count = _increment()
    with _lock:
        _has_had_activity = True
        _queue_empty_since = None
        if _paused:
            return
    desired_max = min(max(_WARM_MAX, count + 1), _MAX_WORKERS)
    threading.Thread(target=_ensure_capacity, args=(desired_max,), daemon=True).start()


def on_job_finish() -> None:
    _decrement()


def _ensure_capacity(desired_max: int) -> None:
    try:
        set_workers(min_n=1, max_n=desired_max)
        print(f"[autoscaler] job started → workers 1/{desired_max}")
    except Exception as exc:
        print(f"[autoscaler] capacity update failed: {exc}")


def _maybe_recover_stuck_workers() -> None:
    """Called when jobs are in flight. Detects all-throttled state and recovers."""
    global _stuck_checks
    import os
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID", "")
    try:
        health = get_endpoint_health(endpoint_id)
    except Exception as exc:
        print(f"[autoscaler] health check failed: {exc}")
        _stuck_checks = 0
        return

    if health["standby"] > 0:
        _stuck_checks = 0
        return  # at least one worker is up and ready — all good

    _stuck_checks += 1
    print(f"[autoscaler] stuck check {_stuck_checks}/{_STUCK_THRESHOLD}: "
          f"standby=0, workers_max={health['workers_max']}")

    if _stuck_checks < _STUCK_THRESHOLD:
        return  # wait one more cycle before acting

    _stuck_checks = 0
    current_max = health["workers_max"] or _WARM_MAX

    desired = min(current_max + 1, _MAX_WORKERS) if current_max < _MAX_WORKERS else _MAX_WORKERS
    try:
        set_workers(min_n=1, max_n=desired)
        print(f"[autoscaler] recovery: re-asserted workers 1/{desired}")
    except Exception as exc:
        print(f"[autoscaler] recovery failed: {exc}")


def _check() -> None:
    global _queue_empty_since
    if not _has_had_activity:
        return  # dormant until first user activity
    with _lock:
        if _paused:
            return

    now = time.time()
    with _lock:
        count = _active_count

    if count > 0:
        with _lock:
            _queue_empty_since = None
        _maybe_recover_stuck_workers()
        return

    with _lock:
        if _queue_empty_since is None:
            _queue_empty_since = now
        idle = now - _queue_empty_since

    if idle >= _SCALE_ZERO:
        try:
            set_workers(min_n=0, max_n=0)
            print(f"[autoscaler] idle {idle:.0f}s → workers 0/0")
        except Exception as exc:
            print(f"[autoscaler] scale-to-zero failed: {exc}")
    elif idle >= _SCALE_DOWN:
        try:
            set_workers(min_n=1, max_n=1)
            print(f"[autoscaler] idle {idle:.0f}s → workers 1/1")
        except Exception as exc:
            print(f"[autoscaler] scale-down failed: {exc}")


def _loop() -> None:
    while True:
        time.sleep(_POLL_INTERVAL)
        try:
            _check()
        except Exception as exc:
            print(f"[autoscaler] check error: {exc}")


def _recover_from_firestore() -> None:
    """On startup, restore _active_count from Firestore processing jobs."""
    global _active_count, _has_had_activity, _queue_empty_since
    try:
        import os
        import firebase_admin
        from firebase_admin import credentials, firestore as fb_firestore

        sa_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
        if not sa_path:
            return

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(sa_path))

        import datetime
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
        db = fb_firestore.client()
        processing = (
            db.collection("jobs")
            .where("status", "in", ["pending", "processing", "fixing"])
            .where("created_at", ">=", cutoff)
            .stream()
        )
        count = sum(1 for _ in processing)

        if count > 0:
            with _lock:
                _active_count = count
                _has_had_activity = True
                _queue_empty_since = None
            print(f"[autoscaler] recovered {count} in-flight jobs from Firestore")
    except Exception as exc:
        print(f"[autoscaler] Firestore recovery failed: {exc}")


def start() -> None:
    _recover_from_firestore()
    threading.Thread(target=_loop, daemon=True).start()
