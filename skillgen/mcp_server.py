"""
MCP Server for SkillGen.

Exposes skillgen functionality as MCP tools for use with AI agents.
"""

import os
import tempfile
from typing import Optional, List, Literal

from mcp.server.fastmcp import FastMCP

from .config import load_config, default_config
from .fetcher import discover_llms_url, fetch_text, fetch_documents
from .parser import parse_llms_text
from .generator import generate_skill
from .installer import install_skill, resolve_target_dir
from .models import GeneratorOptions


CLIENT_TO_TARGET = {
    "codex": "codex",
    "codex-cli": "codex",
    "openai-codex": "codex",
    "claude": "claude",
    "claude-code": "claude",
    "claude-desktop": "claude",
    "anthropic": "claude",
    "cursor": "cursor",
    "cursor-ide": "cursor",
    "opencode": "opencode",
    "open-code": "opencode",
    "amp": "amp",
    "sourcegraph": "amp",
    "sourcegraph-amp": "amp",
    "roo": "roo",
    "roo-code": "roo",
    "generic": "generic",
}


def resolve_client_to_target(client: Optional[str]) -> str:
    """Resolve a client identifier to a target name."""
    if not client:
        return "generic"
    normalized = client.lower().strip()
    return CLIENT_TO_TARGET.get(normalized, "generic")


mcp = FastMCP(
    name="skillgen",
    instructions="""Generate Agent Skills from llms.txt documentation files.

IMPORTANT: When calling generate_skill_from_url or generate_skill_from_text, 
identify yourself using the 'client' parameter so the skill is installed to 
the correct location for your platform. Use one of:
- "codex" or "codex-cli" for OpenAI Codex CLI
- "claude" or "claude-code" for Anthropic Claude
- "cursor" for Cursor IDE
- "opencode" for OpenCode
- "amp" or "sourcegraph" for Sourcegraph Amp
- "roo" for Roo Code

Example: generate_skill_from_url(source_url="https://docs.example.com", client="claude")

This will automatically install the skill to your platform's skills directory.""",
)


@mcp.tool()
def generate_skill_from_url(
    source_url: str,
    client: Optional[str] = None,
    output_dir: Optional[str] = None,
    name: Optional[str] = None,
    target: Optional[str] = None,
    scope: Literal["project", "user"] = "user",
    include_optional: bool = False,
    snapshot: bool = True,
    allow_external: bool = False,
    overwrite: bool = False,
    keyword_mode: Optional[Literal["auto", "heuristic", "llm"]] = None,
) -> dict:
    """
    Generate an Agent Skill from an llms.txt URL or base documentation URL.

    This tool fetches an llms.txt file from the given URL, parses it,
    and generates a complete skill package with documentation references.

    Args:
        source_url: URL to llms.txt file or base docs URL (will auto-discover llms.txt)
        client: Identity of the calling agent/client (e.g., "codex", "claude", "cursor", "amp", "roo", "opencode").
                This automatically sets the correct installation target for your platform.
                RECOMMENDED: Always pass your client identity so the skill is installed correctly.
        output_dir: Directory to output the skill (defaults to temp directory)
        name: Override the skill name (defaults to title from llms.txt)
        target: Manual override for installation target (use 'client' instead for automatic detection)
        scope: Target scope - one of: project, user
        include_optional: Whether to include optional documentation sections
        snapshot: Whether to snapshot/fetch referenced documentation pages
        allow_external: Whether to allow fetching from external domains
        overwrite: Whether to overwrite an existing installed skill with the same name (destructive)
        keyword_mode: Keyword generation mode override (auto, heuristic, llm). If omitted, uses server defaults.

    Returns:
        Dictionary with skill generation results including output path and install path
    """
    cfg = default_config()
    resolved_target = target if target else resolve_client_to_target(client)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="skillgen_")

    user_agent = cfg["user_agent"]
    llms_url = discover_llms_url(source_url, user_agent)
    text = fetch_text(llms_url, user_agent)
    parsed = parse_llms_text(text, source_url=llms_url)

    options = GeneratorOptions(
        output_dir=output_dir,
        name_override=name,
        include_optional=include_optional,
        snapshot=snapshot,
        allow_external=allow_external,
        fetch_mode=cfg["fetch_mode"],
        max_bytes_per_doc=cfg["max_bytes_per_doc"],
        max_total_bytes=cfg["max_total_bytes"],
        max_pages=cfg["max_pages"],
        max_page_chars=cfg["max_page_chars"],
        by_section=cfg["by_section"],
        keyword_mode=keyword_mode or cfg["keyword_mode"],
        llm_provider=cfg["llm_provider"],
        llm_model=cfg["llm_model"],
        llm_device=cfg.get("llm_device", "cpu"),
        llm_max_new_tokens=cfg.get("llm_max_new_tokens", 512),
        llm_temperature=cfg.get("llm_temperature", 0.2),
        llm_fallback=cfg.get("llm_fallback", True),
        user_agent=user_agent,
        domain_allowlist=cfg.get("domain_allowlist"),
        target=resolved_target,
        target_dir=None,
        scope=scope,
        overwrite=overwrite,
        roo_mode=None,
        config_path=None,
    )

    fetch_result = None
    if snapshot and options.fetch_mode == "full":
        fetch_result = fetch_documents(
            links=[l for s in parsed.sections for l in s.links],
            base_url=llms_url,
            include_optional=include_optional,
            allow_external=allow_external,
            domain_allowlist=cfg.get("domain_allowlist"),
            max_pages=cfg["max_pages"],
            max_bytes_per_doc=cfg["max_bytes_per_doc"],
            max_total_bytes=cfg["max_total_bytes"],
            user_agent=user_agent,
        )

    output_path = generate_skill(parsed, options, fetch_result)

    install_path = None
    if resolved_target != "generic":
        install_path = install_skill(
            output_path,
            os.path.basename(output_path),
            target=resolved_target,
            scope=scope,
            target_dir=None,
            overwrite=overwrite,
            roo_mode=None,
            cwd=os.getcwd(),
        )

    return {
        "success": True,
        "title": parsed.title,
        "source_url": llms_url,
        "output_path": output_path,
        "install_path": install_path,
        "target": resolved_target,
        "client": client,
        "sections": [s.title for s in parsed.sections],
        "link_count": sum(len(s.links) for s in parsed.sections),
        "warnings": fetch_result.warnings if fetch_result else [],
    }


