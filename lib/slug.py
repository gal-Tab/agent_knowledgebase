"""Slug generation utilities for LLM Wiki Agent.

Implements the slug rules defined in wiki-schema.md:
- All slugs are lowercase, hyphens only, no special characters.
- Different derivation rules per page type.
"""
import re
import unicodedata


MAX_SLUG_LENGTH = 80


def _normalize(text: str) -> str:
    """Normalize text to ASCII, lowercase, hyphens for separators."""
    # Normalize unicode to ASCII equivalents
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Replace common separators with hyphens
    text = re.sub(r"[\s_/]+", "-", text)
    # Remove everything except alphanumeric and hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Collapse multiple hyphens
    text = re.sub(r"-{2,}", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    # Truncate
    text = text[:MAX_SLUG_LENGTH].rstrip("-")
    return text


# Common filler words to strip from source titles for brevity
_STOPWORDS = {
    "a", "an", "the", "of", "for", "in", "on", "to", "and", "with",
    "from", "by", "at", "is", "are", "was", "were", "be", "been",
}


def slug_source(title: str) -> str:
    """Generate slug for a source page (paper, book, repo, doc).

    Papers/articles: abbreviated title, lowercase, hyphens.
    "Scaling Laws for Neural Language Models" → "scaling-laws-neural-lm"
    """
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")
    words = title.lower().split()
    # Remove stopwords but keep first word always
    filtered = [words[0]] + [w for w in words[1:] if w not in _STOPWORDS]
    # Abbreviate "language models" → "lm", "neural network" → "nn"
    result = "-".join(filtered)
    result = result.replace("language-models", "lm")
    result = result.replace("language-model", "lm")
    result = result.replace("neural-networks", "nn")
    result = result.replace("neural-network", "nn")
    return _normalize(result)


def slug_entity(name: str, entity_type: str = "person") -> str:
    """Generate slug for an entity page.

    Persons: lastname-firstname. "Jared Kaplan" → "kaplan-jared"
    Orgs: lowercase hyphenated. "OpenAI" → "openai"
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    if entity_type == "person":
        parts = name.strip().split()
        if len(parts) >= 2:
            # Last name first, then first name
            slug = f"{parts[-1]}-{parts[0]}"
        else:
            slug = parts[0]
        return _normalize(slug)
    else:
        # Orgs, products, tools, etc: just normalize
        return _normalize(name)


def slug_concept(name: str) -> str:
    """Generate slug for a concept page.

    "Scaling Laws" → "scaling-laws"
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    return _normalize(name)


def slug_comparison(a: str, b: str) -> str:
    """Generate slug for a comparison page.

    "GPT-4", "Claude" → "gpt4-vs-claude-comparison"
    """
    if not a or not a.strip() or not b or not b.strip():
        raise ValueError("Both comparison subjects must be non-empty")
    slug_a = _normalize(a)
    slug_b = _normalize(b)
    return f"{slug_a}-vs-{slug_b}-comparison"[:MAX_SLUG_LENGTH].rstrip("-")
