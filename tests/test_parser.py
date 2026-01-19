from skillgen.parser import parse_llms_text


def test_parse_llms_text():
    text = (
        "# Sample Docs\n"
        "> Summary line.\n"
        "\n"
        "## Guides\n"
        "- [Intro](https://example.com/intro)\n"
        "\n"
        "## Optional\n"
        "- [Extra](https://example.com/extra)\n"
    )
    parsed = parse_llms_text(text, source_url="https://example.com/llms.txt")
    assert parsed.title == "Sample Docs"
    assert parsed.summary == "Summary line."
    assert len(parsed.sections) == 2
    assert parsed.sections[0].title == "Guides"
    assert parsed.sections[1].optional is True
    assert parsed.sections[0].links[0].url == "https://example.com/intro"
