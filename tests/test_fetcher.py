from skillgen.fetcher import fetch_documents
from skillgen.models import DocLink


def test_fetch_documents_respects_total_byte_cap(monkeypatch):
    links = [
        DocLink(title="One", url="https://example.com/one"),
        DocLink(title="Two", url="https://example.com/two"),
        DocLink(title="Three", url="https://example.com/three"),
    ]

    monkeypatch.setattr("skillgen.fetcher.markdown_candidates", lambda url: [url])

    def fake_fetch_stream(session, url, max_bytes, user_agent):
        text = "x" * max_bytes
        return text, "text/markdown", "etag", "last-modified", 200, None, max_bytes, False

    monkeypatch.setattr("skillgen.fetcher._fetch_stream", fake_fetch_stream)

    result = fetch_documents(
        links=links,
        base_url="https://example.com/llms.txt",
        include_optional=True,
        allow_external=True,
        domain_allowlist=None,
        max_pages=10,
        max_bytes_per_doc=8,
        max_total_bytes=10,
        user_agent="SkillGen/0.1",
    )

    assert sum(d.bytes for d in result.docs.values()) <= 10
    assert len(result.docs) == 2
    assert any("max_total_bytes limit reached" in w for w in result.warnings)
