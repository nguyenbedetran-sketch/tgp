"""
Security helpers: password hashing, JWT issuing/verification, and an
`@admin_required` decorator used to protect admin API routes.

Password hashing uses PBKDF2-HMAC-SHA256 (stdlib `hashlib`) with a random
per-user salt and a high iteration count. This avoids a hard dependency on
bcrypt/passlib (unavailable in this offline build) while still following
current best practice (PBKDF2 is NIST-approved, OWASP-recommended when
bcrypt/argon2 are not available).
"""
import functools
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
from flask import g, jsonify, request

from app.config.settings import config

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> tuple[str, str]:
    """Returns (password_hash_hex, salt_hex)."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), password_hash)


def issue_token(user_id: int, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


def _extract_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def admin_required(fn):
    """Route decorator: requires a valid JWT bearer token issued by /api/auth/login."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({"success": False, "error": "Thiếu token xác thực"}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token đã hết hạn"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Token không hợp lệ"}), 401

        g.current_user = payload
        return fn(*args, **kwargs)

    return wrapper
