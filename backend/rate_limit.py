import time
from collections import defaultdict, deque
from threading import Lock


class InMemoryRateLimiter:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max(1, max_requests)
        self.window_seconds = max(1, window_seconds)
        self._hits = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key):
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
                return False, retry_after

            bucket.append(now)
            return True, 0
