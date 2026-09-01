"""Customer testimonial routes."""
from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok
from app.utils.validation import as_int, clamp_str, require

bp = Blueprint("testimonials", __name__, url_prefix="/api/testimonials")


@bp.get("")
def list_testimonials():
    db = get_db()
    rows = db.execute("SELECT * FROM testimonials ORDER BY sort_order ASC").fetchall()
    return ok([dict(r) for r in rows])


@bp.post("")
@admin_required
def create_testimonial():
    data = request.get_json(silent=True) or {}
    try:
        require(data, ["customer_name", "content"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))
    rating = as_int(data.get("rating"), 5)
    rating = max(1, min(5, rating))
    db = get_db()
    cur = db.execute(
        """INSERT INTO testimonials (customer_name, project_name, content, rating, avatar_url, sort_order)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (clamp_str(data["customer_name"], 150), clamp_str(data.get("project_name"), 200),
         clamp_str(data["content"], 1000), rating, clamp_str(data.get("avatar_url"), 500),
         as_int(data.get("sort_order"), 0)),
    )
    db.commit()
    return ok({"id": cur.lastrowid}, 201)


@bp.put("/<int:testimonial_id>")
@admin_required
def update_testimonial(testimonial_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM testimonials WHERE id = ?", (testimonial_id,)).fetchone():
        return err("Không tìm thấy đánh giá", 404)
    data = request.get_json(silent=True) or {}
    fields = ["customer_name", "project_name", "content", "rating", "avatar_url", "sort_order"]
    updates, params = [], []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return err("Không có dữ liệu để cập nhật", 400)
    params.append(testimonial_id)
    db.execute(f"UPDATE testimonials SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return ok({"id": testimonial_id})


@bp.delete("/<int:testimonial_id>")
@admin_required
def delete_testimonial(testimonial_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM testimonials WHERE id = ?", (testimonial_id,)).fetchone():
        return err("Không tìm thấy đánh giá", 404)
    db.execute("DELETE FROM testimonials WHERE id = ?", (testimonial_id,))
    db.commit()
    return ok({"id": testimonial_id})
