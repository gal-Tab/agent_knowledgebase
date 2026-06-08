"""Tests for dedup-on-write resolution of compound learnings.

tools/resolve_learnings.py mirrors tools/resolve_candidates.py: a pure classifier
(CREATE / UPDATE / SKIP / SUPERSEDE) plus the "corrections always win" supersede
mechanic (archive the contradicted learning, drop it from the active index).
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

from tools.resolve_learnings import (
    CREATE,
    UPDATE,
    SKIP,
    SUPERSEDE,
    topic_key,
    classify_learning,
    format_brief,
    supersede,
)
from lib.learning_store import learning_id, write_learning
from lib.learning_index import append_entry, entry_from_content, parse_index


def _learning(type_, headline, tags, lid=None, created="2026-06-08",
              status="active", scope="project", supersedes=None, superseded_by=None,
              confidence="STATED"):
    lid = lid or learning_id(headline, created)
    sup = supersedes if supersedes is not None else []
    return f"""---
id: {lid}
type: {type_}
scope: {scope}
headline: "{headline}"
tags: [{", ".join(tags)}]
confidence: {confidence}
created: {created}
updated: {created}
status: {status}
supersedes: [{", ".join(supersedes or [])}]
superseded_by: {superseded_by if superseded_by else "null"}
---

## Learning
The durable lesson about {headline}.

## Context
When {tags[0] if tags else "this"} comes up.

