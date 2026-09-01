"""Tiny Vietnamese-aware slugify helper (no external unidecode dependency)."""
import re
import unicodedata

_VN_MAP = str.maketrans({
    "đ": "d", "Đ": "D",
})


def slugify(text: str) -> str:
    if not text:
        return ""
    text = text.translate(_VN_MAP)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "item"
