import os
from typing import Optional, Dict, Any

import yaml


_LEVEL_LIMITS = {
    "compact": {
        "max_pages": 150,
        "max_page_chars": 100000,
        "max_total_bytes": 20000000,
        "max_bytes_per_doc": 1000000,
    },
    "balanced": {
        "max_pages": 500,
        "max_page_chars": 200000,
        "max_total_bytes": 100000000,
        "max_bytes_per_doc": 5000000,
    },
    "verbose": {
        "max_pages": 1200,
        "max_page_chars": 400000,
        "max_total_bytes": 250000000,
        "max_bytes_per_doc": 10000000,
    },
}


def limits_for_level(level: str) -> Dict[str, int]:
    return _LEVEL_LIMITS.get((level or "balanced").strip().lower(), _LEVEL_LIMITS["balanced"]).copy()


def default_config() -> Dict[str, Any]:
    return {
        "snapshot": True,
        "include_optional": False,
        "domain_allowlist": [],
        "allow_external": False,
        "heuristic_level": "balanced",
        "user_agent": "SkillGen/0.1",
    }


def load_config(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        path = "skillgen.yaml"
        if not os.path.exists(path):
            return default_config()
    if not os.path.exists(path):
        return default_config()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg = default_config()
    cfg.update(data)
    return cfg
