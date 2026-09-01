"""
Bridge between the Python backend and the Java report/export service
(java/target/tgp-report-service.jar). Used by the admin dashboard to export
projects / consultation leads to CSV or a formatted JSON report.
"""
import json
import logging
import subprocess

from app.config.settings import config

logger = logging.getLogger("tgp.java_bridge")


class JavaBridgeError(RuntimeError):
    pass


def generate_report(title: str, rows: list, fmt: str = "csv", columns: list | None = None,
                     timeout_seconds: float = 10.0) -> str:
    """Invoke the Java report service and return the rendered report text
    (CSV or JSON, depending on `fmt`)."""
    payload = {
        "title": title,
        "format": fmt,
        "columns": columns or [],
        "rows": rows,
    }
    try:
        proc = subprocess.run(
            [config.JAVA_BIN, "-jar", config.JAVA_REPORT_JAR],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        logger.error("Java runtime or report jar not found (jar=%s)", config.JAVA_REPORT_JAR)
        raise JavaBridgeError(
            "Không tìm thấy Java runtime hoặc file tgp-report-service.jar. "
            "Vui lòng build module java/ trước (xem README)."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise JavaBridgeError("Quá trình xuất báo cáo Java bị quá thời gian cho phép") from exc

    if proc.returncode != 0:
        logger.error("Java report service failed: %s", proc.stderr)
        raise JavaBridgeError(proc.stderr.strip() or "Lỗi không xác định từ Java report service")

    return proc.stdout
