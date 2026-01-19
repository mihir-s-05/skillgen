import json
import re
from collections import Counter
from functools import lru_cache
from typing import List, Dict, Optional, Tuple


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in",
    "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will",
    "with", "this", "these", "those", "you", "your", "we", "our", "their", "they",
}

_COMMON_INTENTS = [
    "authentication", "auth", "login", "api key", "rate limit", "pagination",
    "errors", "webhooks", "sdk", "cli", "quickstart", "getting started",
    "examples", "reference", "guides", "tutorial", "billing", "pricing",
]


def _tokenize(text: str) -> List[str]:
    tokens = re.split(r"[^a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if t and t not in _STOPWORDS and len(t) > 2]


def heuristic_keywords(texts: List[str], max_terms: int = 60) -> List[str]:
    counter: Counter[str] = Counter()
    for t in texts:
        counter.update(_tokenize(t))
    terms = [w for w, _ in counter.most_common(max_terms)]
    for intent in _COMMON_INTENTS:
        if intent not in terms:
            terms.append(intent)
    return terms[:max_terms]


def heuristic_description(title: str, summary: Optional[str], sections: List[str]) -> str:
    lines = []
    if summary:
        lines.append(summary)
    else:
        lines.append(f"Documentation skill for {title}.")
    if sections:
        lines.append("Covers: " + ", ".join(sections[:8]) + ".")
    return "\n\n".join(lines)


def _extract_json(text: str) -> Optional[Dict[str, object]]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


@lru_cache(maxsize=2)
def _load_transformers(model_name: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    return model, tokenizer


def _transformers_generate(
    title: str,
    summary: Optional[str],
    sections: List[str],
    headings: List[str],
    model_name: str,
    device: str,
    max_new_tokens: int,
    temperature: float,
) -> Optional[Dict[str, object]]:
    try:
        import torch
    except Exception:
        return None

    prompt_payload = {
        "title": title,
        "summary": summary or "",
        "sections": sections,
        "headings": headings[:200],
    }
    system = (
        "You are generating a skill description and trigger keywords. "
        "Only use the provided data. Output JSON with keys: description (string), keywords (array of strings)."
    )
    prompt = system + "\n\n" + json.dumps(prompt_payload)

    try:
        model, tokenizer = _load_transformers(model_name)
    except Exception:
        return None

    use_cuda = device == "cuda" or (device == "auto" and torch.cuda.is_available())
    if use_cuda:
        model = model.to("cuda")

    inputs = tokenizer(prompt, return_tensors="pt")
    if use_cuda:
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

    output = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=temperature > 0,
        temperature=temperature,
    )
    text = tokenizer.decode(output[0], skip_special_tokens=True)
    parsed = _extract_json(text)
    if parsed and "description" in parsed and "keywords" in parsed:
        return parsed
    return None


def generate_keywords(
    title: str,
    summary: Optional[str],
    sections: List[str],
    headings: List[str],
    mode: str,
    llm_provider: str,
    llm_model: Optional[str],
    llm_device: str,
    llm_max_new_tokens: int,
    llm_temperature: float,
    llm_fallback: bool,
) -> Tuple[str, List[str]]:
    if mode in ("llm", "auto") and llm_provider == "transformers" and llm_model:
        result = _transformers_generate(
            title,
            summary,
            sections,
            headings,
            llm_model,
            llm_device,
            llm_max_new_tokens,
            llm_temperature,
        )
        if result:
            return result["description"], result["keywords"]
        if mode == "llm" and not llm_fallback:
            raise RuntimeError("LLM keyword generation failed")

    description = heuristic_description(title, summary, sections)
    keywords = heuristic_keywords([title, summary or ""] + sections + headings)
    return description, keywords
