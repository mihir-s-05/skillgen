import argparse
import os
import sys

from .config import load_config, limits_for_level
from .fetcher import discover_llms_url, fetch_text, fetch_documents
from .parser import parse_llms_text
from .generator import generate_skill
from .installer import install_skill
from .models import GeneratorOptions


def _is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Agent Skills from llms.txt")
    parser.add_argument("source", help="llms.txt URL, base docs URL, or local file path")
    parser.add_argument("--out", default=".", help="Output directory for generated skill")
    parser.add_argument("--name", default=None, help="Override skill name")
    parser.add_argument("--include-optional", action="store_true", help="Include Optional section links")
    parser.add_argument("--no-snapshot", action="store_true", help="Do not fetch linked pages")
    parser.add_argument("--allow-external", action="store_true", help="Allow external domains")
    parser.add_argument("--heuristic-level", choices=["compact", "balanced", "verbose"], help="Skill description detail level")
    parser.add_argument("--claude", action="store_true", help="Install to ~/.claude/skills instead of ~/.agents/skills")
    args = parser.parse_args()

    cfg = load_config(None)
    include_optional = args.include_optional or cfg.get("include_optional", False)
    snapshot = (not args.no_snapshot) and cfg.get("snapshot", True)
    allow_external = args.allow_external or cfg.get("allow_external", False)
    heuristic_level = args.heuristic_level or cfg.get("heuristic_level", "balanced")
    limits = limits_for_level(heuristic_level)
    user_agent = cfg.get("user_agent", "SkillGen/0.1")

    source_url = None
    if _is_url(args.source):
        llms_url = discover_llms_url(args.source, user_agent)
        text = fetch_text(llms_url, user_agent)
        source_url = llms_url
    else:
        if not os.path.exists(args.source):
            print(f"source not found: {args.source}", file=sys.stderr)
            sys.exit(1)
        with open(args.source, "r", encoding="utf-8") as f:
            text = f.read()

    parsed = parse_llms_text(text, source_url=source_url)

    options = GeneratorOptions(
        output_dir=args.out,
        name_override=args.name,
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
        install_for_claude=args.claude,
        config_path=None,
    )

    fetch_result = None
    if snapshot:
        fetch_result = fetch_documents(
            links=[l for s in parsed.sections for l in s.links],
            base_url=source_url,
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
        for_claude=args.claude,
    )

    print(f"Skill generated at: {output_path}")
    print(f"Installed to: {install_path}")


if __name__ == "__main__":
    main()
