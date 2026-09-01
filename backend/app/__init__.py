"""
Flask application factory for the Tran Gia Phat backend.

Design notes (see README for the full rationale):
  - Flask was chosen over FastAPI because FastAPI/SQLAlchemy could not be
    installed in this build environment (no package-registry access), while
    Flask + Werkzeug + PyJWT + python-dotenv were already available. The
    project brief explicitly allows either ("Uu tien su dung Flask hoac
    FastAPI"). All of the required capabilities (REST API, validation,
    error handling, logging, auth) are implemented for real below.
  - Persistence uses Python's stdlib sqlite3 (see app/models/db.py) rather
    than an ORM, for the same reason.
  - This single Flask process also serves the static frontend (../frontend)
    and uploaded images for a friction-free local run; in production you
    would typically put nginx in front (see README "Huong dan deploy").
"""
import logging
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from app.config.settings import config
from app.models.db import init_db, register_teardown
from app.services.seed import seed_if_empty
from app.utils.logging_config import setup_logging

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def create_app() -> Flask:
    setup_logging()
    logger = logging.getLogger("tgp.app")

    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1024
    app.config["JSON_AS_ASCII"] = False  # keep Vietnamese diacritics readable in raw JSON

    register_teardown(app)

    with app.app_context():
        init_db()
        try:
            seed_if_empty()
        except Exception:
            logger.exception("Seeding initial data failed (continuing without seed data)")

    _register_cors(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_static_routes(app)
    _register_request_logging(app)

    logger.info("Tran Gia Phat backend started (env=%s, debug=%s)", config.ENV, config.DEBUG)
    return app


def _register_cors(app: Flask):
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        allowed = config.CORS_ORIGINS
        if "*" in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        elif origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Vary"] = "Origin"
        return response

    @app.route("/api/<path:_any>", methods=["OPTIONS"])
    def cors_preflight(_any):
        return "", 204


def _register_blueprints(app: Flask):
    from app.routes import (
        admin_routes, auth_routes, blog_routes, contact_routes, estimate_routes,
        hero_slide_routes, project_routes, service_routes, settings_routes,
        strength_routes, team_routes, testimonial_routes, upload_routes, visit_routes,
    )

    for module in (
        auth_routes, project_routes, service_routes, blog_routes, contact_routes,
        estimate_routes, admin_routes, team_routes, testimonial_routes,
        settings_routes, upload_routes, visit_routes, hero_slide_routes, strength_routes,
    ):
        app.register_blueprint(module.bp)

    app.register_blueprint(contact_routes.admin_bp)
    app.register_blueprint(settings_routes.admin_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"success": True, "status": "ok", "service": "tgp-backend"})


def _register_error_handlers(app: Flask):
    logger = logging.getLogger("tgp.errors")

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"success": False, "error": "Không tìm thấy tài nguyên"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"success": False, "error": "Phương thức không được hỗ trợ"}), 405

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"success": False, "error": "Dữ liệu gửi lên quá lớn"}), 413

    @app.errorhandler(429)
    def too_many_requests(_e):
        return jsonify({"success": False, "error": "Quá nhiều yêu cầu, vui lòng thử lại sau"}), 429

    @app.errorhandler(Exception)
    def handle_uncaught(e):
        logger.exception("Unhandled exception while processing %s %s", request.method, request.path)
        return jsonify({"success": False, "error": "Lỗi hệ thống, vui lòng thử lại sau"}), 500


def _register_static_routes(app: Flask):
    """Serve the static frontend and uploaded images from this same process
    for a zero-config local run. Production deployments should instead
    serve `frontend/` via nginx/CDN directly (see README)."""

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(config.UPLOAD_DIR, filename)

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:filename>")
    def frontend_files(filename):
        full_path = FRONTEND_DIR / filename
        if full_path.is_file():
            return send_from_directory(FRONTEND_DIR, filename)
        # SPA-ish fallback for /pages/xyz style links without extension
        html_guess = FRONTEND_DIR / "pages" / f"{filename}.html"
        if html_guess.is_file():
            return send_from_directory(FRONTEND_DIR / "pages", f"{filename}.html")
        return jsonify({"success": False, "error": "Không tìm thấy trang"}), 404


def _register_request_logging(app: Flask):
    logger = logging.getLogger("tgp.access")

    @app.after_request
    def log_request(response):
        if not request.path.startswith("/uploads") and not request.path.startswith(("/css", "/js", "/assets")):
            logger.info("%s %s -> %s", request.method, request.path, response.status_code)
        return response
