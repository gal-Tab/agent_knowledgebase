"""Tests for page format validation (lib/page_format.py)."""
import pytest

from lib.page_format import (
    ValidationResult,
    extract_links,
    parse_frontmatter,
    validate_confidence_labels,
    validate_link_format,
    validate_page,
    validate_slug_format,
    validate_source_refs_format,
)


class TestParseFrontmatter:
    def test_valid_frontmatter(self, sample_source_page):
        fm = parse_frontmatter(sample_source_page)
        assert fm["title"] == "Scaling Laws for Neural Language Models"
        assert fm["type"] == "source"
        assert "2026-04-01" in str(fm["created"])

    def test_no_frontmatter(self):
        content = "# Just a heading\n\nSome content."
        fm = parse_frontmatter(content)
        assert fm == {}

    def test_empty_content(self):
        fm = parse_frontmatter("")
        assert fm == {}

    def test_list_fields(self, sample_entity_page):
        fm = parse_frontmatter(sample_entity_page)
        assert isinstance(fm.get("aliases"), list) or fm.get("aliases") is not None

    def test_source_refs_parsed(self, sample_concept_page):
        fm = parse_frontmatter(sample_concept_page)
        assert "source_refs" in fm


class TestValidatePage:
    def test_valid_source_page(self, sample_source_page):
        result = validate_page(sample_source_page, "source")
        assert result.ok, f"unexpected errors: {result.errors}"

    def test_valid_entity_page(self, sample_entity_page):
        result = validate_page(sample_entity_page, "entity")
        assert result.ok, f"unexpected errors: {result.errors}"

    def test_valid_concept_page(self, sample_concept_page):
        result = validate_page(sample_concept_page, "concept")
        assert result.ok, f"unexpected errors: {result.errors}"

    def test_invalid_type(self):
        result = validate_page("---\ntitle: test\n---\n", "invalid_type")
        assert any("Invalid page type" in e for e in result.errors)

    def test_missing_frontmatter(self):
        result = validate_page("# No frontmatter\n\nJust content.", "source")
        assert any("Missing or invalid frontmatter" in e for e in result.errors)

    def test_missing_required_fields(self):
        content = "---\ntitle: Test\ntype: source\n---\n\n## See Also\n"
        result = validate_page(content, "source")
        # Should flag missing created, updated, source_refs.
        assert not result.ok

    def test_type_mismatch(self):
        content = (
            "---\ntitle: Test\ntype: entity\nsource_refs: []\n"
            "created: 2026-01-01\nupdated: 2026-01-01\n---\n\n## See Also\n"
        )
        result = validate_page(content, "source")
        assert any("Type mismatch" in e for e in result.errors)

    def test_missing_see_also(self):
        content = (
            "---\ntitle: Test\ntype: source\nsource_refs: []\n"
            "created: 2026-01-01\nupdated: 2026-01-01\n---\n\nContent without see also."
        )
        result = validate_page(content, "source")
        assert any("See Also" in e for e in result.errors)

    def test_invalid_date_format(self):
        content = (
            "---\ntitle: Test\ntype: source\nsource_refs: []\n"
            "created: April 1 2026\nupdated: 2026-01-01\n---\n\n## See Also\n"
        )
        result = validate_page(content, "source")
        assert any("date format" in e for e in result.errors)


class TestExtractLinks:
    def test_extracts_markdown_links(self, sample_source_page):
        links = extract_links(sample_source_page)
        assert len(links) > 0
        # Check that we found links to entity/concept pages
        paths = [path for _, path in links]
        assert any("entities/" in p for p in paths)

    def test_no_links(self):
        content = "Just plain text without any links."
        links = extract_links(content)
        assert links == []

    def test_link_format(self):
        content = "[OpenAI](../entities/openai.md) is a company."
        links = extract_links(content)
        assert len(links) == 1
        assert links[0] == ("OpenAI", "../entities/openai.md")

    def test_multiple_links(self):
        content = """See [A](../entities/a.md) and [B](../concepts/b.md) for details."""
        links = extract_links(content)
        assert len(links) == 2

    def test_ignores_non_md_links(self):
        content = "[Google](https://google.com) is a website."
        links = extract_links(content)
        assert links == []


