"""
Application configuration.

All secrets/config come from environment variables (loaded from a .env file
in development). Nothing sensitive is hard-coded in source, per project
requirements.
"""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env from backend/ or project root, whichever exists.
for env_path in (BACKEND_DIR / ".env", PROJECT_ROOT / ".env"):
    if env_path.exists():
        load_dotenv(env_path)
        break


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- General -----------------------------------------------------
    ENV = os.getenv("APP_ENV", "development")  # development | production
    DEBUG = _env_bool("APP_DEBUG", ENV != "production")
    HOST = os.getenv("APP_HOST", "0.0.0.0")
    PORT = int(os.getenv("APP_PORT", "8000"))

    # --- Security ------------------------------------------------------
    # SECRET_KEY must be set explicitly in production. In development we
    # fall back to a randomly generated (per-process) key so the app still
    # boots, but this is NOT persisted -> tokens invalidate on restart.
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8h admin session

    # --- Database --------------------------------------------------------
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH", str(PROJECT_ROOT / "database" / "tgp.db")
    )

    # --- CORS --------------------------------------------------------
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "*").split(",")
        if o.strip()
    ]

    # --- Uploads -----------------------------------------------------
    UPLOAD_DIR = os.getenv(
        "UPLOAD_DIR", str(BACKEND_DIR / "static" / "uploads")
    )
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "8"))
    ALLOWED_UPLOAD_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

    # --- External native/JVM services --------------------------------
    CPP_CALCULATOR_BIN = os.getenv(
        "CPP_CALCULATOR_BIN", str(PROJECT_ROOT / "cpp" / "tgp_calculator")
    )
    JAVA_BIN = os.getenv("JAVA_BIN", "java")
    JAVA_REPORT_JAR = os.getenv(
        "JAVA_REPORT_JAR",
        str(PROJECT_ROOT / "java" / "target" / "tgp-report-service.jar"),
    )

    # --- Rate limiting -------------------------------------------------
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "8"))

    # --- Seed / bootstrap admin account -------------------------------
    ADMIN_BOOTSTRAP_USERNAME = os.getenv("ADMIN_BOOTSTRAP_USERNAME", "admin")
    ADMIN_BOOTSTRAP_EMAIL = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "admin@trangiaphat.example")
    ADMIN_BOOTSTRAP_PASSWORD = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "")

    # --- Logging -------------------------------------------------------
    LOG_DIR = os.getenv("LOG_DIR", str(PROJECT_ROOT / "logs"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
