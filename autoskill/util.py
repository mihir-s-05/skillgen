import hashlib
import json
import os
import re
from typing import Any


_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_len: int = 64) -> str:
    text = text.strip().lower()
    text = _slug_re.sub("-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if not text:
        text = "skill"
    return text[:max_len]


def safe_filename(text: str, max_len: int = 80) -> str:
    base = slugify(text, max_len=max_len)
    if not base:
        base = "file"
    return base


def ensure_dir(path: str) -> None:
    if not path:
        return
    os.makedirs(path, exist_ok=True)


def write_text(path: str, content: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(path: str, data: Any) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n\n[TRUNCATED]\n", True
