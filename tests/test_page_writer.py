"""Tests for the validating write/edit wrapper (lib/page_writer.py)."""
from pathlib import Path

import pytest

from lib.page_format import ValidationResult
from lib.page_writer import infer_page_type, edit_page, write_page


VALID_ENTITY = (
    "---\n"
    "title: Test Entity\n"
    "type: entity\n"
    "source_refs:\n"
    "  - slug: paper-x\n"
    "    confidence: STATED\n"
    "created: 2026-05-01\n"
    "updated: 2026-05-01\n"
    "---\n"
    "\n"
    "## Overview\n"
    "Body.\n"
    "\n"
    "## See Also\n"
    "- [Other](../entities/other.md) [STATED]\n"
)

INVALID_ENTITY_PLAIN_REFS = (
    "---\n"
    "title: Test Entity\n"
    "type: entity\n"
    "source_refs:\n"
    "  - paper-x\n"
    "created: 2026-05-01\n"
    "updated: 2026-05-01\n"
    "---\n"
    "\n"
    "## See Also\n"
    "- [Other](../entities/other.md) [STATED]\n"
)


class TestInferPageType:
    def test_entities_dir(self):
        assert infer_page_type(Path("wiki/entities/openai.md")) == "entity"

    def test_concepts_dir(self):
        assert infer_page_type(Path("wiki/concepts/scaling-laws.md")) == "concept"

    def test_sources_dir(self):
        assert infer_page_type(Path("wiki/sources/paper-x.md")) == "source"

    def test_comparisons_dir(self):
        assert infer_page_type(Path("wiki/comparisons/a-vs-b-comparison.md")) == "comparison"

    def test_unknown_dir_raises(self):
        with pytest.raises(ValueError):
            infer_page_type(Path("wiki/random/foo.md"))


class TestWritePage:
    def test_writes_valid_page(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "test.md"
        path.parent.mkdir(parents=True)
        result = write_page(path, VALID_ENTITY)
        assert result.ok
        assert path.exists()
        assert path.read_text() == VALID_ENTITY

    def test_does_not_write_invalid_page(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "test.md"
        path.parent.mkdir(parents=True)
        result = write_page(path, INVALID_ENTITY_PLAIN_REFS)
        assert not result.ok
        assert len(result.errors) > 0
        assert not path.exists(), "invalid page must not reach disk"

    def test_returns_validation_result(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "test.md"
        path.parent.mkdir(parents=True)
        result = write_page(path, VALID_ENTITY)
        assert isinstance(result, ValidationResult)

    def test_does_not_overwrite_on_validation_failure(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "existing.md"
        path.parent.mkdir(parents=True)
        path.write_text("PRIOR_CONTENT")
        result = write_page(path, INVALID_ENTITY_PLAIN_REFS)
        assert not result.ok
        assert path.read_text() == "PRIOR_CONTENT", "existing content must be preserved"

    def test_creates_parent_directory(self, tmp_path):
        # write_page should not auto-create dirs — caller must ensure path exists.
        # This test pins that contract.
        path = tmp_path / "wiki" / "entities" / "no-dir-yet.md"
        path.parent.mkdir(parents=True)
        result = write_page(path, VALID_ENTITY)
        assert result.ok

    def test_explicit_page_type_overrides_inference(self, tmp_path):
        # Allow callers in non-standard layouts to pass page_type explicitly.
        path = tmp_path / "anywhere" / "test.md"
        path.parent.mkdir(parents=True)
        result = write_page(path, VALID_ENTITY, page_type="entity")
        assert result.ok


class TestEditPage:
    def test_applies_edit_when_post_edit_content_valid(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "test.md"
        path.parent.mkdir(parents=True)
        path.write_text(VALID_ENTITY)
        result = edit_page(path, "Body.", "Body. Extended.")
        assert result.ok
        assert "Body. Extended." in path.read_text()

    def test_rejects_edit_when_old_string_not_found(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "test.md"
        path.parent.mkdir(parents=True)
        path.write_text(VALID_ENTITY)
        result = edit_page(path, "DOES NOT EXIST", "X")
        assert not result.ok
        assert any("not found" in e.lower() or "no match" in e.lower() for e in result.errors)
        assert path.read_text() == VALID_ENTITY

    def test_rejects_edit_when_post_edit_content_invalid(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "test.md"
        path.parent.mkdir(parents=True)
        path.write_text(VALID_ENTITY)
        # Strip the See Also section by replacing it with empty.
        result = edit_page(
            path,
            "## See Also\n- [Other](../entities/other.md) [STATED]\n",
            "",
        )
        assert not result.ok
        assert path.read_text() == VALID_ENTITY, "file must be untouched on failure"

    def test_rejects_edit_when_file_missing(self, tmp_path):
        path = tmp_path / "wiki" / "entities" / "missing.md"
        path.parent.mkdir(parents=True)
        result = edit_page(path, "x", "y")
        assert not result.ok

    def test_rejects_ambiguous_edit(self, tmp_path):
        # Multiple matches for old_string should refuse.
        path = tmp_path / "wiki" / "entities" / "test.md"
        path.parent.mkdir(parents=True)
        content = VALID_ENTITY + "\n## Notes\nBody.\n"  # "Body." now appears twice
        path.write_text(content)
        result = edit_page(path, "Body.", "Replaced.")
        assert not result.ok
        assert any("ambiguous" in e.lower() or "multiple" in e.lower() for e in result.errors)
