import os
import tempfile
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from .config import load_config, limits_for_level
from .fetcher import discover_llms_url, fetch_text, fetch_documents
from .parser import parse_llms_text
from .generator import generate_skill
from .installer import install_skill, resolve_install_dir
from .models import GeneratorOptions


mcp = FastMCP(
    name="skillgen",
    instructions="""Generate Agent Skills from llms.txt documentation files.

Defaults:
- Install to ~/.agents/skills
- Use heuristic keyword/description generation
- Use balanced preset limits

Set for_claude=true to install to ~/.claude/skills.""",
)


@mcp.tool()
def generate_skill_from_url(
    source_url: str,
    output_dir: Optional[str] = None,
    name: Optional[str] = None,
    include_optional: bool = False,
    snapshot: bool = True,
    allow_external: bool = False,
    heuristic_level: Literal["compact", "balanced", "verbose"] = "balanced",
    for_claude: bool = False,
) -> dict:
    cfg = load_config(None)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="skillgen_")

    limits = limits_for_level(heuristic_level)
    user_agent = cfg.get("user_agent", "SkillGen/0.1")

    llms_url = discover_llms_url(source_url, user_agent)
    text = fetch_text(llms_url, user_agent)
    parsed = parse_llms_text(text, source_url=llms_url)

    options = GeneratorOptions(
        output_dir=output_dir,
        name_override=name,
        include_optional=include_optional,
        snapshot=snapshot,
        allow_external=allow_external,
        max_bytes_per_doc=limits["max_bytes_per_doc"],
        max_total_bytes=limits["max_total_bytes"],
        max_pages=limits["max_pages"],
        max_page_chars=limits["max_page_chars"],
        heuristic_level=heuristic_level,
        user_agent=user_agent,
        domain_allowlist=cfg.get("domain_allowlist"),
        install_for_claude=for_claude,
        config_path=None,
    )

    fetch_result = None
    if snapshot:
        fetch_result = fetch_documents(
            links=[l for s in parsed.sections for l in s.links],
            base_url=llms_url,
            include_optional=include_optional,
            allow_external=allow_external,
            domain_allowlist=cfg.get("domain_allowlist"),
            max_pages=options.max_pages,
            max_bytes_per_doc=options.max_bytes_per_doc,
            max_total_bytes=options.max_total_bytes,
            user_agent=user_agent,
        )

    output_path = generate_skill(parsed, options, fetch_result)
    install_path = install_skill(
        output_path,
        os.path.basename(output_path),
        for_claude=for_claude,
    )

    return {
        "success": True,
        "title": parsed.title,
        "source_url": llms_url,
        "output_path": output_path,
        "install_path": install_path,
        "install_root": resolve_install_dir(for_claude=for_claude),
        "sections": [s.title for s in parsed.sections],
        "link_count": sum(len(s.links) for s in parsed.sections),
        "warnings": fetch_result.warnings if fetch_result else [],
    }


@mcp.tool()
def generate_skill_from_text(
    llms_text: str,
    output_dir: Optional[str] = None,
    name: Optional[str] = None,
    include_optional: bool = False,
    heuristic_level: Literal["compact", "balanced", "verbose"] = "balanced",
    for_claude: bool = False,
) -> dict:
    cfg = load_config(None)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="skillgen_")

    limits = limits_for_level(heuristic_level)
    parsed = parse_llms_text(llms_text, source_url=None)

    options = GeneratorOptions(
        output_dir=output_dir,
        name_override=name,
        include_optional=include_optional,
        snapshot=False,
        allow_external=False,
        max_bytes_per_doc=limits["max_bytes_per_doc"],
        max_total_bytes=limits["max_total_bytes"],
        max_pages=limits["max_pages"],
        max_page_chars=limits["max_page_chars"],
        heuristic_level=heuristic_level,
        user_agent=cfg.get("user_agent", "SkillGen/0.1"),
        domain_allowlist=None,
        install_for_claude=for_claude,
        config_path=None,
    )

    output_path = generate_skill(parsed, options, None)
    install_path = install_skill(
        output_path,
        os.path.basename(output_path),
        for_claude=for_claude,
    )

    return {
        "success": True,
        "title": parsed.title,
        "output_path": output_path,
        "install_path": install_path,
        "install_root": resolve_install_dir(for_claude=for_claude),
        "sections": [s.title for s in parsed.sections],
        "link_count": sum(len(s.links) for s in parsed.sections),
    }


@mcp.tool()
def parse_llms(source: str, is_url: bool = True) -> dict:
    cfg = load_config(None)

    if is_url:
        llms_url = discover_llms_url(source, cfg.get("user_agent", "SkillGen/0.1"))
        text = fetch_text(llms_url, cfg.get("user_agent", "SkillGen/0.1"))
        source_url = llms_url
    else:
        text = source
        source_url = None

    parsed = parse_llms_text(text, source_url=source_url)
    return {
        "title": parsed.title,
        "summary": parsed.summary,
        "preamble": parsed.preamble,
        "source_url": parsed.source_url,
        "sections": [
            {
                "title": section.title,
                "slug": section.slug,
                "optional": section.optional,
                "links": [
                    {
                        "title": link.title,
                        "url": link.url,
                        "note": link.note,
                        "optional": link.optional,
                    }
                    for link in section.links
                ],
            }
            for section in parsed.sections
        ],
        "total_links": sum(len(s.links) for s in parsed.sections),
    }


@mcp.tool()
def discover_llms(base_url: str) -> dict:
    cfg = load_config(None)
    user_agent = cfg.get("user_agent", "SkillGen/0.1")
    try:
        llms_url = discover_llms_url(base_url, user_agent)
        return {
            "success": True,
            "llms_url": llms_url,
            "base_url": base_url,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "base_url": base_url,
        }


@mcp.tool()
def get_config() -> dict:
    cfg = load_config(None)
    return {
        "config": cfg,
        "presets": {
            level: limits_for_level(level) for level in ("compact", "balanced", "verbose")
        },
        "install_paths": {
            "default": resolve_install_dir(for_claude=False),
            "claude": resolve_install_dir(for_claude=True),
        },
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
