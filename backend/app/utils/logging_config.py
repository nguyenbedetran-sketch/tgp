"""Centralised logging configuration for the backend."""
import logging
import logging.handlers
from pathlib import Path

from app.config.settings import config


def setup_logging():
    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("tgp")
    root.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    if root.handlers:
        # Avoid duplicate handlers when the reloader re-imports this module.
        return root

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    return root