class TestValidationResult:
    def test_ok_result_has_no_errors(self):
        r = ValidationResult(ok=True, errors=[], warnings=[])
        assert r.ok is True
        assert r.errors == []

    def test_errors_imply_not_ok(self):
        r = ValidationResult(ok=False, errors=["bad"], warnings=[])
        assert r.ok is False
        assert "bad" in r.errors

    def test_warnings_do_not_block(self):
        r = ValidationResult(ok=True, errors=[], warnings=["soft"])
        assert r.ok is True
        assert r.warnings == ["soft"]


class TestValidateSourceRefsFormat:
    def test_accepts_object_form(self):
        fm = {"source_refs": [{"slug": "paper-x", "confidence": "STATED"}]}
        errors = validate_source_refs_format(fm)
        assert errors == []

    def test_accepts_multiple_object_entries(self):
        fm = {
            "source_refs": [
                {"slug": "paper-x", "confidence": "STATED"},
                {"slug": "paper-y", "confidence": "INFERRED"},
            ]
        }
        assert validate_source_refs_format(fm) == []

    def test_rejects_plain_string_entries(self):
        fm = {"source_refs": ["paper-x"]}
        errors = validate_source_refs_format(fm)
        assert any("must be objects" in e or "string" in e for e in errors)

    def test_rejects_object_missing_slug(self):
        fm = {"source_refs": [{"confidence": "STATED"}]}
        errors = validate_source_refs_format(fm)
        assert any("slug" in e for e in errors)

    def test_rejects_object_missing_confidence(self):
        fm = {"source_refs": [{"slug": "paper-x"}]}
        errors = validate_source_refs_format(fm)
        assert any("confidence" in e for e in errors)

    def test_rejects_invalid_confidence_label(self):
        fm = {"source_refs": [{"slug": "paper-x", "confidence": "MAYBE"}]}
        errors = validate_source_refs_format(fm)
        assert any("MAYBE" in e or "confidence" in e.lower() for e in errors)

    def test_empty_source_refs_is_ok(self):
        # Source pages legitimately have empty source_refs.
        assert validate_source_refs_format({"source_refs": []}) == []

    def test_missing_source_refs_field_is_not_this_validators_problem(self):
        # validate_page covers the "missing required field" check elsewhere.
        assert validate_source_refs_format({}) == []


class TestValidateLinkFormat:
    def test_accepts_relative_link(self):
        body = "## See Also\n- [OpenAI](../entities/openai.md) [STATED]\n"
        assert validate_link_format(body) == []

    def test_accepts_multiple_relative_links(self):
        body = (
            "Body with [A](../entities/a.md) and [B](../concepts/b.md) refs.\n"
            "## See Also\n- [C](../entities/c.md) [STATED]\n"
        )
        assert validate_link_format(body) == []

    def test_rejects_wiki_link_double_brackets(self):
        body = "See [[some-slug]] for details.\n## See Also\n"
        errors = validate_link_format(body)
        assert any("wiki-link" in e or "[[" in e for e in errors)

    def test_rejects_absolute_path(self):
        body = "[X](/wiki/entities/x.md)\n## See Also\n"
        errors = validate_link_format(body)
        assert any("absolute" in e or "relative" in e for e in errors)

    def test_rejects_non_md_internal_link(self):
        # Internal-looking link without .md extension.
        body = "[X](../entities/x)\n## See Also\n"
        errors = validate_link_format(body)
        assert len(errors) > 0

    def test_ignores_external_http_links(self):
        body = "[Google](https://google.com)\n## See Also\n"
        assert validate_link_format(body) == []


