"""Tests for compound-learning format validation (lib/learning_format.py)."""
from lib.learning_format import (
    REQUIRED_FM,
    VALID_SCOPES,
    VALID_STATUS,
    VALID_TYPES,
    validate_learning,
)
from lib.page_format import ValidationResult

VALID_LEARNING = (
    "---\n"
    "id: kw-2026-06-08-retry-jitter\n"
    "type: correction\n"
    "scope: project\n"
    'headline: "Add jitter to retry backoff or thundering-herd recurs"\n'
    "tags: [retries, networking, reliability]\n"
    "confidence: STATED\n"
    "created: 2026-06-08\n"
    "updated: 2026-06-08\n"
    "status: active\n"
    "---\n"
    "\n"
    "## Learning\n"
    "Add jitter to exponential backoff.\n"
    "\n"
    "## Context\n"
    "Observed during a flaky deploy poller.\n"
    "\n"
    "## Implication\n"
    "Default new retry loops to full-jitter backoff.\n"
)


def _without_line(text: str, needle: str) -> str:
    """Return text with the first line containing needle removed."""
    return "\n".join(line for line in text.splitlines() if needle not in line) + "\n"


class TestValidLearning:
    def test_valid_learning_passes(self):
        result = validate_learning(VALID_LEARNING)
        assert isinstance(result, ValidationResult)
        assert result.ok, result.errors
        assert result.errors == []

    def test_scope_optional_defaults_ok(self):
        # scope is not in REQUIRED_FM; a learning without it still validates.
        text = _without_line(VALID_LEARNING, "scope:")
        result = validate_learning(text)
        assert result.ok, result.errors


class TestFrontmatter:
    def test_missing_frontmatter_fails(self):
        result = validate_learning("# Just a heading\n\nbody\n")
        assert not result.ok
        assert any("frontmatter" in e.lower() for e in result.errors)

    def test_each_required_field_is_enforced(self):
        for fieldname in REQUIRED_FM:
            text = _without_line(VALID_LEARNING, f"{fieldname}:")
            result = validate_learning(text)
            assert not result.ok, f"missing '{fieldname}' should fail"
            assert any(fieldname in e for e in result.errors), (
                f"error should name missing field '{fieldname}': {result.errors}"
            )


class TestEnums:
    def test_bad_type_fails(self):
        text = VALID_LEARNING.replace("type: correction", "type: rumor")
        result = validate_learning(text)
        assert not result.ok
        assert any("type" in e.lower() for e in result.errors)

    def test_all_valid_types_pass(self):
        for t in VALID_TYPES:
            text = VALID_LEARNING.replace("type: correction", f"type: {t}")
            assert validate_learning(text).ok, t

    def test_bad_confidence_fails(self):
        text = VALID_LEARNING.replace("confidence: STATED", "confidence: MAYBE")
        result = validate_learning(text)
        assert not result.ok
        assert any("confidence" in e.lower() for e in result.errors)

    def test_bad_scope_fails(self):
        text = VALID_LEARNING.replace("scope: project", "scope: galaxy")
        result = validate_learning(text)
        assert not result.ok
        assert any("scope" in e.lower() for e in result.errors)

    def test_all_valid_scopes_pass(self):
        for s in VALID_SCOPES:
            text = VALID_LEARNING.replace("scope: project", f"scope: {s}")
            assert validate_learning(text).ok, s

    def test_bad_status_fails(self):
        text = VALID_LEARNING.replace("status: active", "status: deleted")
        result = validate_learning(text)
        assert not result.ok
        assert any("status" in e.lower() for e in result.errors)

    def test_all_valid_statuses_pass(self):
        for s in VALID_STATUS:
            text = VALID_LEARNING.replace("status: active", f"status: {s}")
            assert validate_learning(text).ok, s


class TestHeadline:
    def test_headline_too_long_fails(self):
        long = "x" * 101
        text = VALID_LEARNING.replace(
            'headline: "Add jitter to retry backoff or thundering-herd recurs"',
            f'headline: "{long}"',
        )
        result = validate_learning(text)
        assert not result.ok
        assert any("headline" in e.lower() for e in result.errors)

    def test_headline_at_limit_passes(self):
        ok_len = "y" * 100
        text = VALID_LEARNING.replace(
            'headline: "Add jitter to retry backoff or thundering-herd recurs"',
            f'headline: "{ok_len}"',
        )
        assert validate_learning(text).ok


class TestDates:
    def test_bad_date_fails(self):
        text = VALID_LEARNING.replace("created: 2026-06-08", "created: June 8 2026")
        result = validate_learning(text)
        assert not result.ok
        assert any("date" in e.lower() or "created" in e.lower() for e in result.errors)


class TestSections:
    def test_missing_learning_section_fails(self):
        text = VALID_LEARNING.replace("## Learning", "## Lesson")
        result = validate_learning(text)
        assert not result.ok
        assert any("Learning" in e for e in result.errors)

    def test_missing_context_section_fails(self):
        text = VALID_LEARNING.replace("## Context", "## Background")
        result = validate_learning(text)
        assert not result.ok
        assert any("Context" in e for e in result.errors)

    def test_missing_implication_section_fails(self):
        text = VALID_LEARNING.replace("## Implication", "## Takeaway")
        result = validate_learning(text)
        assert not result.ok
        assert any("Implication" in e for e in result.errors)


class TestTags:
    def test_tags_not_a_list_fails(self):
        text = VALID_LEARNING.replace("tags: [retries, networking, reliability]", "tags: retries")
        result = validate_learning(text)
        assert not result.ok
        assert any("tags" in e.lower() for e in result.errors)

    def test_empty_tags_warns_not_blocks(self):
        text = VALID_LEARNING.replace("tags: [retries, networking, reliability]", "tags: []")
        result = validate_learning(text)
        assert result.ok, result.errors
        assert any("tags" in w.lower() for w in result.warnings)
