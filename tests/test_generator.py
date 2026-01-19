import os

from skillgen.parser import parse_llms_text
from skillgen.generator import generate_skill
from skillgen.models import GeneratorOptions


def test_generate_skill_no_snapshot(tmp_path):
    text = (
        "# Sample Docs\n"
        "> Summary line.\n"
        "\n"
        "## Guides\n"
        "- [Intro](https://example.com/intro)\n"
    )
    parsed = parse_llms_text(text, source_url="https://example.com/llms.txt")
    options = GeneratorOptions(
        output_dir=str(tmp_path),
        name_override="sample-docs",
        include_optional=False,
        snapshot=False,
        allow_external=False,
        fetch_mode="metadata",
        max_bytes_per_doc=1000000,
        max_total_bytes=10000000,
        max_pages=10,
        max_page_chars=10000,
        by_section=True,
        keyword_mode="heuristic",
        llm_provider="none",
        llm_model=None,
        llm_device="cpu",
        llm_max_new_tokens=128,
        llm_temperature=0.2,
        llm_fallback=True,
        user_agent="SkillGen/0.1",
        target="generic",
        target_dir=None,
        scope="project",
        overwrite=False,
        roo_mode=None,
    )
    out = generate_skill(parsed, options, fetch_result=None)
    assert os.path.exists(os.path.join(out, "SKILL.md"))
    assert os.path.exists(os.path.join(out, "references", "INDEX.md"))
    assert os.path.exists(os.path.join(out, "references", "catalog.json"))
