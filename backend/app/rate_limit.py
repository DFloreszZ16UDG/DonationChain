"""Small in-process limiter for login abuse in a single API instance.

For a horizontally scaled deployment this interface should be backed by Redis.
"""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class LoginRateLimiter:
    def __init__(self, attempts: int, window_seconds: int):
        self.attempts = attempts
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> int | None:
        """Record an attempt and return retry-after seconds when blocked."""
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.attempts:
                return max(1, int(self.window_seconds - (now - events[0])))
            events.append(now)
        return None

    def clear(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)
