import re
from collections import Counter
from typing import List, Dict, Optional, Tuple


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in",
    "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will",
    "with", "this", "these", "those", "you", "your", "we", "our", "their", "they", "via",
}

_GENERIC_INTENTS = [
    "authentication", "auth", "login", "api key", "rate limit", "pagination",
    "errors", "webhooks", "sdk", "cli", "quickstart", "getting started",
    "examples", "reference", "guides", "tutorial", "billing", "pricing",
]

_INTENT_HINTS = {
    "authentication": {"auth", "oauth", "token", "jwt", "sso", "identity", "credential", "login"},
    "api key": {"api key", "apikey", "key management", "secret"},
    "rate limit": {"rate limit", "throttle", "quota"},
    "pagination": {"pagination", "page size", "cursor", "offset"},
    "errors": {"error", "exception", "status code", "retry"},
    "webhooks": {"webhook", "event delivery", "event", "callback"},
    "sdk": {"sdk", "library", "client", "python", "typescript", "java"},
    "cli": {"cli", "command line", "terminal", "shell"},
    "quickstart": {"quickstart", "quick start", "getting started", "setup"},
    "examples": {"example", "sample", "cookbook"},
    "reference": {"reference", "api reference", "specification"},
    "guides": {"guide", "how to", "walkthrough"},
    "tutorial": {"tutorial", "step by step"},
    "billing": {"billing", "invoice", "usage cost"},
    "pricing": {"pricing", "price", "plan"},
    "deployment": {"deploy", "deployment", "production", "hosting"},
    "configuration": {"config", "configuration", "settings", "options"},
    "monitoring": {"monitor", "observability", "metrics", "tracing", "logging"},
    "troubleshooting": {"troubleshoot", "debug", "known issues", "faq"},
}


def _heuristic_profile(level: str) -> Dict[str, object]:
    normalized = (level or "balanced").strip().lower()
    if normalized == "compact":
        return {
            "max_terms": 60,
            "heading_input": 80,
            "seed_sections": 8,
            "seed_headings": 16,
            "theme_cap": 2,
            "intent_cap": 2,
            "section_preview": 4,
            "include_themes": False,
            "include_detected_intents": True,
            "generic_intent_limit": 8,
        }
    if normalized == "verbose":
        return {
            "max_terms": 60,
            "heading_input": 300,
            "seed_sections": 24,
            "seed_headings": 72,
            "theme_cap": 8,
            "intent_cap": 8,
            "section_preview": 12,
            "include_themes": True,
            "include_detected_intents": True,
            "generic_intent_limit": 8,
        }
    return {
        "max_terms": 60,
        "heading_input": 180,
        "seed_sections": 16,
        "seed_headings": 36,
        "theme_cap": 4,
        "intent_cap": 5,
        "section_preview": 8,
        "include_themes": True,
        "include_detected_intents": True,
        "generic_intent_limit": 8,
    }


