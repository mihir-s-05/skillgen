import os
from typing import Optional, Dict, Any

import yaml


def default_config() -> Dict[str, Any]:
    return {
        "snapshot": True,
        "include_optional": False,
        "max_pages": 500,
        "max_page_chars": 200000,
        "max_total_bytes": 100000000,
        "max_bytes_per_doc": 5000000,
        "domain_allowlist": [],
        "allow_external": False,
        "keyword_mode": "llm",
        "llm_provider": "transformers",
        "llm_model": "Qwen/Qwen3-0.6B",
        "llm_device": "auto",
        "llm_max_new_tokens": 512,
        "llm_temperature": 0.2,
        "llm_fallback": True,
        "fetch_mode": "full",
        "by_section": True,
        "user_agent": "AutoSkill/0.1",
        "target": "generic",
        "scope": "user",
        "overwrite": False,
        "roo_mode": None,
    }


def load_config(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        path = "autoskill.yaml"
        if not os.path.exists(path):
            return default_config()
    if not os.path.exists(path):
        return default_config()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg = default_config()
    cfg.update(data)
    return cfg
