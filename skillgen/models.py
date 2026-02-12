from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class DocLink:
    title: str
    url: str
    note: Optional[str] = None
    optional: bool = False
    section_title: Optional[str] = None


@dataclass
class Section:
    title: str
    slug: str
    optional: bool
    links: List[DocLink] = field(default_factory=list)


@dataclass
class ParsedLlms:
    title: str
    summary: Optional[str]
    preamble: Optional[str]
    sections: List[Section]
    source_url: Optional[str]
    raw_text: str


@dataclass
class FetchedDoc:
    source_url: str
    final_url: str
    content_type: Optional[str]
    status_code: int
    ok: bool
    error: Optional[str]
    bytes: int
    text: Optional[str]
    etag: Optional[str] = None
    last_modified: Optional[str] = None


@dataclass
class FetchResult:
    docs: Dict[str, FetchedDoc]
    warnings: List[str] = field(default_factory=list)


@dataclass
class GeneratorOptions:
    output_dir: str
    name_override: Optional[str]
    include_optional: bool
    snapshot: bool
    allow_external: bool
    max_bytes_per_doc: int
    max_total_bytes: int
    max_pages: int
    max_page_chars: int
    heuristic_level: str = "balanced"
    user_agent: str = "SkillGen/0.1"
    domain_allowlist: Optional[List[str]] = None
    install_for_claude: bool = False
    config_path: Optional[str] = None