@mcp.tool()
def generate_skill_from_text(
    llms_text: str,
    client: Optional[str] = None,
    output_dir: Optional[str] = None,
    name: Optional[str] = None,
    target: Optional[str] = None,
    scope: Literal["project", "user"] = "user",
    include_optional: bool = False,
    overwrite: bool = False,
    keyword_mode: Optional[Literal["auto", "heuristic", "llm"]] = None,
) -> dict:
    """
    Generate an Agent Skill from raw llms.txt content.

    This tool takes raw llms.txt content as a string, parses it,
    and generates a skill package. Note: Since no URL is provided,
    document snapshotting is disabled.

    Args:
        llms_text: Raw llms.txt content as a string
        client: Identity of the calling agent/client (e.g., "codex", "claude", "cursor", "amp", "roo", "opencode").
                This automatically sets the correct installation target for your platform.
                RECOMMENDED: Always pass your client identity so the skill is installed correctly.
        output_dir: Directory to output the skill (defaults to temp directory)
        name: Override the skill name (defaults to title from llms.txt)
        target: Manual override for installation target (use 'client' instead for automatic detection)
        scope: Target scope - one of: project, user
        include_optional: Whether to include optional documentation sections
        overwrite: Whether to overwrite an existing installed skill with the same name (destructive)
        keyword_mode: Keyword generation mode override (auto, heuristic, llm). If omitted, uses server defaults.

    Returns:
        Dictionary with skill generation results including output path
    """
    cfg = default_config()
    resolved_target = target if target else resolve_client_to_target(client)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="skillgen_")

    parsed = parse_llms_text(llms_text, source_url=None)

    options = GeneratorOptions(
        output_dir=output_dir,
        name_override=name,
        include_optional=include_optional,
        snapshot=False,
        allow_external=False,
        fetch_mode="metadata",
        max_bytes_per_doc=cfg["max_bytes_per_doc"],
        max_total_bytes=cfg["max_total_bytes"],
        max_pages=cfg["max_pages"],
        max_page_chars=cfg["max_page_chars"],
        by_section=cfg["by_section"],
        keyword_mode=keyword_mode or cfg["keyword_mode"],
        llm_provider=cfg["llm_provider"],
        llm_model=cfg["llm_model"],
        llm_device=cfg.get("llm_device", "cpu"),
        llm_max_new_tokens=cfg.get("llm_max_new_tokens", 512),
        llm_temperature=cfg.get("llm_temperature", 0.2),
        llm_fallback=cfg.get("llm_fallback", True),
        user_agent=cfg["user_agent"],
        domain_allowlist=None,
        target=resolved_target,
        target_dir=None,
        scope=scope,
        overwrite=overwrite,
        roo_mode=None,
        config_path=None,
    )

    output_path = generate_skill(parsed, options, None)

    install_path = None
    if resolved_target != "generic":
        install_path = install_skill(
            output_path,
            os.path.basename(output_path),
            target=resolved_target,
            scope=scope,
            target_dir=None,
            overwrite=overwrite,
            roo_mode=None,
            cwd=os.getcwd(),
        )

    return {
        "success": True,
        "title": parsed.title,
        "output_path": output_path,
        "install_path": install_path,
        "target": resolved_target,
        "client": client,
        "sections": [s.title for s in parsed.sections],
        "link_count": sum(len(s.links) for s in parsed.sections),
    }


