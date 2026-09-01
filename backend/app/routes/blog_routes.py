"""Blog / news routes."""
import logging

from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.responses import err, ok
from app.utils.slugify import slugify
from app.utils.validation import as_int, clamp_str, require

logger = logging.getLogger("tgp.blog")

bp = Blueprint("blog", __name__, url_prefix="/api/blog")


@bp.get("")
def list_posts():
    db = get_db()
    category = request.args.get("category")
    status = request.args.get("status", "published")
    limit = as_int(request.args.get("limit"), 0)

    query = ("SELECT id, title, slug, category, author, excerpt, thumbnail_url, "
              "status, published_at, created_at FROM blog_posts WHERE 1=1")
    params: list = []
    if status != "all":
        query += " AND status = ?"
        params.append(status)
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY COALESCE(published_at, created_at) DESC"
    if limit:
        query += " LIMIT ?"
        params.append(limit)

    rows = db.execute(query, params).fetchall()
    return ok([dict(r) for r in rows])


@bp.get("/<identifier>")
def get_post(identifier):
    db = get_db()
    if identifier.isdigit():
        row = db.execute("SELECT * FROM blog_posts WHERE id = ?", (identifier,)).fetchone()
    else:
        row = db.execute("SELECT * FROM blog_posts WHERE slug = ?", (identifier,)).fetchone()
    if row is None:
        return err("Không tìm thấy bài viết", 404)
    return ok(dict(row))


@bp.post("")
@admin_required
def create_post():
    data = request.get_json(silent=True) or {}
    try:
        require(data, ["title", "content"])
    except Exception as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, getattr(exc, "errors", {}))

    db = get_db()
    slug = data.get("slug") or slugify(data["title"])
    base_slug = slug
    n = 1
    while db.execute("SELECT 1 FROM blog_posts WHERE slug = ?", (slug,)).fetchone():
        n += 1
        slug = f"{base_slug}-{n}"

    status = data.get("status", "draft")
    published_at = "datetime('now')" if status == "published" else "NULL"
    cur = db.execute(
        f"""INSERT INTO blog_posts
           (title, slug, category, author, excerpt, content, thumbnail_url,
            seo_title, seo_description, status, published_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {published_at})""",
        (
            clamp_str(data["title"], 250), slug, clamp_str(data.get("category"), 100),
            clamp_str(data.get("author"), 100), clamp_str(data.get("excerpt"), 500),
            data["content"], clamp_str(data.get("thumbnail_url"), 500),
            clamp_str(data.get("seo_title"), 250), clamp_str(data.get("seo_description"), 500),
            status,
        ),
    )
    db.commit()
    return ok({"id": cur.lastrowid, "slug": slug}, 201)


@bp.put("/<int:post_id>")
@admin_required
def update_post(post_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM blog_posts WHERE id = ?", (post_id,)).fetchone():
        return err("Không tìm thấy bài viết", 404)

    data = request.get_json(silent=True) or {}
    fields = ["title", "category", "author", "excerpt", "content", "thumbnail_url",
              "seo_title", "seo_description", "status"]
    updates, params = [], []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if data.get("status") == "published":
        updates.append("published_at = COALESCE(published_at, datetime('now'))")
    if not updates:
        return err("Không có dữ liệu để cập nhật", 400)
    params.append(post_id)
    db.execute(f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return ok({"id": post_id})


@bp.delete("/<int:post_id>")
@admin_required
def delete_post(post_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM blog_posts WHERE id = ?", (post_id,)).fetchone():
        return err("Không tìm thấy bài viết", 404)
    db.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    db.commit()
    return ok({"id": post_id})
