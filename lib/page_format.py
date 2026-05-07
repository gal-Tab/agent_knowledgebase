"""Page format validation for LLM Wiki Agent.

Validates wiki page frontmatter and structure against wiki-schema.md rules.

The validators here are the canonical enforcement of templates/wiki-schema.md.
Any rule documented in the schema must be enforced here, not just described in
the resolver prompt. Pages that fail validation must not reach disk — see
lib/page_writer.py for the pre-write gate that uses these validators.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from lib.slug import _normalize

VALID_TYPES = {"source", "entity", "concept", "comparison"}
VALID_CONFIDENCE = {"STATED", "INFERRED", "UNCERTAIN"}

# Required frontmatter fields per page type.
REQUIRED_FIELDS = {
    "source": {"title", "type", "source_refs", "created", "updated"},
    "entity": {"title", "type", "source_refs", "created", "updated"},
    "concept": {"title", "type", "source_refs", "created", "updated"},
    "comparison": {"title", "type", "source_refs", "created", "updated"},
}

# Optional but expected fields per type (currently informational only).
EXPECTED_FIELDS = {
    "source": {"source_file", "source_type", "key_entities", "key_concepts", "tags"},
    "entity": {"aliases", "tags"},
    "concept": {"aliases", "domain_tags", "tags"},
    "comparison": {"compared_entities", "tags"},
}


@dataclass
class ValidationResult:
    """Outcome of validating a wiki page.

    `errors` block writes; `warnings` are advisory and do not block.
    `ok` is True iff `errors` is empty.
    """

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a markdown file.

    Expects content starting with '---' and ending with a closing '---'.
    Returns dict of frontmatter fields. Returns empty dict if no frontmatter
    or if the YAML is malformed.
    """
    if not content.startswith("---"):
        return {}

    end = content.find("\n---", 3)
    if end == -1:
        return {}

    fm_text = content[3:end].strip()
    try:
        parsed = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return {}

    if not isinstance(parsed, dict):
        return {}
    return parsed


def validate_source_refs_format(frontmatter: dict) -> list[str]:
    """Each source_refs entry must be a {slug, confidence} object.

    The string form (e.g. `- "paper-x"`) is rejected — that was the failure
    mode that motivated commit 2bb1b6f.
    """
    errors: list[str] = []
    refs = frontmatter.get("source_refs")
    if refs is None:
        # Missing field is REQUIRED_FIELDS' problem, not ours.
        return errors
    if not isinstance(refs, list):
        errors.append("source_refs must be a list")
        return errors

    for i, entry in enumerate(refs):
        if isinstance(entry, str):
            errors.append(
                f"source_refs[{i}]: entries must be objects with slug+confidence, "
                f"got plain string '{entry}'"
            )
            continue
        if not isinstance(entry, dict):
            errors.append(f"source_refs[{i}]: entry must be an object, got {type(entry).__name__}")
            continue
        if "slug" not in entry:
            errors.append(f"source_refs[{i}]: missing 'slug' field")
        if "confidence" not in entry:
            errors.append(f"source_refs[{i}]: missing 'confidence' field")
        elif entry["confidence"] not in VALID_CONFIDENCE:
            errors.append(
                f"source_refs[{i}]: invalid confidence '{entry['confidence']}', "
                f"must be one of {sorted(VALID_CONFIDENCE)}"
            )
    return errors


# Match markdown links of the form [text](target). Excludes images ![...](...).
_LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")
# Match wiki-style links [[slug]] anywhere in the body.
_WIKILINK_RE = re.compile(r"\[\[[^\]]+\]\]")
# Match valid relative links to wiki pages.
_RELATIVE_PAGE_RE = re.compile(r"^\.\./[a-z0-9-]+/[a-z0-9-]+\.md$")


def validate_link_format(body: str) -> list[str]:
    """Internal markdown links must be relative `../{category}/{slug}.md`.

    External http(s) links are ignored. Wiki-style `[[slug]]` is rejected.
    Absolute paths and missing `.md` extensions are rejected.
    """
    errors: list[str] = []

    for match in _WIKILINK_RE.finditer(body):
        errors.append(f"wiki-link not allowed: '{match.group(0)}' (use [text](../category/slug.md))")

    for text, target in _LINK_RE.findall(body):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if target.startswith("/"):
            errors.append(f"absolute path not allowed in link '[{text}]({target})' (use relative ../)")
            continue
        if not target.endswith(".md"):
            errors.append(f"internal link must end in .md: '[{text}]({target})'")
            continue
        if not _RELATIVE_PAGE_RE.match(target):
            errors.append(
                f"link '[{text}]({target})' must match relative form ../category/slug.md"
            )

    return errors


