"""Team member routes."""
from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok
from app.utils.validation import as_int, clamp_str, require

bp = Blueprint("team", __name__, url_prefix="/api/team")


@bp.get("")
def list_team():
    db = get_db()
    rows = db.execute("SELECT * FROM team_members ORDER BY sort_order ASC").fetchall()
    return ok([dict(r) for r in rows])


@bp.post("")
@admin_required
def create_member():
    data = request.get_json(silent=True) or {}
    try:
        require(data, ["full_name", "position"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))
    db = get_db()
    cur = db.execute(
        """INSERT INTO team_members (full_name, position, specialty, photo_url, sort_order)
           VALUES (?, ?, ?, ?, ?)""",
        (clamp_str(data["full_name"], 150), clamp_str(data["position"], 150),
         clamp_str(data.get("specialty"), 300), clamp_str(data.get("photo_url"), 500),
         as_int(data.get("sort_order"), 0)),
    )
    db.commit()
    return ok({"id": cur.lastrowid}, 201)


@bp.put("/<int:member_id>")
@admin_required
def update_member(member_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM team_members WHERE id = ?", (member_id,)).fetchone():
        return err("Không tìm thấy thành viên", 404)
    data = request.get_json(silent=True) or {}
    fields = ["full_name", "position", "specialty", "photo_url", "sort_order"]
    updates, params = [], []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return err("Không có dữ liệu để cập nhật", 400)
    params.append(member_id)
    db.execute(f"UPDATE team_members SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return ok({"id": member_id})


@bp.delete("/<int:member_id>")
@admin_required
def delete_member(member_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM team_members WHERE id = ?", (member_id,)).fetchone():
        return err("Không tìm thấy thành viên", 404)
    db.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
    db.commit()
    return ok({"id": member_id})
