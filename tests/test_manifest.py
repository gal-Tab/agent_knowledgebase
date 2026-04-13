"""Tests for manifest management (lib/manifest.py)."""
import json

import pytest

from lib.manifest import (
    load_manifest,
    save_manifest,
    add_entry,
    update_status,
    get_pending,
    get_by_status,
)


class TestLoadSave:
    def test_load_nonexistent_returns_empty(self, tmp_path):
        result = load_manifest(tmp_path / "nonexistent.json")
        assert result == {}

    def test_roundtrip(self, tmp_path):
        path = tmp_path / "manifest.json"
        data = {"test.pdf": {"status": "new", "sha256": "abc123"}}
        save_manifest(path, data)
        loaded = load_manifest(path)
        assert loaded == data

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "subdir" / "manifest.json"
        save_manifest(path, {"key": "value"})
        assert path.exists()


class TestAddEntry:
    def test_adds_new_entry(self):
        manifest = {}
        result = add_entry(manifest, "paper.pdf", "abc123def456")
        assert "paper.pdf" in result
        assert result["paper.pdf"]["status"] == "new"
        assert result["paper.pdf"]["sha256"] == "abc123def456"
        assert result["paper.pdf"]["source_page"] is None
        assert result["paper.pdf"]["wiki_pages"] == []
        assert result["paper.pdf"]["extracted_at"] is None
        assert result["paper.pdf"]["compiled_at"] is None
        assert result["paper.pdf"]["error"] is None

    def test_preserves_existing_entries(self):
        manifest = {"old.pdf": {"status": "compiled"}}
        add_entry(manifest, "new.pdf", "hash123")
        assert "old.pdf" in manifest
        assert "new.pdf" in manifest


class TestUpdateStatus:
    def test_valid_status_transition(self):
        manifest = {"file.pdf": {"status": "new", "extracted_at": None, "compiled_at": None}}
        update_status(manifest, "file.pdf", "extracted")
        assert manifest["file.pdf"]["status"] == "extracted"
        assert manifest["file.pdf"]["extracted_at"] is not None

    def test_compiled_sets_timestamp(self):
        manifest = {"file.pdf": {"status": "extracted", "extracted_at": "2026-01-01", "compiled_at": None}}
        update_status(manifest, "file.pdf", "compiled")
        assert manifest["file.pdf"]["compiled_at"] is not None

    def test_invalid_status_raises(self):
        manifest = {"file.pdf": {"status": "new"}}
        with pytest.raises(ValueError, match="Invalid status"):
            update_status(manifest, "file.pdf", "invalid_status")

    def test_missing_file_raises(self):
        manifest = {}
        with pytest.raises(KeyError, match="not found"):
            update_status(manifest, "missing.pdf", "compiled")

    def test_kwargs_merged(self):
        manifest = {"file.pdf": {"status": "new", "source_page": None, "error": None,
                                  "extracted_at": None, "compiled_at": None}}
        update_status(manifest, "file.pdf", "compiled", source_page="wiki/sources/file.md")
        assert manifest["file.pdf"]["source_page"] == "wiki/sources/file.md"

    def test_failed_status(self):
        manifest = {"file.pdf": {"status": "new", "error": None,
                                  "extracted_at": None, "compiled_at": None}}
        update_status(manifest, "file.pdf", "failed", error="extraction error")
        assert manifest["file.pdf"]["status"] == "failed"
        assert manifest["file.pdf"]["error"] == "extraction error"


class TestGetPending:
    def test_new_files_are_pending(self):
        manifest = {"a.pdf": {"status": "new"}, "b.pdf": {"status": "compiled", "compiled_at": "2026-01-01"}}
        assert get_pending(manifest) == ["a.pdf"]

    def test_extracted_without_compiled_is_pending(self):
        manifest = {"a.pdf": {"status": "extracted", "compiled_at": None}}
        assert get_pending(manifest) == ["a.pdf"]

    def test_failed_files_are_pending(self):
        manifest = {"a.pdf": {"status": "failed"}}
        assert get_pending(manifest) == ["a.pdf"]

    def test_compiled_not_pending(self):
        manifest = {"a.pdf": {"status": "compiled", "compiled_at": "2026-01-01"}}
        assert get_pending(manifest) == []

    def test_empty_manifest(self):
        assert get_pending({}) == []


class TestGetByStatus:
    def test_filters_correctly(self, sample_manifest):
        compiled = get_by_status(sample_manifest, "compiled")
        assert "paper-one.pdf" in compiled

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            get_by_status({}, "nonexistent")

    def test_empty_result(self):
        manifest = {"a.pdf": {"status": "compiled"}}
        assert get_by_status(manifest, "new") == []
