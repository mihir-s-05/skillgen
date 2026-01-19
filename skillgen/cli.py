import argparse
import os
import sys

from .config import load_config
from .fetcher import discover_llms_url, fetch_text, fetch_documents
from .parser import parse_llms_text
from .generator import generate_skill
from .installer import install_skill
from .models import GeneratorOptions


def _is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Agent Skills from llms.txt")
    parser.add_argument("source", help="llms.txt URL or base docs URL or local file path")
    parser.add_argument("--out", default=".", help="Output directory")
    parser.add_argument("--name", default=None, help="Override skill name")
    parser.add_argument("--include-optional", action="store_true", help="Include Optional section")
    parser.add_argument("--exclude-optional", action="store_true", help="Exclude Optional section")
    parser.add_argument("--snapshot", action="store_true", help="Snapshot referenced docs")
    parser.add_argument("--no-snapshot", action="store_true", help="Do not snapshot referenced docs")
    parser.add_argument("--allow-external", action="store_true", help="Allow external domains")
    parser.add_argument("--deny-external", action="store_true", help="Deny external domains")
    parser.add_argument("--fetch-mode", choices=["full", "metadata"], help="Fetch mode")
    parser.add_argument("--max-bytes-per-doc", type=int, help="Max bytes per doc")
    parser.add_argument("--max-total-bytes", type=int, help="Max total bytes")
    parser.add_argument("--max-pages", type=int, help="Max pages to fetch")
    parser.add_argument("--max-page-chars", type=int, help="Max chars per page")
    parser.add_argument("--by-section", action="store_true", help="Aggregate by section")
    parser.add_argument("--by-link", action="store_true", help="One file per link")
    parser.add_argument("--keyword-mode", choices=["auto", "heuristic", "llm"], help="Keyword mode")
    parser.add_argument("--llm-provider", choices=["none", "transformers"], help="LLM provider")
    parser.add_argument("--llm-model", help="LLM model name")
    parser.add_argument("--llm-device", help="LLM device (cpu/cuda/auto)")
    parser.add_argument("--llm-max-new-tokens", type=int, help="Max new tokens for LLM output")
    parser.add_argument("--llm-temperature", type=float, help="LLM temperature")
    parser.add_argument("--no-llm-fallback", action="store_true", help="Fail if LLM is unavailable")
    parser.add_argument("--user-agent", help="Custom User-Agent")
    parser.add_argument("--config", help="Path to skillgen.yaml")
    parser.add_argument("--target", choices=["generic", "codex", "claude", "opencode", "amp", "roo", "cursor"], help="Install target")
    parser.add_argument("--scope", choices=["project", "user"], help="Target scope")
    parser.add_argument("--target-dir", help="Override target directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing target")
    parser.add_argument("--roo-mode", help="Roo mode folder name (e.g., skills-code)")

    args = parser.parse_args()

    cfg = load_config(args.config)

    include_optional = cfg["include_optional"]
    if args.include_optional:
        include_optional = True
    if args.exclude_optional:
        include_optional = False

    snapshot = cfg["snapshot"]
    if args.snapshot:
        snapshot = True
    if args.no_snapshot:
        snapshot = False

    allow_external = cfg.get("allow_external", False)
    if args.allow_external:
        allow_external = True
    if args.deny_external:
        allow_external = False

    fetch_mode = args.fetch_mode or cfg.get("fetch_mode", "full")
    max_bytes_per_doc = args.max_bytes_per_doc or cfg["max_bytes_per_doc"]
    max_total_bytes = args.max_total_bytes or cfg["max_total_bytes"]
    max_pages = args.max_pages or cfg["max_pages"]
    max_page_chars = args.max_page_chars or cfg["max_page_chars"]
    by_section = cfg.get("by_section", True)
    if args.by_link:
        by_section = False
    elif args.by_section:
        by_section = True

    keyword_mode = args.keyword_mode or cfg["keyword_mode"]
    llm_provider = args.llm_provider or cfg["llm_provider"]
    llm_model = args.llm_model or cfg["llm_model"]
    llm_device = args.llm_device or cfg.get("llm_device", "cpu")
    llm_max_new_tokens = args.llm_max_new_tokens or cfg.get("llm_max_new_tokens", 512)
    llm_temperature = args.llm_temperature if args.llm_temperature is not None else cfg.get("llm_temperature", 0.2)
    user_agent = args.user_agent or cfg["user_agent"]
    llm_fallback = cfg.get("llm_fallback", True)
    if args.no_llm_fallback:
        llm_fallback = False
    target = args.target or cfg.get("target", "generic")
    scope = args.scope or cfg.get("scope", "project")
    overwrite = args.overwrite or cfg.get("overwrite", False)
    roo_mode = args.roo_mode or cfg.get("roo_mode")

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
        fetch_mode=fetch_mode,
        max_bytes_per_doc=max_bytes_per_doc,
        max_total_bytes=max_total_bytes,
        max_pages=max_pages,
        max_page_chars=max_page_chars,
        by_section=by_section,
        keyword_mode=keyword_mode,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_device=llm_device,
        llm_max_new_tokens=llm_max_new_tokens,
        llm_temperature=llm_temperature,
        llm_fallback=llm_fallback,
        user_agent=user_agent,
        domain_allowlist=cfg.get("domain_allowlist"),
        target=target,
        target_dir=args.target_dir,
        scope=scope,
        overwrite=overwrite,
        roo_mode=roo_mode,
        config_path=args.config,
    )

    fetch_result = None
    if snapshot and fetch_mode == "full":
        fetch_result = fetch_documents(
            links=[l for s in parsed.sections for l in s.links],
            base_url=source_url,
            include_optional=include_optional,
            allow_external=allow_external,
            domain_allowlist=cfg.get("domain_allowlist"),
            max_pages=max_pages,
            max_bytes_per_doc=max_bytes_per_doc,
            max_total_bytes=max_total_bytes,
            user_agent=user_agent,
        )

    output_path = generate_skill(parsed, options, fetch_result)
    install_path = install_skill(
        output_path,
        os.path.basename(output_path),
        target=target,
        scope=scope,
        target_dir=args.target_dir,
        overwrite=overwrite,
        roo_mode=roo_mode,
        cwd=os.getcwd(),
    )
    print(f"Skill generated at: {output_path}")
    if target != "generic":
        print(f"Installed to: {install_path}")


if __name__ == "__main__":
    main()
