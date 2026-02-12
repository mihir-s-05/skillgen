from typing import List, Optional, Tuple, Dict
from urllib.parse import urljoin, urlparse, urlunparse

import requests

from .models import DocLink, FetchResult, FetchedDoc


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    if base_url:
        url = urljoin(base_url, url)
    parsed = urlparse(url)
    parsed = parsed._replace(fragment="")
    return urlunparse(parsed)


def is_same_host(url: str, base_url: str) -> bool:
    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()


def markdown_candidates(url: str) -> List[str]:
    url = url.strip()
    lower = url.lower()
    if lower.endswith(".md"):
        return [url]
    candidates: List[str] = []
    candidates.append(url + ".md")

    parsed = urlparse(url)
    path = parsed.path or ""
    last = path.split("/")[-1]
    is_dir = path.endswith("/") or (last and "." not in last)
    if is_dir:
        base = url if url.endswith("/") else url + "/"
        candidates.extend([
            base + "index.html.md",
            base + "index-commonmark.md",
            base + "index.md",
        ])
    candidates.append(url)

    seen = set()
    ordered = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


def _fetch_stream(
    session: requests.Session,
    url: str,
    max_bytes: int,
    user_agent: str,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], int, Optional[str], int, bool]:
    headers = {"User-Agent": user_agent}
    try:
        r = session.get(url, headers=headers, timeout=20, stream=True, allow_redirects=True)
    except Exception as exc:
        return None, None, None, None, 0, f"request failed: {exc}", 0, False
    if len(r.history) > 5:
        return None, None, None, None, r.status_code, "too many redirects", 0, False
    content_type = r.headers.get("Content-Type")
    etag = r.headers.get("ETag")
    last_modified = r.headers.get("Last-Modified")
    if r.status_code >= 400:
        return None, content_type, None, last_modified, r.status_code, f"http {r.status_code}", 0, False
    chunks = []
    total = 0
    truncated = False
    for chunk in r.iter_content(chunk_size=65536):
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            truncated = True
            remaining = max_bytes - (total - len(chunk))
            if remaining > 0:
                chunks.append(chunk[:remaining])
            break
        chunks.append(chunk)
    data = b"".join(chunks)
    try:
        text = data.decode(r.encoding or "utf-8", errors="ignore")
    except Exception:
        text = data.decode("utf-8", errors="ignore")
    if truncated:
        text += "\n\n[TRUNCATED]\n"
    return text, content_type, etag, last_modified, r.status_code, None, len(data), truncated


def fetch_documents(
    links: List[DocLink],
    base_url: Optional[str],
    include_optional: bool,
    allow_external: bool,
    domain_allowlist: Optional[List[str]],
    max_pages: int,
    max_bytes_per_doc: int,
    max_total_bytes: int,
    user_agent: str,
) -> FetchResult:
    session = requests.Session()
    docs: Dict[str, FetchedDoc] = {}
    warnings: List[str] = []

    total_bytes = 0
    count = 0

    for link in links:
        if link.optional and not include_optional:
            continue
        if count >= max_pages:
            warnings.append("max_pages limit reached")
            break
        if total_bytes >= max_total_bytes:
            warnings.append("max_total_bytes limit reached")
            break
        normalized = normalize_url(link.url, base_url)
        parsed = urlparse(normalized)
        scheme = parsed.scheme.lower()
        host = parsed.netloc.lower()

        if scheme and scheme != "https":
            warnings.append(f"non-https link skipped: {normalized}")
            continue

        if not allow_external:
            if domain_allowlist:
                allowed = {d.lower() for d in domain_allowlist}
                if not host or host not in allowed:
                    warnings.append(f"external link skipped: {normalized}")
                    continue
            elif base_url:
                if not is_same_host(normalized, base_url):
                    warnings.append(f"external link skipped: {normalized}")
                    continue
            else:
                if host:
                    warnings.append(f"external link skipped: {normalized}")
                    continue
                warnings.append(f"relative link skipped (no base_url): {normalized}")
                continue

        if normalized in docs:
            continue

        final_doc = None
        for candidate in markdown_candidates(normalized):
            remaining_bytes = max_total_bytes - total_bytes
            if remaining_bytes <= 0:
                warnings.append("max_total_bytes limit reached")
                break
            request_cap = min(max_bytes_per_doc, remaining_bytes)
            text, content_type, etag, last_modified, status, err, fetched_bytes, _ = _fetch_stream(
                session,
                candidate,
                request_cap,
                user_agent,
            )
            if err:
                continue
            total_bytes += fetched_bytes
            final_doc = FetchedDoc(
                source_url=normalized,
                final_url=candidate,
                content_type=content_type,
                status_code=status,
                ok=True,
                error=None,
                bytes=fetched_bytes,
                text=text,
                etag=etag,
                last_modified=last_modified,
            )
            break

        if final_doc is None:
            final_doc = FetchedDoc(
                source_url=normalized,
                final_url=normalized,
                content_type=None,
                status_code=0,
                ok=False,
                error="fetch failed",
                bytes=0,
                text=None,
            )
        docs[normalized] = final_doc
        count += 1

    return FetchResult(docs=docs, warnings=warnings)


def fetch_text(url: str, user_agent: str) -> str:
    session = requests.Session()
    text, _, _, _, status, err, _, _ = _fetch_stream(session, url, 5_000_000, user_agent)
    if err or status >= 400 or text is None:
        raise RuntimeError(f"failed to fetch {url}: {err or status}")
    return text


def discover_llms_url(base_url: str, user_agent: str, allow_well_known: bool = True) -> str:
    if base_url.endswith("llms.txt"):
        return base_url
    candidates = [base_url.rstrip("/") + "/llms.txt"]
    if allow_well_known:
        candidates.append(base_url.rstrip("/") + "/.well-known/llms.txt")
    last_err = None
    for c in candidates:
        try:
            _ = fetch_text(c, user_agent)
            return c
        except Exception as e:
            last_err = e
    raise RuntimeError(f"no llms.txt found at {base_url}: {last_err}")
