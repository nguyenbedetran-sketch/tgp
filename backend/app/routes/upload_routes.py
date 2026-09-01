"""Admin image upload (project photos, blog thumbnails, team photos, banners).

Security notes:
  - file extension is checked against an allow-list (config.ALLOWED_UPLOAD_EXTENSIONS)
  - the actual image content is verified with a magic-bytes sniff so a
    renamed .php/.html file cannot slip through as "photo.jpg"
  - filenames are regenerated (uuid4) - the client-supplied filename is
    never trusted or used to build a filesystem path
  - Flask's MAX_CONTENT_LENGTH (see app/__init__.py) enforces the request
    size cap at the WSGI layer before this handler even runs
"""
import logging
import uuid
from pathlib import Path

from flask import Blueprint, request

from app.config.settings import config
from app.services.security import admin_required
from app.utils.responses import err, ok

logger = logging.getLogger("tgp.upload")

bp = Blueprint("upload", __name__, url_prefix="/api/admin/upload")

# Minimal magic-byte signatures for the image types we accept.
_MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",  # WEBP starts with RIFF....WEBP, checked further below
}


def _sniff_extension(head: bytes) -> str | None:
    for magic, ext in _MAGIC_BYTES.items():
        if head.startswith(magic):
            if ext == "webp" and b"WEBP" not in head[:16]:
                continue
            return ext
    return None


@bp.post("")
@admin_required
def upload_file():
    if "file" not in request.files:
        return err("Không có file được gửi lên (trường 'file')", 400)

    file = request.files["file"]
    if not file or file.filename == "":
        return err("File rỗng hoặc không hợp lệ", 400)

    original_name = file.filename
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in config.ALLOWED_UPLOAD_EXTENSIONS:
        return err(
            f"Định dạng file không được hỗ trợ. Cho phép: {sorted(config.ALLOWED_UPLOAD_EXTENSIONS)}",
            415,
        )

    head = file.stream.read(32)
    file.stream.seek(0)
    sniffed = _sniff_extension(head)
    if sniffed is None:
        return err("Nội dung file không phải là hình ảnh hợp lệ", 415)

    upload_dir = Path(config.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    new_name = f"{uuid.uuid4().hex}.{ext}"
    dest_path = upload_dir / new_name
    file.save(dest_path)

    size_bytes = dest_path.stat().st_size
    max_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        dest_path.unlink(missing_ok=True)
        return err(f"File vuot qua gioi han {config.MAX_UPLOAD_SIZE_MB}MB", 413)

    logger.info("Uploaded file %s (%d bytes) as %s", original_name, size_bytes, new_name)
    return ok({"url": f"/uploads/{new_name}", "filename": new_name, "size_bytes": size_bytes}, 201)
