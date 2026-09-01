"""Service catalogue routes."""
import logging

from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok
from app.utils.slugify import slugify
from app.utils.validation import as_int, clamp_str, require

logger = logging.getLogger("tgp.services")

bp = Blueprint("services", __name__, url_prefix="/api/services")


@bp.get("")
def list_services():
    db = get_db()
    rows = db.execute("SELECT * FROM services ORDER BY sort_order ASC").fetchall()
    return ok([dict(r) for r in rows])


@bp.get("/<slug>")
def get_service(slug):
    db = get_db()
    row = db.execute("SELECT * FROM services WHERE slug = ? OR code = ?", (slug, slug)).fetchone()
    if row is None:
        return err("Không tìm thấy dịch vụ", 404)
    return ok(dict(row))


@bp.post("")
@admin_required
def create_service():
    data = request.get_json(silent=True) or {}
    try:
        require(data, ["title"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))

    db = get_db()
    slug = data.get("slug") or slugify(data["title"])
    code = data.get("code") or slug.replace("-", "_")
    cur = db.execute(
        """INSERT INTO services (code, title, slug, icon, short_description, description, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (code, clamp_str(data["title"], 200), slug, clamp_str(data.get("icon"), 50),
         clamp_str(data.get("short_description"), 500), clamp_str(data.get("description"), 4000),
         as_int(data.get("sort_order"), 0)),
    )
    db.commit()
    return ok({"id": cur.lastrowid, "slug": slug}, 201)


@bp.put("/<int:service_id>")
@admin_required
def update_service(service_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM services WHERE id = ?", (service_id,)).fetchone():
        return err("Không tìm thấy dịch vụ", 404)

    data = request.get_json(silent=True) or {}
    fields = ["title", "icon", "short_description", "description", "sort_order"]
    updates, params = [], []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return err("Không có dữ liệu để cập nhật", 400)
    params.append(service_id)
    db.execute(f"UPDATE services SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return ok({"id": service_id})


@bp.delete("/<int:service_id>")
@admin_required
def delete_service(service_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM services WHERE id = ?", (service_id,)).fetchone():
        return err("Không tìm thấy dịch vụ", 404)
    db.execute("DELETE FROM services WHERE id = ?", (service_id,))
    db.commit()
    return ok({"id": service_id})
