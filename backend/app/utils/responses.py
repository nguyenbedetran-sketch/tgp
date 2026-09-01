"""Small helpers to keep JSON API responses consistent across all routes."""
from flask import jsonify


def ok(data=None, status: int = 200, **extra):
    body = {"success": True}
    if data is not None:
        body["data"] = data
    body.update(extra)
    return jsonify(body), status


def err(message: str, status: int = 400, errors: dict | None = None):
    body = {"success": False, "error": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status
