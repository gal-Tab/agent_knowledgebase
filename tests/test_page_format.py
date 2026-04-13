"""Tests for page format validation (lib/page_format.py)."""
import pytest

from lib.page_format import parse_frontmatter, validate_page, extract_links


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
        errors = validate_page(sample_source_page, "source")
        assert errors == []

    def test_valid_entity_page(self, sample_entity_page):
        errors = validate_page(sample_entity_page, "entity")
        assert errors == []

    def test_valid_concept_page(self, sample_concept_page):
        errors = validate_page(sample_concept_page, "concept")
        assert errors == []

    def test_invalid_type(self):
        errors = validate_page("---\ntitle: test\n---\n", "invalid_type")
        assert any("Invalid page type" in e for e in errors)

    def test_missing_frontmatter(self):
        content = "# No frontmatter\n\nJust content."
        errors = validate_page(content, "source")
        assert any("Missing or invalid frontmatter" in e for e in errors)

    def test_missing_required_fields(self):
        content = "---\ntitle: Test\ntype: source\n---\n\n## See Also\n"
        errors = validate_page(content, "source")
        # Should flag missing created, updated, source_refs
        assert len(errors) > 0

    def test_type_mismatch(self):
        content = "---\ntitle: Test\ntype: entity\nsource_refs: []\ncreated: 2026-01-01\nupdated: 2026-01-01\n---\n\n## See Also\n"
        errors = validate_page(content, "source")
        assert any("Type mismatch" in e for e in errors)

    def test_missing_see_also(self):
        content = "---\ntitle: Test\ntype: source\nsource_refs: []\ncreated: 2026-01-01\nupdated: 2026-01-01\n---\n\nContent without see also."
        errors = validate_page(content, "source")
        assert any("See Also" in e for e in errors)

    def test_invalid_date_format(self):
        content = "---\ntitle: Test\ntype: source\nsource_refs: []\ncreated: April 1 2026\nupdated: 2026-01-01\n---\n\n## See Also\n"
        errors = validate_page(content, "source")
        assert any("date format" in e for e in errors)


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
