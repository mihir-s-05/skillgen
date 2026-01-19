"""
MCP Server for SkillGen - Install skills from llms.txt URLs.

This server exposes a single tool that allows LLMs to install skills
from any llms.txt URL with minimal friction.
"""

import os
import tempfile
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .fetcher import discover_llms_url, fetch_text, fetch_documents
from .parser import parse_llms_text
from .generator import generate_skill
from .installer import install_skill
from .models import GeneratorOptions

# Create the MCP server
mcp = FastMCP(
    "skillgen",
    description="Generate and install Agent Skills from llms.txt files. "
    "Provide a URL to an llms.txt file and this tool will fetch the documentation, "
    "generate a skill bundle, and install it for immediate use.",
)


@mcp.tool()
def install_skill_from_url(
    url: str,
    name: str | None = None,
    include_optional: bool = False,
    snapshot: bool = True,
) -> dict[str, Any]:
    """
    Install a skill from an llms.txt URL.

    This tool fetches documentation from the given URL, generates a skill bundle,
    and installs it to Claude Code for immediate use.

    Args:
        url: URL to an llms.txt file or a documentation site (will auto-discover llms.txt)
        name: Optional override for the skill name (defaults to name from llms.txt)
        include_optional: Whether to include optional documentation sections
        snapshot: Whether to download and cache the referenced documentation (recommended)

    Returns:
        Information about the installed skill including its location and how to use it
    """
    cfg = load_config(None)

    # Discover and fetch the llms.txt
    llms_url = discover_llms_url(url, cfg["user_agent"])
    text = fetch_text(llms_url, cfg["user_agent"])

    # Parse the llms.txt
    parsed = parse_llms_text(text, source_url=llms_url)

    # Create a temp directory for generation
    with tempfile.TemporaryDirectory() as tmpdir:
        options = GeneratorOptions(
            output_dir=tmpdir,
            name_override=name,
            include_optional=include_optional,
            snapshot=snapshot,
            allow_external=cfg.get("allow_external", False),
            fetch_mode="full" if snapshot else "metadata",
            max_bytes_per_doc=cfg["max_bytes_per_doc"],
            max_total_bytes=cfg["max_total_bytes"],
            max_pages=cfg["max_pages"],
            max_page_chars=cfg["max_page_chars"],
            by_section=True,
            keyword_mode="heuristic",  # Use heuristic for speed in MCP context
            llm_provider="none",
            llm_model=None,
            llm_device="cpu",
            llm_fallback=True,
            user_agent=cfg["user_agent"],
            domain_allowlist=cfg.get("domain_allowlist"),
            target="claude",
            scope="user",
            overwrite=True,
        )

        # Fetch documents if snapshotting
        fetch_result = None
        if snapshot:
            fetch_result = fetch_documents(
                links=[link for section in parsed.sections for link in section.links],
                base_url=llms_url,
                include_optional=include_optional,
                allow_external=cfg.get("allow_external", False),
                domain_allowlist=cfg.get("domain_allowlist"),
                max_pages=cfg["max_pages"],
                max_bytes_per_doc=cfg["max_bytes_per_doc"],
                max_total_bytes=cfg["max_total_bytes"],
                user_agent=cfg["user_agent"],
            )

        # Generate the skill
        output_path = generate_skill(parsed, options, fetch_result)
        skill_name = os.path.basename(output_path)

        # Install to Claude Code
        install_path = install_skill(
            output_path,
            skill_name,
            target="claude",
            scope="user",
            target_dir=None,
            overwrite=True,
            roo_mode=None,
            cwd=os.getcwd(),
        )

    # Read the SKILL.md to get the description
    skill_md_path = os.path.join(install_path, "SKILL.md")
    skill_content = ""
    if os.path.exists(skill_md_path):
        with open(skill_md_path, "r", encoding="utf-8") as f:
            skill_content = f.read()

    # Count sections and links
    section_count = len(parsed.sections)
    link_count = sum(len(s.links) for s in parsed.sections)

    return {
        "success": True,
        "skill_name": skill_name,
        "install_path": install_path,
        "source_url": llms_url,
        "title": parsed.title,
        "summary": parsed.summary,
        "sections": section_count,
        "documentation_pages": link_count,
        "message": f"Successfully installed skill '{skill_name}' from {llms_url}. "
        f"The skill contains {link_count} documentation pages across {section_count} sections. "
        f"You can now use this skill by referencing documentation in {install_path}.",
        "skill_content_preview": skill_content[:2000] if skill_content else None,
    }


@mcp.tool()
def list_installed_skills() -> dict[str, Any]:
    """
    List all skills currently installed in Claude Code.

    Returns:
        List of installed skills with their paths and metadata
    """
    skills_dir = os.path.expanduser("~/.claude/skills")

    if not os.path.exists(skills_dir):
        return {
            "success": True,
            "skills": [],
            "message": "No skills directory found. Install a skill first using install_skill_from_url.",
        }

    skills = []
    for entry in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, entry)
        if os.path.isdir(skill_path):
            manifest_path = os.path.join(skill_path, "manifest.json")
            skill_md_path = os.path.join(skill_path, "SKILL.md")

            skill_info = {
                "name": entry,
                "path": skill_path,
            }

            # Try to read manifest
            if os.path.exists(manifest_path):
                import json
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                        skill_info["source_url"] = manifest.get("source_url")
                        skill_info["generated_at"] = manifest.get("generated_at")
                except Exception:
                    pass

            # Check for SKILL.md
            skill_info["has_skill_md"] = os.path.exists(skill_md_path)

            skills.append(skill_info)

    return {
        "success": True,
        "skills": skills,
        "count": len(skills),
        "skills_directory": skills_dir,
    }


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
