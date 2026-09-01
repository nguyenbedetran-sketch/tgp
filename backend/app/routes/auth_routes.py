"""Authentication routes: admin login / logout / current user."""
import logging

from flask import Blueprint, g, request

from app.models.db import get_db
from app.services.security import admin_required, issue_token, verify_password
from app.utils.rate_limit import rate_limited
from app.utils.responses import err, ok

logger = logging.getLogger("tgp.auth")

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
@rate_limited(max_requests=10, window_seconds=60)
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return err("Vui lòng nhập tên đăng nhập và mật khẩu", 400)

    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?", (username, username)
    ).fetchone()

    if row is None or not row["is_active"]:
        logger.warning("Failed login attempt for username=%s", username)
        return err("Sai tên đăng nhập hoặc mật khẩu", 401)

    if not verify_password(password, row["password_hash"], row["password_salt"]):
        logger.warning("Failed login attempt (bad password) for username=%s", username)
        return err("Sai tên đăng nhập hoặc mật khẩu", 401)

    token = issue_token(row["id"], row["username"], row["role"])
    db.execute(
        "UPDATE users SET last_login_at = datetime('now') WHERE id = ?", (row["id"],)
    )
    db.commit()

    logger.info("User %s logged in", row["username"])
    return ok({
        "token": token,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "role": row["role"],
        },
    })


@bp.post("/logout")
@admin_required
def logout():
    # JWTs issued by this service are stateless; true server-side revocation
    # would require a token blacklist store (e.g. Redis) keyed by jti with a
    # TTL matching JWT_EXPIRE_MINUTES. Left as a documented extension point;
    # clients should simply discard the token on logout.
    return ok({"message": "Đã đăng xuất"})


@bp.get("/me")
@admin_required
def me():
    return ok({"user": g.current_user})