## Implication
Do the right thing next time.
"""


def _entry(type_, headline, tags, lid=None, created="2026-06-08"):
    return entry_from_content(_learning(type_, headline, tags, lid=lid, created=created))


class TestTopicKey:
    def test_extracts_slug_from_id(self):
        lid = learning_id("Add jitter to retry backoff", "2026-06-08")
        assert topic_key(lid) == topic_key("Add jitter to retry backoff")

    def test_same_lesson_different_date_same_key(self):
        a = learning_id("Add jitter to retry backoff", "2026-06-08")
        b = learning_id("Add jitter to retry backoff", "2026-07-01")
        assert topic_key(a) == topic_key(b)

    def test_different_lessons_differ(self):
        a = learning_id("Add jitter to retry backoff", "2026-06-08")
        b = learning_id("Order Dockerfile layers for cache", "2026-06-08")
        assert topic_key(a) != topic_key(b)


class TestClassify:
    def test_create_when_no_match(self):
        cand = {"type": "insight", "headline": "Brand new lesson", "tags": ["x"]}
        r = classify_learning(cand, existing=[])
        assert r["action"] == CREATE

    def test_skip_when_identical_same_type(self):
        existing = [_entry("insight", "Use backoff for retries", ["retries", "backoff"])]
        cand = {"type": "insight", "headline": "Use backoff for retries",
                "tags": ["retries", "backoff"]}
        r = classify_learning(cand, existing)
        assert r["action"] == SKIP
        assert r["target_id"] == existing[0]["id"]

    def test_update_when_same_topic_same_type_changed_tags(self):
        existing = [_entry("insight", "Use backoff for retries", ["retries"])]
        cand = {"type": "insight", "headline": "Use backoff for retries",
                "tags": ["retries", "backoff", "jitter"]}
        r = classify_learning(cand, existing)
        assert r["action"] == UPDATE
        assert r["target_id"] == existing[0]["id"]

    def test_supersede_when_explicit_supersedes(self):
        old = _entry("insight", "Retry without jitter is fine", ["retries"])
        cand = {"type": "correction", "headline": "Retries need jitter after all",
                "tags": ["retries"], "supersedes": [old["id"]]}
        r = classify_learning(cand, [old])
        assert r["action"] == SUPERSEDE
        assert r["superseded_ids"] == [old["id"]]

    def test_correction_supersedes_same_topic_noncorrection(self):
        # corrections always win: a correction on the same topic as an active
        # non-correction supersedes it even without an explicit supersedes list.
        old = _entry("insight", "Skip retries on 500s", ["retries", "errors"])
        cand = {"type": "correction", "headline": "Skip retries on 500s",
                "tags": ["retries", "errors"]}
        r = classify_learning(cand, [old])
        assert r["action"] == SUPERSEDE
        assert old["id"] in r["superseded_ids"]

    def test_correction_does_not_supersede_matching_correction(self):
        # same-topic correction already exists -> dedup (skip/update), not self-supersede
        old = _entry("correction", "Add jitter to retries", ["retries"])
        cand = {"type": "correction", "headline": "Add jitter to retries",
                "tags": ["retries"]}
        r = classify_learning(cand, [old])
        assert r["action"] == SKIP

    def test_explicit_supersedes_ignored_if_target_absent(self):
        cand = {"type": "correction", "headline": "New thing", "tags": ["x"],
                "supersedes": ["kw-2020-01-01-ghost"]}
        r = classify_learning(cand, existing=[])
        assert r["action"] == CREATE


class TestFormatBrief:
    def test_empty_when_all_skip(self):
        rs = [{"action": SKIP, "candidate": {"headline": "h"}, "target_id": "kw-x",
               "superseded_ids": []}]
        assert format_brief(rs) == ""

    def test_lists_actionable(self):
        rs = [
            {"action": CREATE, "candidate": {"type": "insight", "headline": "New one"},
             "target_id": None, "superseded_ids": []},
            {"action": SUPERSEDE, "candidate": {"type": "correction", "headline": "Fix it"},
             "target_id": None, "superseded_ids": ["kw-old"]},
        ]
        out = format_brief(rs)
        assert "CREATE" in out
        assert "SUPERSEDE" in out
        assert "New one" in out
        assert "kw-old" in out

    def test_update_branch_names_target(self):
        rs = [{"action": UPDATE, "candidate": {"type": "insight", "headline": "Refined"},
               "target_id": "kw-2026-06-08-refined", "superseded_ids": []}]
        out = format_brief(rs)
        assert "UPDATE" in out
        assert "Refined" in out
        assert "updates kw-2026-06-08-refined" in out


class TestSupersedeSideEffect:
    def test_archives_old_and_drops_from_index(self, tmp_path):
        root = tmp_path / ".compound"
        # seed an active insight + its index line
        old_content = _learning("insight", "Skip retries on 500s", ["retries"])
        res = write_learning(root, old_content)
        assert res.ok
        old_id = entry_from_content(old_content)["id"]
        append_entry(root / "index.md", entry_from_content(old_content))

        new_id = learning_id("Skip retries on 500s", "2026-07-01")
        arch = supersede(root, old_id, new_id, reason="contradicted by correction")

        # old body left the active type dir, now under .archive/
        assert not (root / "insights" / f"{old_id}.md").exists()
        assert Path(arch).exists()
        assert ".archive" in str(arch)

        # archived copy carries the superseded status + pointer
        archived_text = Path(arch).read_text()
        assert "status: superseded" in archived_text
        assert new_id in archived_text

        # sidecar records the supersession
        sidecar = Path(arch).with_suffix(".archive.json")
        assert sidecar.exists()
        assert new_id in sidecar.read_text()

        # index no longer lists the superseded learning
        index_ids = [e["id"] for e in parse_index((root / "index.md").read_text())]
        assert old_id not in index_ids

    def test_supersede_missing_id_raises(self, tmp_path):
        root = tmp_path / ".compound"
        root.mkdir()
        with pytest.raises(Exception):
            supersede(root, "kw-2020-01-01-ghost", "kw-new", reason="x")


class TestCLI:
    """The CLI is dry-run by default; --apply performs the supersede side effect."""

    def _seed(self, tmp_path):
        root = tmp_path / ".compound"
        old = _learning("insight", "Skip retries on 500s", ["retries"], created="2026-06-01")
        write_learning(root, old)
        old_id = entry_from_content(old)["id"]
        append_entry(root / "index.md", entry_from_content(old))
        draft = tmp_path / "cand.md"
        draft.write_text(_learning("correction", "Skip retries on 500s", ["retries"],
                                   created="2026-07-01"))
        return root, old_id, draft

    def _run(self, draft, root, *extra):
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "tools" / "resolve_learnings.py"),
             str(draft), "--root", str(root), *extra],
            capture_output=True, text=True,
        )

    def test_dry_run_classifies_without_side_effects(self, tmp_path):
        root, old_id, draft = self._seed(tmp_path)
        proc = self._run(draft, root)
        assert proc.returncode == 0, proc.stderr
        assert "SUPERSEDE" in proc.stdout
        # nothing archived, old still active in the index
        assert (root / "insights" / f"{old_id}.md").exists()
        assert old_id in (root / "index.md").read_text()

    def test_apply_performs_supersede(self, tmp_path):
        root, old_id, draft = self._seed(tmp_path)
        proc = self._run(draft, root, "--apply")
        assert proc.returncode == 0, proc.stderr
        assert "archived" in proc.stdout
        assert not (root / "insights" / f"{old_id}.md").exists()
        assert old_id not in (root / "index.md").read_text()
        assert (root / ".archive" / "insights" / f"{old_id}.md").exists()
