import os
import json
from pathlib import Path

from skillgen.config import default_config, limits_for_level
from skillgen.generator import generate_skill
from skillgen.models import GeneratorOptions, FetchResult, FetchedDoc
from skillgen.parser import parse_llms_text


def _base_options(tmp_path: Path, snapshot: bool) -> GeneratorOptions:
    limits = limits_for_level("balanced")
    return GeneratorOptions(
        output_dir=str(tmp_path),
        name_override="sample-docs",
        include_optional=False,
        snapshot=snapshot,
        allow_external=False,
        max_bytes_per_doc=limits["max_bytes_per_doc"],
        max_total_bytes=limits["max_total_bytes"],
        max_pages=limits["max_pages"],
        max_page_chars=limits["max_page_chars"],
        heuristic_level="balanced",
        user_agent="SkillGen/0.1",
        domain_allowlist=None,
        install_for_claude=False,
        config_path=None,
    )


def test_generate_skill_no_snapshot(tmp_path):
    text = (
        "# Sample Docs\n"
        "> Summary line.\n"
        "\n"
        "## Guides\n"
        "- [Intro](https://example.com/intro)\n"
    )
    parsed = parse_llms_text(text, source_url="https://example.com/llms.txt")
    options = _base_options(tmp_path, snapshot=False)

    out = generate_skill(parsed, options, fetch_result=None)
    assert os.path.exists(os.path.join(out, "SKILL.md"))
    assert os.path.exists(os.path.join(out, "references", "INDEX.md"))
    assert os.path.exists(os.path.join(out, "references", "catalog.json"))


def test_generate_skill_snapshot_writes_per_link_page(tmp_path):
    text = (
        "# Sample Docs\n"
        "> Summary line.\n"
        "\n"
        "## Guides\n"
        "- [Intro](https://example.com/intro)\n"
    )
    parsed = parse_llms_text(text, source_url="https://example.com/llms.txt")
    options = _base_options(tmp_path, snapshot=True)
    fetch_result = FetchResult(
        docs={
            "https://example.com/intro": FetchedDoc(
                source_url="https://example.com/intro",
                final_url="https://example.com/intro.md",
                content_type="text/markdown",
                status_code=200,
                ok=True,
                error=None,
                bytes=42,
                text="# Intro\n\nBody",
            )
        },
        warnings=[],
    )

    out = generate_skill(parsed, options, fetch_result=fetch_result)
    page = Path(out) / "references" / "sections" / "guides" / "pages" / "intro.md"
    source = Path(str(page) + ".source.json")
    manifest = Path(out) / "manifest.json"
    assert page.exists()
    assert source.exists()
    assert manifest.exists()
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["heuristic_level"] == "balanced"
    assert "fetch_mode" not in manifest_data


def test_default_config_sets_heuristic_mode_defaults():
    cfg = default_config()
    assert cfg["heuristic_level"] == "balanced"
    assert cfg["snapshot"] is True
