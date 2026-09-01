"""Contact / consultation-request routes.

POST /api/contact is the public "Nhan tu van" form on the website.
The /api/admin/contacts/* routes let staff manage incoming leads.
"""
import logging

from flask import Blueprint, request

from app.models.db import get_db
from app.services.security import admin_required
from app.utils.rate_limit import rate_limited
from app.utils.responses import err, ok
from app.utils.validation import ValidationError, clamp_str, require, valid_email, valid_phone

logger = logging.getLogger("tgp.contact")

bp = Blueprint("contact", __name__, url_prefix="/api/contact")
admin_bp = Blueprint("contact_admin", __name__, url_prefix="/api/admin/contacts")


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "")


@bp.post("")
@rate_limited()
def submit_contact():
    data = request.get_json(silent=True) or {}

    # Basic honeypot anti-spam: a hidden field named "website" that real
    # users never fill in. Bots that auto-fill every field trip this.
    if (data.get("website") or "").strip():
        logger.warning("Honeypot triggered for contact submission from %s", _client_ip())
        # Pretend success so bots don't learn the honeypot exists.
        return ok({"message": "Đã gửi yêu cầu tư vấn thành công"}, 201)

    try:
        require(data, ["full_name", "phone"])
    except ValidationError as exc:
        return err("Thiếu dữ liệu bắt buộc", 422, exc.errors)

    phone = (data.get("phone") or "").strip()
    if not valid_phone(phone):
        return err("Số điện thoại không hợp lệ", 422, {"phone": "Số điện thoại không hợp lệ"})

    email = (data.get("email") or "").strip()
    if email and not valid_email(email):
        return err("Email không hợp lệ", 422, {"email": "Email không hợp lệ"})

    db = get_db()
    cur = db.execute(
        """INSERT INTO contacts
           (full_name, phone, email, location, construction_type, area_expected, budget,
            message, ip_address)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            clamp_str(data["full_name"], 150), phone, email,
            clamp_str(data.get("location"), 200), clamp_str(data.get("construction_type"), 100),
            clamp_str(data.get("area_expected"), 100), clamp_str(data.get("budget"), 100),
            clamp_str(data.get("message"), 2000), _client_ip(),
        ),
    )
    db.commit()
    logger.info("New contact request id=%s from %s", cur.lastrowid, phone)

    # NOTE: notification hook - wire this up to email/SMS/Zalo OA once the
    # company provides real credentials (see .env.example NOTIFY_* keys).
    # Left as a clean extension point rather than a fake integration.

    return ok({"id": cur.lastrowid, "message": "Đã gửi yêu cầu tư vấn thành công"}, 201)


@admin_bp.get("")
@admin_required
def list_contacts():
    db = get_db()
    status = request.args.get("status")
    query = "SELECT * FROM contacts WHERE 1=1"
    params: list = []
    if status and status != "all":
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()
    return ok([dict(r) for r in rows])


@admin_bp.put("/<int:contact_id>")
@admin_required
def update_contact(contact_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,)).fetchone():
        return err("Không tìm thấy yêu cầu tư vấn", 404)

    data = request.get_json(silent=True) or {}
    if "status" not in data or data["status"] not in ("new", "contacted", "closed"):
        return err("status không hợp lệ (new | contacted | closed)", 422)

    db.execute("UPDATE contacts SET status = ? WHERE id = ?", (data["status"], contact_id))
    db.commit()
    return ok({"id": contact_id})


@admin_bp.delete("/<int:contact_id>")
@admin_required
def delete_contact(contact_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,)).fetchone():
        return err("Không tìm thấy yêu cầu tư vấn", 404)
    db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    db.commit()
    return ok({"id": contact_id})
