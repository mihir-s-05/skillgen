import re
from typing import Optional, List

from .models import ParsedLlms, Section, DocLink
from .util import slugify


_h1_re = re.compile(r"^#\s+(.+?)\s*$")
_h2_re = re.compile(r"^##\s+(.+?)\s*$")
_link_re = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")


def parse_llms_text(text: str, source_url: Optional[str] = None) -> ParsedLlms:
    lines = text.splitlines()
    title = None
    summary_lines: List[str] = []
    preamble_lines: List[str] = []
    sections: List[Section] = []
    current_section: Optional[Section] = None
    seen_h2 = False

    i = 0
    while i < len(lines):
        line = lines[i]
        if title is None:
            m = _h1_re.match(line.strip())
            if m:
                title = m.group(1).strip()
                i += 1
                while i < len(lines):
                    s = lines[i].strip()
                    if s.startswith(">"):
                        summary_lines.append(s.lstrip(">").strip())
                        i += 1
                        continue
                    if s == "":
                        i += 1
                        continue
                    break
                continue
        m2 = _h2_re.match(line.strip())
        if m2:
            seen_h2 = True
            section_title = m2.group(1).strip()
            optional = section_title.strip().lower() == "optional"
            current_section = Section(
                title=section_title,
                slug=slugify(section_title, max_len=60),
                optional=optional,
                links=[],
            )
            sections.append(current_section)
            i += 1
            continue

        if not seen_h2:
            if title is not None:
                if line.strip() != "":
                    preamble_lines.append(line)
        else:
            if current_section:
                link_match = _link_re.search(line)
                if link_match:
                    link_title = link_match.group(1).strip()
                    link_url = link_match.group(2).strip()
                    note = None
                    after = line[link_match.end():].strip()
                    if after.startswith(":"):
                        note = after[1:].strip()
                    elif after:
                        note = after
                    current_section.links.append(
                        DocLink(
                            title=link_title,
                            url=link_url,
                            note=note,
                            optional=current_section.optional,
                            section_title=current_section.title,
                        )
                    )
        i += 1

    if title is None:
        title = "Untitled"

    summary = "\n".join(summary_lines).strip() if summary_lines else None
    preamble = "\n".join(preamble_lines).strip() if preamble_lines else None

    return ParsedLlms(
        title=title,
        summary=summary,
        preamble=preamble,
        sections=sections,
        source_url=source_url,
        raw_text=text,
    )
