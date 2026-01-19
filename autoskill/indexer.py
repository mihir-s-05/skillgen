from typing import Dict, List


def render_index(sections: Dict[str, List[dict]]) -> str:
    lines = ["# References Index", ""]
    for section_title, pages in sections.items():
        lines.append(f"## {section_title}")
        if not pages:
            lines.append("- (no pages)")
        else:
            for p in pages:
                title = p.get("title") or p.get("id")
                path = p.get("local_path") or p.get("source_url")
                lines.append(f"- [{title}]({path})")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_section_index(section_title: str, pages: List[dict], synopsis: str | None = None) -> str:
    lines = [f"# {section_title}", ""]
    if synopsis:
        lines.append(synopsis)
        lines.append("")
    lines.append("## Pages")
    for p in pages:
        title = p.get("title") or p.get("id")
        path = p.get("local_path") or p.get("source_url")
        lines.append(f"- [{title}]({path})")
    lines.append("")
    return "\n".join(lines)
