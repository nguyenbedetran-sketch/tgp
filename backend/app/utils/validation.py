"""Small, dependency-free input validation helpers.

Pydantic is available in this environment, but is used here only for
lightweight ad-hoc validation (no FastAPI, so no automatic request-model
binding) - see routes for usage. These helpers cover the common cases:
required fields, string length, phone/email shape and numeric ranges.
"""
import re

PHONE_RE = re.compile(r"^[0-9+()\-\s]{8,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(str(errors))


def require(data: dict, fields: list[str]) -> dict:
    """Raise ValidationError listing every missing/blank required field."""
    errors = {}
    for f in fields:
        value = data.get(f)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors[f] = "Trường này là bắt buộc"
    if errors:
        raise ValidationError(errors)
    return data


def valid_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone.strip())) if phone else False


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip())) if email else False


def clamp_str(value, max_len: int) -> str:
    value = "" if value is None else str(value)
    return value[:max_len]


def as_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
