"""Admin dashboard summary + data export (delegates rendering to the Java
report service, see app/services/java_bridge.py)."""
import logging

from flask import Blueprint, Response, request

from app.models.db import get_db
from app.services.java_bridge import JavaBridgeError, generate_report
from app.services.security import admin_required
from app.utils.responses import err, ok

logger = logging.getLogger("tgp.admin")

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/dashboard")
@admin_required
def dashboard():
    db = get_db()

    def scalar(query, params=()):
        return db.execute(query, params).fetchone()[0]

    total_projects = scalar("SELECT COUNT(*) FROM projects")
    published_projects = scalar("SELECT COUNT(*) FROM projects WHERE status = 'published'")
    total_contacts = scalar("SELECT COUNT(*) FROM contacts")
    new_contacts = scalar("SELECT COUNT(*) FROM contacts WHERE status = 'new'")
    contacts_this_month = scalar(
        "SELECT COUNT(*) FROM contacts WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
    )
    total_blog_posts = scalar("SELECT COUNT(*) FROM blog_posts")
    total_estimates = scalar("SELECT COUNT(*) FROM estimates")
    total_page_views = scalar("SELECT COUNT(*) FROM page_views")
    page_views_this_month = scalar(
        "SELECT COUNT(*) FROM page_views WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
    )

    monthly_contacts = db.execute(
        """SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS total
           FROM contacts GROUP BY month ORDER BY month DESC LIMIT 12"""
    ).fetchall()
    monthly_views = db.execute(
        """SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS total
           FROM page_views GROUP BY month ORDER BY month DESC LIMIT 12"""
    ).fetchall()
    recent_contacts = db.execute(
        "SELECT id, full_name, phone, construction_type, status, created_at FROM contacts "
        "ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    return ok({
        "total_projects": total_projects,
        "published_projects": published_projects,
        "total_contacts": total_contacts,
        "new_contacts": new_contacts,
        "contacts_this_month": contacts_this_month,
        "total_blog_posts": total_blog_posts,
        "total_estimates": total_estimates,
        "total_page_views": total_page_views,
        "page_views_this_month": page_views_this_month,
        "monthly_contacts": [dict(r) for r in monthly_contacts],
        "monthly_page_views": [dict(r) for r in monthly_views],
        "recent_contacts": [dict(r) for r in recent_contacts],
    })


@bp.get("/export/<dataset>")
@admin_required
def export(dataset):
    fmt = request.args.get("format", "csv")
    if fmt not in ("csv", "json"):
        return err("format phải là csv hoặc json", 422)

    db = get_db()
    if dataset == "projects":
        rows = db.execute(
            "SELECT id, title, category, location, area_m2, year, status, created_at FROM projects "
            "ORDER BY created_at DESC"
        ).fetchall()
        title = "Danh sach du an"
        columns = ["id", "title", "category", "location", "area_m2", "year", "status", "created_at"]
    elif dataset == "contacts":
        rows = db.execute(
            "SELECT id, full_name, phone, email, location, construction_type, status, created_at "
            "FROM contacts ORDER BY created_at DESC"
        ).fetchall()
        title = "Danh sach yeu cau tu van"
        columns = ["id", "full_name", "phone", "email", "location", "construction_type", "status", "created_at"]
    else:
        return err("dataset không hợp lệ (projects | contacts)", 404)

    payload_rows = [dict(r) for r in rows]

    try:
        report_text = generate_report(title, payload_rows, fmt=fmt, columns=columns)
    except JavaBridgeError as exc:
        logger.error("Export failed: %s", exc)
        return err(str(exc), 502)

    mimetype = "text/csv" if fmt == "csv" else "application/json"
    filename = f"{dataset}.{fmt}"
    return Response(
        report_text,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
