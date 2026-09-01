"""Project (portfolio) routes: GET /api/projects, GET/POST/PUT/DELETE for
a single project. Read endpoints are public; write endpoints require admin
auth."""
import logging

from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok
from app.utils.slugify import slugify
from app.utils.validation import as_int, clamp_str, require

logger = logging.getLogger("tgp.projects")

bp = Blueprint("projects", __name__, url_prefix="/api/projects")

ALLOWED_CATEGORIES = {"nha_pho", "biet_thu", "van_phong", "noi_that", "thuong_mai", "khac"}


def _row_to_dict(row, images=None):
    d = dict(row)
    if images is not None:
        d["images"] = images
    return d


@bp.get("")
def list_projects():
    db = get_db()
    category = request.args.get("category")
    status = request.args.get("status", "published")
    limit = as_int(request.args.get("limit"), 0)

    query = "SELECT * FROM projects WHERE 1=1"
    params: list = []
    if status != "all":
        query += " AND status = ?"
        params.append(status)
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY sort_order ASC, created_at DESC"
    if limit:
        query += " LIMIT ?"
        params.append(limit)

    rows = db.execute(query, params).fetchall()
    return ok([dict(r) for r in rows])


@bp.get("/<identifier>")
def get_project(identifier):
    db = get_db()
    if identifier.isdigit():
        row = db.execute("SELECT * FROM projects WHERE id = ?", (identifier,)).fetchone()
    else:
        row = db.execute("SELECT * FROM projects WHERE slug = ?", (identifier,)).fetchone()

    if row is None:
        return err("Không tìm thấy dự án", 404)

    images = db.execute(
        "SELECT * FROM project_images WHERE project_id = ? ORDER BY sort_order ASC",
        (row["id"],),
    ).fetchall()
    return ok(_row_to_dict(row, [dict(i) for i in images]))


@bp.post("")
@admin_required
def create_project():
    data = request.get_json(silent=True) or {}
    try:
        require(data, ["title", "category"])
    except Exception as exc:  # ValidationError
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))

    if data["category"] not in ALLOWED_CATEGORIES:
        return err(f"category không hợp lệ. Cho phép: {sorted(ALLOWED_CATEGORIES)}", 422)

    db = get_db()
    slug = data.get("slug") or slugify(data["title"])
    base_slug = slug
    n = 1
    while db.execute("SELECT 1 FROM projects WHERE slug = ?", (slug,)).fetchone():
        n += 1
        slug = f"{base_slug}-{n}"

    cur = db.execute(
        """INSERT INTO projects
           (title, slug, category, location, area_m2, year, cost_display, summary, concept,
            design_notes, progress_notes, result_notes, cover_image, status, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            clamp_str(data["title"], 200), slug, data["category"],
            clamp_str(data.get("location"), 200), data.get("area_m2"), data.get("year"),
            clamp_str(data.get("cost_display"), 100), clamp_str(data.get("summary"), 2000),
            clamp_str(data.get("concept"), 4000), clamp_str(data.get("design_notes"), 4000),
            clamp_str(data.get("progress_notes"), 4000), clamp_str(data.get("result_notes"), 4000),
            clamp_str(data.get("cover_image"), 500), data.get("status", "draft"),
            as_int(data.get("sort_order"), 0),
        ),
    )
    db.commit()
    logger.info("Project created: id=%s slug=%s", cur.lastrowid, slug)
    return ok({"id": cur.lastrowid, "slug": slug}, 201)


@bp.put("/<int:project_id>")
@admin_required
def update_project(project_id):
    db = get_db()
    existing = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if existing is None:
        return err("Không tìm thấy dự án", 404)

    data = request.get_json(silent=True) or {}
    if "category" in data and data["category"] not in ALLOWED_CATEGORIES:
        return err(f"category không hợp lệ. Cho phép: {sorted(ALLOWED_CATEGORIES)}", 422)

    fields = [
        "title", "category", "location", "area_m2", "year", "cost_display", "summary",
        "concept", "design_notes", "progress_notes", "result_notes", "cover_image",
        "status", "sort_order",
    ]
    updates, params = [], []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return err("Không có dữ liệu để cập nhật", 400)

    updates.append("updated_at = datetime('now')")
    params.append(project_id)
    db.execute(f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    logger.info("Project updated: id=%s", project_id)
    return ok({"id": project_id})


@bp.delete("/<int:project_id>")
@admin_required
def delete_project(project_id):
    db = get_db()
    existing = db.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
    if existing is None:
        return err("Không tìm thấy dự án", 404)
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    logger.info("Project deleted: id=%s", project_id)
    return ok({"id": project_id})


@bp.post("/<int:project_id>/images")
@admin_required
def add_project_image(project_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone():
        return err("Không tìm thấy dự án", 404)

    data = request.get_json(silent=True) or {}
    try:
        require(data, ["image_url"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))

    cur = db.execute(
        "INSERT INTO project_images (project_id, image_url, caption, sort_order) VALUES (?, ?, ?, ?)",
        (project_id, data["image_url"], clamp_str(data.get("caption"), 300), as_int(data.get("sort_order"), 0)),
    )
    db.commit()
    return ok({"id": cur.lastrowid}, 201)


@bp.delete("/images/<int:image_id>")
@admin_required
def delete_project_image(image_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM project_images WHERE id = ?", (image_id,)).fetchone():
        return err("Không tìm thấy hình ảnh", 404)
    db.execute("DELETE FROM project_images WHERE id = ?", (image_id,))
    db.commit()
    return ok({"id": image_id})