@mcp.tool()
def parse_llms(
    source: str,
    is_url: bool = True,
) -> dict:
    """
    Parse an llms.txt file and return its structured content.

    This tool fetches (if URL) or parses (if text) an llms.txt file
    and returns the parsed structure without generating a skill.

    Args:
        source: URL to llms.txt file, or raw llms.txt content
        is_url: Whether source is a URL (True) or raw text content (False)

    Returns:
        Dictionary with parsed llms.txt structure including title, summary, and sections
    """
    cfg = default_config()

    if is_url:
        llms_url = discover_llms_url(source, cfg["user_agent"])
        text = fetch_text(llms_url, cfg["user_agent"])
        source_url = llms_url
    else:
        text = source
        source_url = None

    parsed = parse_llms_text(text, source_url=source_url)

    sections_data = []
    for section in parsed.sections:
        section_info = {
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
        sections_data.append(section_info)

    return {
        "title": parsed.title,
        "summary": parsed.summary,
        "preamble": parsed.preamble,
        "source_url": parsed.source_url,
        "sections": sections_data,
        "total_links": sum(len(s.links) for s in parsed.sections),
    }


@mcp.tool()
def discover_llms(
    base_url: str,
) -> dict:
    """
    Discover the llms.txt URL from a base documentation URL.

    This tool attempts to find the llms.txt file at common locations
    relative to the given base URL (e.g., /llms.txt, /.well-known/llms.txt).

    Args:
        base_url: Base URL of the documentation site

    Returns:
        Dictionary with discovered llms.txt URL or error information
    """
    cfg = default_config()

    try:
        llms_url = discover_llms_url(base_url, cfg["user_agent"])
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
def list_targets() -> dict:
    """
    List available skill installation targets and client identifiers.

    Returns information about supported targets for skill installation,
    including codex, claude, opencode, amp, roo, and cursor.
    Also includes the client identifier mappings so agents know how to identify themselves.

    Returns:
        Dictionary with available targets, their descriptions, and client identifier mappings
    """
    targets = {
        "generic": {
            "description": "Generic output - no installation, just generates the skill folder",
            "scopes": ["project", "user"],
            "client_identifiers": ["generic"],
        },
        "codex": {
            "description": "OpenAI Codex CLI agent skills",
            "scopes": ["project", "user"],
            "project_path": ".codex/skills/",
            "user_path": "~/.codex/skills/",
            "client_identifiers": ["codex", "codex-cli", "openai-codex"],
        },
        "claude": {
            "description": "Anthropic Claude agent skills",
            "scopes": ["project", "user"],
            "project_path": ".claude/skills/",
            "user_path": "~/.claude/skills/",
            "client_identifiers": ["claude", "claude-code", "claude-desktop", "anthropic"],
        },
        "opencode": {
            "description": "OpenCode agent skills",
            "scopes": ["project", "user"],
            "project_path": ".opencode/skill/",
            "user_path": "~/.config/opencode/skill/",
            "client_identifiers": ["opencode", "open-code"],
        },
        "amp": {
            "description": "Sourcegraph Amp agent skills",
            "scopes": ["project", "user"],
            "project_path": ".agents/skills/",
            "user_path": "~/.config/agents/skills/",
            "client_identifiers": ["amp", "sourcegraph", "sourcegraph-amp"],
        },
        "roo": {
            "description": "Roo agent skills (supports custom modes)",
            "scopes": ["project", "user"],
            "project_path": ".roo/skills/",
            "user_path": "~/.roo/skills/",
            "client_identifiers": ["roo", "roo-code"],
        },
        "cursor": {
            "description": "Cursor IDE rules (project scope only)",
            "scopes": ["project"],
            "project_path": ".cursor/rules/",
            "client_identifiers": ["cursor", "cursor-ide"],
        },
    }

    return {
        "targets": targets,
        "default_target": "generic",
        "default_scope": "user",
        "usage_hint": "Pass your client identifier (e.g., 'claude', 'codex', 'cursor') to the 'client' parameter when calling generate_skill_from_url or generate_skill_from_text to automatically install to the correct location.",
    }


@mcp.tool()
def get_config() -> dict:
    """
    Get the current skillgen configuration.

    Returns the default configuration values used by skillgen,
    including fetch limits, LLM settings, and output options.

    Returns:
        Dictionary with current configuration values
    """
    cfg = default_config()
    return {
        "config": cfg,
        "description": {
            "snapshot": "Whether to fetch and include referenced documentation",
            "include_optional": "Whether to include optional sections",
            "max_pages": "Maximum number of pages to fetch",
            "max_page_chars": "Maximum characters per page",
            "max_total_bytes": "Maximum total bytes to fetch",
            "max_bytes_per_doc": "Maximum bytes per document",
            "keyword_mode": "Keyword generation mode (auto, heuristic, llm)",
            "llm_provider": "LLM provider for keyword generation",
            "llm_model": "LLM model name",
            "fetch_mode": "Fetch mode (full, metadata)",
            "by_section": "Whether to aggregate content by section",
        },
    }


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