def _tokenize(text: str) -> List[str]:
    tokens = re.split(r"[^a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if t and t not in _STOPWORDS and len(t) > 2]


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_term(text: str) -> str:
    cleaned = _normalize_space(text.lower())
    cleaned = cleaned.strip(".,:;!?()[]{}<>\"'")
    return cleaned


def _phrase_ngrams(tokens: List[str], min_n: int = 2, max_n: int = 3) -> List[str]:
    phrases: List[str] = []
    for n in range(min_n, max_n + 1):
        if len(tokens) < n:
            continue
        for i in range(0, len(tokens) - n + 1):
            phrase = " ".join(tokens[i : i + n])
            if len(phrase) >= 6:
                phrases.append(phrase)
    return phrases


def _add_weight(counter: Counter[str], term: str, weight: int) -> None:
    normalized = _normalize_term(term)
    if not normalized:
        return
    if normalized in _STOPWORDS:
        return
    words = normalized.split()
    if len(words) > 8:
        return
    if len(normalized) > 80:
        return
    counter[normalized] += weight


def _collect_weighted_terms(
    title: str,
    summary: Optional[str],
    sections: List[str],
    headings: List[str],
) -> Counter[str]:
    counter: Counter[str] = Counter()

    _add_weight(counter, title, 14)
    title_tokens = _tokenize(title)
    for token in title_tokens:
        _add_weight(counter, token, 5)
    for phrase in _phrase_ngrams(title_tokens):
        _add_weight(counter, phrase, 6)

    if summary:
        _add_weight(counter, summary, 9)
        summary_tokens = _tokenize(summary)
        for token in summary_tokens:
            _add_weight(counter, token, 3)

    for section in sections:
        _add_weight(counter, section, 11)
        section_tokens = _tokenize(section)
        for token in section_tokens:
            _add_weight(counter, token, 4)
        for phrase in _phrase_ngrams(section_tokens):
            _add_weight(counter, phrase, 5)

    for heading in headings[:250]:
        _add_weight(counter, heading, 7)
        heading_tokens = _tokenize(heading)
        for token in heading_tokens:
            _add_weight(counter, token, 2)
        for phrase in _phrase_ngrams(heading_tokens):
            _add_weight(counter, phrase, 3)

    return counter


def _ranked_terms(counter: Counter[str], max_terms: int) -> List[str]:
    ranked = sorted(counter.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [term for term, _ in ranked[:max_terms]]


def _detect_intents(summary: Optional[str], sections: List[str], headings: List[str]) -> List[str]:
    corpus = " ".join([summary or "", *sections, *headings]).lower()
    intents = []
    for intent, hints in _INTENT_HINTS.items():
        if any(hint in corpus for hint in hints):
            intents.append(intent)
    return intents


def _dedupe_terms(terms: List[str]) -> List[str]:
    ordered: List[str] = []
    for term in terms:
        cleaned = _normalize_term(term)
        if not cleaned:
            continue
        if cleaned.isdigit():
            continue

        skip = False
        cleaned_is_phrase = " " in cleaned
        for existing in ordered:
            existing_is_phrase = " " in existing
            if cleaned == existing:
                skip = True
                break
            if len(cleaned) >= 6 and cleaned in existing:
                skip = True
                break
            if cleaned_is_phrase and existing_is_phrase and len(existing) >= 6 and existing in cleaned:
                skip = True
                break
        if skip:
            continue
        ordered.append(cleaned)
    return ordered


def heuristic_keywords(
    title: str,
    summary: Optional[str],
    sections: List[str],
    headings: List[str],
    level: str = "balanced",
) -> List[str]:
    profile = _heuristic_profile(level)
    max_terms = int(profile["max_terms"])
    heading_input = int(profile["heading_input"])

    counter = _collect_weighted_terms(title, summary, sections, headings[:heading_input])

    seeded: List[str] = []
    seeded.extend(sections[: int(profile["seed_sections"])])
    seeded.extend(headings[: int(profile["seed_headings"])])
    ranked = _ranked_terms(counter, max_terms * 2)
    intents = _detect_intents(summary, sections, headings[:heading_input])[: int(profile["intent_cap"])]

    terms = _dedupe_terms(seeded + ranked)
    if profile["include_detected_intents"]:
        terms = _dedupe_terms(terms + intents)
    generic_limit = int(profile["generic_intent_limit"])
    if generic_limit > 0:
        for intent in _GENERIC_INTENTS[:generic_limit]:
            if len(terms) >= max_terms:
                break
            if _normalize_term(intent) not in terms:
                terms.append(_normalize_term(intent))
    return terms[:max_terms]


def _human_join(items: List[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def heuristic_description(
    title: str,
    summary: Optional[str],
    sections: List[str],
    headings: List[str],
    level: str = "balanced",
) -> str:
    profile = _heuristic_profile(level)
    if summary:
        lead = _normalize_space(summary)
    else:
        lead = f"Documentation skill for {title}."
    paragraphs = [lead]

    if sections:
        section_preview = [_normalize_space(s) for s in sections[: int(profile["section_preview"])]]
        if level == "compact":
            paragraphs.append("Covers: " + ", ".join(section_preview) + ".")
        else:
            paragraphs.append(f"Primary coverage includes {_human_join(section_preview)}.")

    if not profile["include_themes"]:
        return "\n\n".join(paragraphs)

    counter = _collect_weighted_terms(title, summary, sections, headings[: int(profile["heading_input"])])
    section_terms = {_normalize_term(s) for s in sections}
    title_tokens = set(_tokenize(title))

    themes: List[str] = []
    for term in _ranked_terms(counter, 50):
        if term in section_terms:
            continue
        if term in title_tokens:
            continue
        if " " not in term and len(term) < 8:
            continue
        themes.append(term)
        if len(themes) >= int(profile["theme_cap"]):
            break
    themes = _dedupe_terms(themes)

    intents = [
        intent for intent in _detect_intents(summary, sections, [])
        if _normalize_term(intent) not in section_terms
    ][: int(profile["intent_cap"])]

    if themes and intents:
        paragraphs.append(
            "The references emphasize "
            + _human_join(themes[:4])
            + ", with practical guidance for "
            + _human_join(intents[:5])
            + "."
        )
    elif themes:
        paragraphs.append("The references emphasize " + _human_join(themes[:5]) + ".")
    elif intents:
        paragraphs.append("Common question patterns include " + _human_join(intents[:5]) + ".")

    if level == "verbose":
        anchors = _dedupe_terms(sections[:6] + headings[:8])[:6]
        if anchors:
            paragraphs.append("Useful navigation anchors include " + _human_join(anchors) + ".")

    return "\n\n".join(paragraphs)


def generate_keywords(
    title: str,
    summary: Optional[str],
    sections: List[str],
    headings: List[str],
    heuristic_level: str,
) -> Tuple[str, List[str]]:
    description = heuristic_description(title, summary, sections, headings, level=heuristic_level)
    keywords = heuristic_keywords(title, summary, sections, headings, level="balanced")
    return description, keywords
