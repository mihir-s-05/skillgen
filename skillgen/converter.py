from typing import Optional

import trafilatura


def html_to_markdown(html: str, url: Optional[str] = None) -> str:
    md = trafilatura.extract(
        html,
        output_format="markdown",
        url=url,
        include_links=True,
        include_tables=True,
        favor_recall=True,
    )
    if md:
        return md
    return html


def convert_to_markdown(text: str, content_type: Optional[str], url: Optional[str] = None) -> str:
    if not content_type:
        return text
    ct = content_type.lower()
    if "text/markdown" in ct or "text/plain" in ct:
        return text
    if "text/html" in ct or "application/xhtml" in ct:
        return html_to_markdown(text, url=url)
    return text
