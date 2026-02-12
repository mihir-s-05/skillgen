from skillgen.keywords import generate_keywords


def test_heuristic_keywords_are_detailed_and_intent_aware():
    description, keywords = generate_keywords(
        title="Acme API Docs",
        summary="API platform for authentication, webhooks, and deployment workflows.",
        sections=["Authentication", "Webhooks", "Deployment Guide", "API Reference"],
        headings=["Token lifecycle", "Webhook retries", "Production rollout checklist"],
        heuristic_level="balanced",
    )

    assert "Primary coverage includes" in description
    assert "practical guidance for" in description
    assert "authentication" in keywords
    assert "webhooks" in keywords
    assert any("deployment" in term for term in keywords)
    assert "api reference" in keywords


def test_heuristic_levels_are_distinct():
    shared_kwargs = dict(
        title="Acme Platform Docs",
        summary="Operational guides for setup, auth, deployment, and troubleshooting.",
        sections=["Setup", "Authentication", "Deployment", "Troubleshooting", "API Reference"],
        headings=[
            "Getting started",
            "Token rotation",
            "Production rollouts",
            "Incident debugging",
            "Rate limits",
            "Webhook retries",
        ],
    )

    compact_desc, compact_keywords = generate_keywords(heuristic_level="compact", **shared_kwargs)
    balanced_desc, balanced_keywords = generate_keywords(heuristic_level="balanced", **shared_kwargs)
    verbose_desc, verbose_keywords = generate_keywords(heuristic_level="verbose", **shared_kwargs)

    assert "Covers:" in compact_desc
    assert "Primary coverage includes" in balanced_desc
    assert "Primary coverage includes" in verbose_desc
    assert "Useful navigation anchors include" in verbose_desc
    assert compact_keywords == balanced_keywords == verbose_keywords
