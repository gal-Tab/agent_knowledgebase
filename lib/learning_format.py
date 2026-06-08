"""Format validation for compound learnings (the kw-* subsystem).

A *learning* is the agent's own work-lesson — distinct from the source-document
wiki pages validated by lib/page_format.py. Learnings live in the project store
`.compound/<type>/<slug>.md` and (opt-in) the global store
`~/.claude/compound-knowledge/<type>/<slug>.md`.

This module is the canonical enforcement of templates/learning-schema.md. The
pre-write gate in lib/learning_store.py uses `validate_learning` so malformed
learnings never reach disk — the same discipline page_writer.py applies to wiki
pages.
"""
from __future__ import annotations

import re

from lib.page_format import VALID_CONFIDENCE, ValidationResult, parse_frontmatter

VALID_TYPES = {"insight", "playbook", "correction", "pattern"}
VALID_SCOPES = {"project", "global"}
VALID_STATUS = {"active", "archived", "superseded"}

# Frontmatter fields that must be present. `scope` is intentionally absent: it
# defaults to "project" and is only set explicitly when a learning is promoted
# to the global store.
REQUIRED_FM = ["id", "type", "headline", "tags", "confidence", "created", "updated", "status"]

# Body sections every learning must carry.
REQUIRED_SECTIONS = ["## Learning", "## Context", "## Implication"]

HEADLINE_MAX = 100

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_learning(content: str) -> ValidationResult:
    """Validate a learning file against learning-schema.md rules.

    Returns a ValidationResult. `errors` block writes; `warnings` are advisory.
    `ok` is True iff there are no errors.
    """
    errors: list[str] = []
    warnings: list[str] = []

    fm = parse_frontmatter(content)
    if not fm:
        errors.append("Missing or invalid frontmatter (must start with --- and contain valid YAML)")
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    for required_field in REQUIRED_FM:
        if required_field not in fm or fm[required_field] in (None, ""):
            errors.append(f"Missing required field: '{required_field}'")

    learning_type = fm.get("type")
    if learning_type is not None and learning_type not in VALID_TYPES:
        errors.append(
            f"Invalid type '{learning_type}', must be one of {sorted(VALID_TYPES)}"
        )

    confidence = fm.get("confidence")
    if confidence is not None and confidence not in VALID_CONFIDENCE:
        errors.append(
            f"Invalid confidence '{confidence}', must be one of {sorted(VALID_CONFIDENCE)}"
        )

    status = fm.get("status")
    if status is not None and status not in VALID_STATUS:
        errors.append(
            f"Invalid status '{status}', must be one of {sorted(VALID_STATUS)}"
        )

    # scope is optional (defaults to project) but validated when present.
    scope = fm.get("scope")
    if scope is not None and scope not in VALID_SCOPES:
        errors.append(
            f"Invalid scope '{scope}', must be one of {sorted(VALID_SCOPES)}"
        )

    headline = fm.get("headline")
    if isinstance(headline, str) and len(headline) > HEADLINE_MAX:
        errors.append(
            f"headline too long ({len(headline)} chars), max {HEADLINE_MAX}"
        )

    for date_field in ("created", "updated"):
        value = fm.get(date_field)
        if value and not _DATE_RE.match(str(value)):
            errors.append(
                f"Invalid date format for '{date_field}': '{value}' (expected YYYY-MM-DD)"
            )

    tags = fm.get("tags")
    if "tags" in fm and not isinstance(tags, list):
        errors.append(f"tags must be a list, got {type(tags).__name__}")
    elif isinstance(tags, list) and len(tags) == 0:
        warnings.append("tags is empty — this learning will be hard to surface during retrieval")

    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing required section: '{section}'")

    return ValidationResult(ok=len(errors) == 0, errors=errors, warnings=warnings)