def validate_confidence_labels(body: str) -> list[str]:
    """Every list item under `## See Also` must end with a [CONFIDENCE] label.

    Lines outside the See Also section are ignored. A page without a See Also
    section passes this validator (a different validator catches that).
    """
    errors: list[str] = []
    in_see_also = False
    label_re = re.compile(r"\[(STATED|INFERRED|UNCERTAIN)\]\s*$")
    bracket_re = re.compile(r"\[([A-Z]+)\]\s*$")

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_see_also = stripped.lower().startswith("## see also")
            continue
        if not in_see_also:
            continue
        if not stripped or not stripped.startswith("- "):
            continue

        if label_re.search(stripped):
            continue
        bad = bracket_re.search(stripped)
        if bad:
            errors.append(
                f"See Also line has invalid confidence label '[{bad.group(1)}]', "
                f"must be one of {sorted(VALID_CONFIDENCE)}: {stripped!r}"
            )
        else:
            errors.append(
                f"See Also line missing [CONFIDENCE] label "
                f"(STATED|INFERRED|UNCERTAIN): {stripped!r}"
            )
    return errors


def validate_slug_format(frontmatter: dict, file_path: str | os.PathLike) -> list[str]:
    """File basename (sans .md) must satisfy the slug rules.

    Lowercase, hyphens only, no underscores or special chars. We also require
    a `.md` extension. We do NOT enforce title↔basename equality — slug
    derivation rules differ per page type (entities use lastname-firstname,
    concepts use the literal name) and cannot be re-derived from frontmatter
    alone.
    """
    errors: list[str] = []
    if not frontmatter.get("title"):
        return errors

    name = Path(str(file_path)).name
    if not name.endswith(".md"):
        errors.append(f"page filename must end in .md: '{name}'")
        return errors

    stem = name[:-3]
    if not stem:
        errors.append("page filename has empty stem")
        return errors

    if "_" in stem:
        errors.append(f"slug '{stem}' contains underscore — use hyphens only")
    if stem != stem.lower():
        errors.append(f"slug '{stem}' must be lowercase")
    normalized = _normalize(stem)
    if normalized != stem:
        errors.append(
            f"slug '{stem}' contains characters disallowed by slug rules "
            f"(normalized form would be '{normalized}')"
        )

    return errors


def validate_page(content: str, page_type: str) -> ValidationResult:
    """Validate a wiki page against schema rules.

    Returns a ValidationResult. `ok` is True iff there are no errors.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if page_type not in VALID_TYPES:
        errors.append(f"Invalid page type: '{page_type}'. Must be one of: {sorted(VALID_TYPES)}")
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    fm = parse_frontmatter(content)
    if not fm:
        errors.append("Missing or invalid frontmatter (must start with --- and contain valid YAML)")
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    for required_field in REQUIRED_FIELDS[page_type]:
        if required_field not in fm:
            errors.append(f"Missing required field: '{required_field}'")

    if "type" in fm and fm["type"] != page_type:
        errors.append(f"Type mismatch: frontmatter says '{fm['type']}' but expected '{page_type}'")

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for date_field in ("created", "updated"):
        value = fm.get(date_field)
        if value and not date_pattern.match(str(value)):
            errors.append(
                f"Invalid date format for '{date_field}': '{value}' (expected YYYY-MM-DD)"
            )

    if "## See Also" not in content:
        errors.append("Missing '## See Also' section (required by wiki-schema.md)")

    errors.extend(validate_source_refs_format(fm))
    errors.extend(validate_link_format(content))
    errors.extend(validate_confidence_labels(content))

    return ValidationResult(ok=len(errors) == 0, errors=errors, warnings=warnings)


def extract_links(content: str) -> list[tuple[str, str]]:
    """Extract markdown links from content.

    Returns list of (display_text, path) tuples for links whose target ends in
    `.md`. Used by Step 7 link validation.
    """
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
    return pattern.findall(content)
