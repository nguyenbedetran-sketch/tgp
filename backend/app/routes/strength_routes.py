"""Homepage "vi sao chon chung toi" strength cards (photo + title + description)."""
from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok
from app.utils.validation import as_int, clamp_str, require

bp = Blueprint("strengths", __name__, url_prefix="/api/strengths")


@bp.get("")
def list_strengths():
    db = get_db()
    rows = db.execute("SELECT * FROM home_strengths ORDER BY sort_order ASC, id ASC").fetchall()
    return ok([dict(r) for r in rows])


@bp.post("")
@admin_required
def create_strength():
    data = request.get_json(silent=True) or {}
    try:
        require(data, ["title"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))
    db = get_db()
    cur = db.execute(
        """INSERT INTO home_strengths (image_url, title, description, sort_order)
           VALUES (?, ?, ?, ?)""",
        (clamp_str(data.get("image_url"), 500), clamp_str(data["title"], 150),
         clamp_str(data.get("description"), 500), as_int(data.get("sort_order"), 0)),
    )
    db.commit()
    return ok({"id": cur.lastrowid}, 201)


@bp.put("/<int:strength_id>")
@admin_required
def update_strength(strength_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM home_strengths WHERE id = ?", (strength_id,)).fetchone():
        return err("Không tìm thấy mục", 404)
    data = request.get_json(silent=True) or {}
    fields = ["image_url", "title", "description", "sort_order"]
    updates, params = [], []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return err("Không có dữ liệu để cập nhật", 400)
    params.append(strength_id)
    db.execute(f"UPDATE home_strengths SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return ok({"id": strength_id})


@bp.delete("/<int:strength_id>")
@admin_required
def delete_strength(strength_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM home_strengths WHERE id = ?", (strength_id,)).fetchone():
        return err("Không tìm thấy mục", 404)
    db.execute("DELETE FROM home_strengths WHERE id = ?", (strength_id,))
    db.commit()
    return ok({"id": strength_id})
