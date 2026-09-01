"""
Minimal in-memory sliding-window rate limiter.

Good enough to stop naive spam/scripted abuse of public POST endpoints
(contact form, estimate tool) in a single-process deployment. For a
multi-process/production deployment behind a load balancer, replace the
in-memory store with Redis (the interface below is intentionally tiny so
that swap is a one-file change).
"""
import functools
import threading
import time

from flask import jsonify, request

from app.config.settings import config

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limited(max_requests: int | None = None, window_seconds: int | None = None):
    """Decorator limiting an endpoint to `max_requests` per `window_seconds`
    per client IP."""
    limit = max_requests or config.RATE_LIMIT_MAX_REQUESTS
    window = window_seconds or config.RATE_LIMIT_WINDOW_SECONDS

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            ip = _client_ip()
            key = f"{fn.__name__}:{ip}"
            now = time.time()
            with _lock:
                hits = _hits.setdefault(key, [])
                # drop hits outside the window
                cutoff = now - window
                while hits and hits[0] < cutoff:
                    hits.pop(0)
                if len(hits) >= limit:
                    return (
                        jsonify({
                            "success": False,
                            "error": "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau ít phút.",
                        }),
                        429,
                    )
                hits.append(now)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
