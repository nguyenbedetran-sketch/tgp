"""Real (not simulated) pageview logging, used to power the admin dashboard
"Luot truy cap" metric. The frontend calls this once per page load."""
import logging

from flask import Blueprint, request

from app.models.db import get_db
from app.utils.rate_limit import rate_limited
from app.utils.responses import ok
from app.utils.validation import clamp_str

logger = logging.getLogger("tgp.visit")

bp = Blueprint("visit", __name__, url_prefix="/api/visit")


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "")


@bp.post("")
@rate_limited(max_requests=60, window_seconds=60)
def log_visit():
    data = request.get_json(silent=True) or {}
    db = get_db()
    db.execute(
        "INSERT INTO page_views (path, ip_address, user_agent) VALUES (?, ?, ?)",
        (
            clamp_str(data.get("path"), 300),
            _client_ip(),
            clamp_str(request.headers.get("User-Agent"), 300),
        ),
    )
    db.commit()
    return ok({"logged": True})
