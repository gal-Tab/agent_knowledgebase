"""Tests for the quarantine helpers (lib/quarantine.py)."""
import json
from pathlib import Path

import pytest

from lib.quarantine import (
    count_quarantined,
    list_quarantined,
    move_to_quarantine,
    recover_from_quarantine,
)


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
    "## See Also\n"
    "- [Other](../entities/other.md) [STATED]\n"
)

INVALID_ENTITY = (
    "---\n"
    "title: Bad Entity\n"
    "type: entity\n"
    "source_refs:\n"
    "  - paper-x\n"  # plain string — invalid
    "created: 2026-05-01\n"
    "updated: 2026-05-01\n"
    "---\n"
    "\n"
    "## See Also\n"
    "- [Other](../entities/other.md) [STATED]\n"
)


@pytest.fixture
def wiki_root(tmp_path):
    """Create a wiki/ skeleton."""
    wiki = tmp_path / "wiki"
    for d in ("sources", "entities", "concepts", "comparisons"):
        (wiki / d).mkdir(parents=True)
    return wiki


class TestMoveToQuarantine:
    def test_writes_content_to_quarantine_path(self, wiki_root):
        target = wiki_root / "entities" / "bad.md"
        q_path = move_to_quarantine(target, INVALID_ENTITY, ["err1", "err2"], wiki_root)
        assert q_path.exists()
        assert q_path.read_text() == INVALID_ENTITY
        assert q_path == wiki_root / ".quarantine" / "entities" / "bad.md"

    def test_writes_errors_sidecar(self, wiki_root):
        target = wiki_root / "entities" / "bad.md"
        q_path = move_to_quarantine(target, INVALID_ENTITY, ["err1", "err2"], wiki_root)
        sidecar = q_path.with_suffix(".errors.json")
        assert sidecar.exists()
        data = json.loads(sidecar.read_text())
        assert data["errors"] == ["err1", "err2"]
        assert data["original_path"].endswith("entities/bad.md")

    def test_does_not_touch_original_target(self, wiki_root):
        target = wiki_root / "entities" / "existing.md"
        target.write_text("PRIOR")
        move_to_quarantine(target, INVALID_ENTITY, ["err"], wiki_root)
        assert target.read_text() == "PRIOR"

    def test_creates_quarantine_directory(self, wiki_root):
        target = wiki_root / "concepts" / "new.md"
        q_path = move_to_quarantine(target, INVALID_ENTITY, ["err"], wiki_root)
        assert q_path.parent.exists()

    def test_overwrites_existing_quarantined_entry(self, wiki_root):
        target = wiki_root / "entities" / "bad.md"
        move_to_quarantine(target, "OLD CONTENT", ["old-err"], wiki_root)
        q_path = move_to_quarantine(target, INVALID_ENTITY, ["new-err"], wiki_root)
        assert q_path.read_text() == INVALID_ENTITY
        sidecar = q_path.with_suffix(".errors.json")
        assert json.loads(sidecar.read_text())["errors"] == ["new-err"]


class TestCountQuarantined:
    def test_zero_when_dir_missing(self, wiki_root):
        assert count_quarantined(wiki_root) == 0

    def test_zero_when_dir_empty(self, wiki_root):
        (wiki_root / ".quarantine").mkdir()
        assert count_quarantined(wiki_root) == 0

    def test_counts_md_files_only(self, wiki_root):
        target = wiki_root / "entities" / "a.md"
        move_to_quarantine(target, INVALID_ENTITY, ["e"], wiki_root)
        # Should count the .md page, not the .errors.json sidecar.
        assert count_quarantined(wiki_root) == 1

    def test_counts_across_categories(self, wiki_root):
        move_to_quarantine(wiki_root / "entities" / "a.md", INVALID_ENTITY, ["e"], wiki_root)
        move_to_quarantine(wiki_root / "concepts" / "b.md", INVALID_ENTITY, ["e"], wiki_root)
        assert count_quarantined(wiki_root) == 2


class TestListQuarantined:
    def test_returns_empty_when_no_quarantine(self, wiki_root):
        assert list_quarantined(wiki_root) == []

    def test_returns_quarantined_paths(self, wiki_root):
        move_to_quarantine(wiki_root / "entities" / "a.md", INVALID_ENTITY, ["e"], wiki_root)
        move_to_quarantine(wiki_root / "concepts" / "b.md", INVALID_ENTITY, ["e"], wiki_root)
        paths = list_quarantined(wiki_root)
        assert len(paths) == 2
        assert all(p.suffix == ".md" for p in paths)


class TestRecoverFromQuarantine:
    def test_recovers_when_now_valid(self, wiki_root):
        target = wiki_root / "entities" / "fixed.md"
        q_path = move_to_quarantine(target, INVALID_ENTITY, ["e"], wiki_root)
        # User manually edits the quarantined file to fix the violation.
        q_path.write_text(VALID_ENTITY)
        result = recover_from_quarantine(q_path, wiki_root)
        assert result.ok
        assert target.exists()
        assert target.read_text() == VALID_ENTITY
        assert not q_path.exists(), "quarantined file should be removed after recovery"
        assert not q_path.with_suffix(".errors.json").exists()

    def test_refuses_recovery_if_still_invalid(self, wiki_root):
        target = wiki_root / "entities" / "still-bad.md"
        q_path = move_to_quarantine(target, INVALID_ENTITY, ["e"], wiki_root)
        result = recover_from_quarantine(q_path, wiki_root)
        assert not result.ok
        assert q_path.exists(), "quarantine file must remain on failed recovery"
        assert not target.exists(), "target must not be created when recovery fails"
