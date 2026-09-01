"""Site-wide settings (company info, homepage counters, banner text, social
links). Publicly readable (the frontend needs them to render the site);
writable only by admins."""
from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok

bp = Blueprint("settings", __name__, url_prefix="/api/settings")
admin_bp = Blueprint("settings_admin", __name__, url_prefix="/api/admin/settings")


@bp.get("")
def get_settings():
    db = get_db()
    rows = db.execute("SELECT key, value FROM site_settings").fetchall()
    return ok({r["key"]: r["value"] for r in rows})


@admin_bp.put("")
@admin_required
def update_settings():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict) or not data:
        return err("Dữ liệu không hợp lệ, cần gửi { key: value, ... }", 422)

    db = get_db()
    for key, value in data.items():
        db.execute(
            """INSERT INTO site_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')""",
            (str(key), "" if value is None else str(value)),
        )
    db.commit()
    return ok({"updated_keys": list(data.keys())})
