"""A small in-memory rate limiter for login attempts.

Single-process only, by the same assumption the demo clock already makes
(the deployed service runs with ``WEB_CONCURRENCY=1``) -- a real multi-instance
deployment would need a shared store (Redis, or a database table) for this to
be correct across instances. This is the proportionate version of "don't let
/users/authenticate be brute-forced" for a build that already runs as one
process; reaching for external infrastructure to rate-limit a demo app's one
password-checking endpoint would be solving a scale problem this app does not
have.
"""

import time
from collections import defaultdict

WINDOW_SECONDS = 15 * 60
MAX_ATTEMPTS = 5

_failures: dict[str, list[float]] = defaultdict(list)


def _prune(key: str, now: float) -> list[float]:
    """Drop attempts outside the window and return what is left."""
    window = [t for t in _failures[key] if now - t < WINDOW_SECONDS]
    _failures[key] = window
    return window


def is_locked_out(key: str) -> bool:
    """True once ``key`` has hit the failure limit within the current window."""
    return len(_prune(key, time.monotonic())) >= MAX_ATTEMPTS


def register_failure(key: str) -> None:
    """Record one failed attempt for ``key``."""
    now = time.monotonic()
    _prune(key, now).append(now)


def clear(key: str) -> None:
    """Drop a key's history -- called on a successful attempt."""
    _failures.pop(key, None)


def reset_all() -> None:
    """Wipe every key. Used by tests, which otherwise share this process's state."""
    _failures.clear()
