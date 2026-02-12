from skillgen.config import limits_for_level


def test_limits_for_level_profiles_are_distinct():
    compact = limits_for_level("compact")
    balanced = limits_for_level("balanced")
    verbose = limits_for_level("verbose")

    assert compact["max_pages"] < balanced["max_pages"] < verbose["max_pages"]
    assert compact["max_total_bytes"] < balanced["max_total_bytes"] < verbose["max_total_bytes"]
    assert compact["max_bytes_per_doc"] < balanced["max_bytes_per_doc"] < verbose["max_bytes_per_doc"]
    assert compact["max_page_chars"] < balanced["max_page_chars"] < verbose["max_page_chars"]


def test_limits_for_level_defaults_to_balanced_for_unknown_level():
    assert limits_for_level("unknown-level") == limits_for_level("balanced")
