"""Thread-safe counter of in-flight jobs."""
import threading


class JobTracker:
    def __init__(self) -> None:
        self._count = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:
            self._count += 1

    def decrement(self) -> None:
        with self._lock:
            self._count = max(0, self._count - 1)

    @property
    def active_count(self) -> int:
        with self._lock:
            return self._count
