"""Homepage hero slider slides."""
from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok
from app.utils.validation import as_int, clamp_str, require

bp = Blueprint("hero_slides", __name__, url_prefix="/api/hero-slides")


@bp.get("")
def list_slides():
    db = get_db()
    rows = db.execute("SELECT * FROM hero_slides ORDER BY sort_order ASC, id ASC").fetchall()
    return ok([dict(r) for r in rows])


@bp.post("")
@admin_required
def create_slide():
    data = request.get_json(silent=True) or {}
    try:
        require(data, ["image_url", "title_line1"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))
    db = get_db()
    cur = db.execute(
        """INSERT INTO hero_slides
           (image_url, eyebrow, title_line1, title_line2, subtitle,
            button1_text, button1_link, button2_text, button2_link, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            clamp_str(data["image_url"], 500), clamp_str(data.get("eyebrow"), 150),
            clamp_str(data["title_line1"], 150), clamp_str(data.get("title_line2"), 150),
            clamp_str(data.get("subtitle"), 500),
            clamp_str(data.get("button1_text"), 60), clamp_str(data.get("button1_link"), 300),
            clamp_str(data.get("button2_text"), 60), clamp_str(data.get("button2_link"), 300),
            as_int(data.get("sort_order"), 0),
        ),
    )
    db.commit()
    return ok({"id": cur.lastrowid}, 201)


@bp.put("/<int:slide_id>")
@admin_required
def update_slide(slide_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM hero_slides WHERE id = ?", (slide_id,)).fetchone():
        return err("Không tìm thấy slide", 404)
    data = request.get_json(silent=True) or {}
    fields = ["image_url", "eyebrow", "title_line1", "title_line2", "subtitle",
              "button1_text", "button1_link", "button2_text", "button2_link", "sort_order"]
    updates, params = [], []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return err("Không có dữ liệu để cập nhật", 400)
    params.append(slide_id)
    db.execute(f"UPDATE hero_slides SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return ok({"id": slide_id})


@bp.delete("/<int:slide_id>")
@admin_required
def delete_slide(slide_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM hero_slides WHERE id = ?", (slide_id,)).fetchone():
        return err("Không tìm thấy slide", 404)
    db.execute("DELETE FROM hero_slides WHERE id = ?", (slide_id,))
    db.commit()
    return ok({"id": slide_id})
