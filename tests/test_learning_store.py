"""Tests for the compound-learning store (lib/learning_store.py)."""
import json

import pytest

from lib.learning_store import (
    TYPE_DIRS,
    archive_path_for,
    dest_path,
    edit_learning,
    global_root,
    learning_id,
    merge_learnings,
    move_to_archive,
    project_root,
    resolve_stores,
    write_learning,
)

VALID_LEARNING = (
    "---\n"
    "id: kw-2026-06-08-retry-jitter\n"
    "type: correction\n"
    "scope: project\n"
    'headline: "Add jitter to retry backoff or thundering-herd recurs"\n'
    "tags: [retries, networking]\n"
    "confidence: STATED\n"
    "created: 2026-06-08\n"
    "updated: 2026-06-08\n"
    "status: active\n"
    "---\n"
    "\n"
    "## Learning\nAdd jitter to exponential backoff.\n"
    "\n## Context\nObserved during a flaky deploy poller.\n"
    "\n## Implication\nDefault new retry loops to full-jitter backoff.\n"
)

INVALID_LEARNING = VALID_LEARNING.replace("type: correction", "type: rumor")


@pytest.fixture
def isolated_global(tmp_path, monkeypatch):
    """Point the global store at a tmp dir so tests never touch ~/.claude."""
    g = tmp_path / "global"
    monkeypatch.setenv("COMPOUND_KNOWLEDGE_HOME", str(g))
    return g


class TestPaths:
    def test_global_root_from_env(self, isolated_global):
        assert global_root() == isolated_global

    def test_project_root(self, tmp_path):
        assert project_root(tmp_path) == tmp_path / ".compound"

    def test_learning_id_format(self):
        assert learning_id("Add jitter to retry backoff", "2026-06-08") == (
            "kw-2026-06-08-add-jitter-retry-backoff"
        )

    def test_dest_path_uses_type_dir_and_id(self, tmp_path):
        root = tmp_path / ".compound"
        path = dest_path(root, VALID_LEARNING)
        assert path == root / TYPE_DIRS["correction"] / "kw-2026-06-08-retry-jitter.md"


class TestResolveStores:
    def test_project_first_then_global(self, tmp_path, isolated_global):
        (tmp_path / ".compound").mkdir()
        isolated_global.mkdir(parents=True)
        stores = resolve_stores(tmp_path)
        assert [s[0] for s in stores] == ["project", "global"]

    def test_only_project_when_no_global(self, tmp_path, isolated_global):
        (tmp_path / ".compound").mkdir()
        stores = resolve_stores(tmp_path)
        assert [s[0] for s in stores] == ["project"]

    def test_empty_when_neither_exists(self, tmp_path, isolated_global):
        assert resolve_stores(tmp_path) == []


class TestWriteLearning:
    def test_writes_valid_learning(self, tmp_path):
        root = tmp_path / ".compound"
        result = write_learning(root, VALID_LEARNING)
        assert result.ok, result.errors
        path = dest_path(root, VALID_LEARNING)
        assert path.exists()
        assert path.read_text() == VALID_LEARNING

    def test_self_creates_type_dir(self, tmp_path):
        # The store bootstraps its own directories.
        root = tmp_path / ".compound"
        assert not root.exists()
        assert write_learning(root, VALID_LEARNING).ok
        assert (root / TYPE_DIRS["correction"]).is_dir()

    def test_refuses_invalid_learning(self, tmp_path):
        root = tmp_path / ".compound"
        result = write_learning(root, INVALID_LEARNING)
        assert not result.ok
        # Nothing should have been written anywhere under the store.
        assert not any(root.rglob("*.md")) if root.exists() else True

    def test_does_not_overwrite_on_failure(self, tmp_path):
        root = tmp_path / ".compound"
        assert write_learning(root, VALID_LEARNING).ok
        path = dest_path(root, VALID_LEARNING)
        # An invalid edit of the same id must not clobber the good file.
        broken = VALID_LEARNING.replace("status: active", "status: nope")
        assert not write_learning(root, broken).ok
        assert path.read_text() == VALID_LEARNING


class TestEditLearning:
    def test_applies_valid_edit(self, tmp_path):
        root = tmp_path / ".compound"
        write_learning(root, VALID_LEARNING)
        path = dest_path(root, VALID_LEARNING)
        result = edit_learning(path, "full-jitter backoff.", "decorrelated jitter.")
        assert result.ok, result.errors
        assert "decorrelated jitter." in path.read_text()

    def test_rejects_edit_breaking_validation(self, tmp_path):
        root = tmp_path / ".compound"
        write_learning(root, VALID_LEARNING)
        path = dest_path(root, VALID_LEARNING)
        before = path.read_text()
        result = edit_learning(path, "## Implication", "## Outcome")
        assert not result.ok
        assert path.read_text() == before

    def test_rejects_missing_file(self, tmp_path):
        result = edit_learning(tmp_path / "nope.md", "a", "b")
        assert not result.ok


class TestArchive:
    def test_move_to_archive_relocates_with_sidecar(self, tmp_path):
        root = tmp_path / ".compound"
        write_learning(root, VALID_LEARNING)
        src = dest_path(root, VALID_LEARNING)
        assert src.exists()

        dst = move_to_archive(
            root, "correction", "kw-2026-06-08-retry-jitter",
            reason="superseded", superseded_by="kw-2026-07-01-retry-decorrelated",
        )
        assert dst == archive_path_for(root, "correction", "kw-2026-06-08-retry-jitter")
        assert dst.exists()
        assert not src.exists(), "archived learning must leave the active store"

        sidecar = dst.with_suffix(".archive.json")
        payload = json.loads(sidecar.read_text())
        assert payload["reason"] == "superseded"
        assert payload["superseded_by"] == "kw-2026-07-01-retry-decorrelated"


class TestMerge:
    def test_project_shadows_global_by_id(self):
        project = [{"id": "a", "scope": "project"}, {"id": "b", "scope": "project"}]
        glob = [{"id": "b", "scope": "global"}, {"id": "c", "scope": "global"}]
        merged = merge_learnings(project, glob)
        ids = {m["id"]: m["scope"] for m in merged}
        assert ids == {"a": "project", "b": "project", "c": "global"}