class TestValidateConfidenceLabels:
    def test_accepts_all_three_labels(self):
        body = (
            "## See Also\n"
            "- [A](../entities/a.md) [STATED]\n"
            "- [B](../concepts/b.md) [INFERRED]\n"
            "- [C](../entities/c.md) [UNCERTAIN]\n"
        )
        assert validate_confidence_labels(body) == []

    def test_rejects_missing_label(self):
        body = "## See Also\n- [A](../entities/a.md)\n"
        errors = validate_confidence_labels(body)
        assert any("confidence" in e.lower() for e in errors)

    def test_rejects_invalid_label(self):
        body = "## See Also\n- [A](../entities/a.md) [MAYBE]\n"
        errors = validate_confidence_labels(body)
        assert any("MAYBE" in e or "confidence" in e.lower() for e in errors)

    def test_lines_outside_see_also_are_ignored(self):
        body = (
            "Some link [A](../entities/a.md) in body without label.\n"
            "## See Also\n- [B](../concepts/b.md) [STATED]\n"
        )
        assert validate_confidence_labels(body) == []

    def test_no_see_also_section_passes(self):
        # Other validators handle the missing-section case.
        body = "Just a body, no see also."
        assert validate_confidence_labels(body) == []

    def test_blank_lines_in_see_also_are_skipped(self):
        body = (
            "## See Also\n"
            "\n"
            "- [A](../entities/a.md) [STATED]\n"
            "\n"
        )
        assert validate_confidence_labels(body) == []


class TestValidateSlugFormat:
    def test_basename_matches_normalized_title(self):
        fm = {"title": "Scaling Laws for Neural Language Models"}
        # slug_source normalizes to "scaling-laws-neural-lm" — the file basename
        # should match the title's slug derivation. We pass the basename directly.
        errors = validate_slug_format(fm, "scaling-laws-neural-lm.md")
        assert errors == []

    def test_basename_with_path_works(self):
        fm = {"title": "OpenAI"}
        errors = validate_slug_format(fm, "wiki/entities/openai.md")
        assert errors == []

    def test_uppercase_basename_fails(self):
        fm = {"title": "OpenAI"}
        errors = validate_slug_format(fm, "OpenAI.md")
        assert len(errors) > 0

    def test_underscore_basename_fails(self):
        fm = {"title": "Some Concept"}
        errors = validate_slug_format(fm, "some_concept.md")
        assert any("underscore" in e or "lowercase" in e or "hyphen" in e for e in errors)

    def test_missing_md_extension_fails(self):
        fm = {"title": "OpenAI"}
        errors = validate_slug_format(fm, "openai")
        assert any(".md" in e for e in errors)

    def test_missing_title_is_not_this_validators_problem(self):
        # validate_page covers the missing-title case via REQUIRED_FIELDS.
        assert validate_slug_format({}, "anything.md") == []


class TestValidatePageReturnsValidationResult:
    """validate_page now returns a ValidationResult, not a list."""

    def test_returns_validation_result_for_valid_page(self, sample_source_page):
        result = validate_page(sample_source_page, "source")
        assert isinstance(result, ValidationResult)
        assert result.ok is True
        assert result.errors == []

    def test_returns_errors_for_invalid_page(self):
        result = validate_page("no frontmatter", "source")
        assert isinstance(result, ValidationResult)
        assert result.ok is False
        assert len(result.errors) > 0

    def test_aggregates_new_validator_errors(self):
        # Page with the exact failure modes from commit 2bb1b6f:
        # - source_refs as plain string
        # - wiki-link in See Also
        # - missing confidence labels
        bad_page = (
            "---\n"
            "title: Bad Page\n"
            "type: entity\n"
            "source_refs:\n"
            "  - paper-x\n"
            "created: 2026-01-01\n"
            "updated: 2026-01-01\n"
            "---\n"
            "\n"
            "## See Also\n"
            "- [[some-slug]]\n"
        )
        result = validate_page(bad_page, "entity")
        assert result.ok is False
        # Expect at least: source_refs format, wiki-link, missing confidence label.
        assert len(result.errors) >= 2
