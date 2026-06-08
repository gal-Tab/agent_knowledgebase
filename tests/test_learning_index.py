"""Tests for the compound-learnings index (lib/learning_index.py + CLI)."""
import subprocess
import sys
from pathlib import Path

from lib.learning_index import (
    append_entry,
    build_index,
    format_line,
    parse_index,
    parse_line,
    rebuild,
    scan_store,
)
from lib.learning_store import move_to_archive, write_learning

PROJECT_ROOT = Path(__file__).parent.parent


def _learning(lid, ltype, headline, tags, date="2026-06-08", status="active"):
    taglist = ", ".join(tags)
    return (
        "---\n"
        f"id: {lid}\n"
        f"type: {ltype}\n"
        "scope: project\n"
        f'headline: "{headline}"\n'
        f"tags: [{taglist}]\n"
        "confidence: STATED\n"
        f"created: {date}\n"
        f"updated: {date}\n"
        f"status: {status}\n"
        "---\n"
        "\n## Learning\nx\n\n## Context\ny\n\n## Implication\nz\n"
    )


def _entry(lid, ltype, headline, tags, date="2026-06-08"):
    return {"type": ltype, "id": lid, "tags": tags, "headline": headline,
            "confidence": "STATED", "date": date}


class TestLineRoundTrip:
    def test_round_trip_each_type(self):
        for ltype in ("insight", "playbook", "correction", "pattern"):
            e = _entry(f"kw-x-{ltype}", ltype, "A headline", ["t1", "t2"])
            parsed = parse_line(format_line(e))
            assert parsed["type"] == ltype
            assert parsed["id"] == e["id"]
            assert parsed["tags"] == ["t1", "t2"]
            assert parsed["headline"] == "A headline"

    def test_non_learning_lines_ignored(self):
        assert parse_line("# Compound Learnings Index") is None
        assert parse_line("## corrections") is None
        assert parse_line("") is None

    def test_pipe_in_headline_sanitized(self):
        e = _entry("kw-1", "insight", "use a | b pipe", ["t"])
        line = format_line(e)
        assert line.count("|") == 4  # the 4 schema delimiters, none from headline
        assert parse_line(line) is not None


class TestBuildIndex:
    def test_corrections_bucket_first(self):
        entries = [
            _entry("kw-i", "insight", "i", ["a"]),
            _entry("kw-c", "correction", "c", ["a"]),
            _entry("kw-p", "playbook", "p", ["a"]),
        ]
        text = build_index(entries, updated="2026-06-08")
        assert text.index("## corrections") < text.index("## playbooks")
        assert text.index("## corrections") < text.index("## insights")

    def test_header_counts(self):
        entries = [
            _entry("kw-c1", "correction", "c", ["a"]),
            _entry("kw-c2", "correction", "c", ["a"]),
            _entry("kw-i1", "insight", "i", ["a"]),
        ]
        text = build_index(entries, updated="2026-06-08", archived=3)
        assert "Total: 3 (1i/0p/2c/0pa)" in text
        assert "Archived: 3" in text

    def test_only_nonempty_buckets_emitted(self):
        text = build_index([_entry("kw-i", "insight", "i", ["a"])], updated="2026-06-08")
        assert "## insights" in text
        assert "## corrections" not in text


class TestScanStore:
    def test_scan_excludes_archived_and_inactive(self, tmp_path):
        root = tmp_path / ".compound"
        write_learning(root, _learning("kw-2026-06-08-active-one", "insight", "active", ["x"]))
        write_learning(root, _learning("kw-2026-06-08-super", "correction", "super", ["x"],
                                       status="superseded"))
        # archive an active learning → must drop out of the scan
        write_learning(root, _learning("kw-2026-06-08-arch", "playbook", "arch", ["x"]))
        move_to_archive(root, "playbook", "kw-2026-06-08-arch", reason="test")

        ids = {e["id"] for e in scan_store(root)}
        assert ids == {"kw-2026-06-08-active-one"}


class TestAppend:
    def test_append_adds_one_line_and_counts(self, tmp_path):
        index = tmp_path / "index.md"
        append_entry(index, _entry("kw-1", "correction", "first", ["a"]), updated="2026-06-08")
        text = index.read_text()
        assert text.count("- [") == 1
        assert "Total: 1 (0i/0p/1c/0pa)" in text

    def test_append_same_id_replaces_no_dup(self, tmp_path):
        index = tmp_path / "index.md"
        append_entry(index, _entry("kw-1", "insight", "old", ["a"]), updated="2026-06-08")
        append_entry(index, _entry("kw-1", "insight", "new headline", ["a"]), updated="2026-06-08")
        text = index.read_text()
        assert text.count("- [") == 1
        assert "new headline" in text
        assert "old" not in text

    def test_append_preserves_archived_count(self, tmp_path):
        index = tmp_path / "index.md"
        index.write_text(
            "# Compound Learnings Index\n"
            "Updated: 2026-06-01 | Total: 0 (0i/0p/0c/0pa) | Archived: 7\n"
        )
        append_entry(index, _entry("kw-1", "insight", "h", ["a"]), updated="2026-06-08")
        assert "Archived: 7" in index.read_text()


class TestRebuild:
    def test_rebuild_reconstructs_from_store(self, tmp_path):
        root = tmp_path / ".compound"
        write_learning(root, _learning("kw-2026-06-08-one", "insight", "one", ["x"]))
        write_learning(root, _learning("kw-2026-06-08-two", "correction", "two", ["y"]))
        rebuild(root, updated="2026-06-08")
        entries = parse_index((root / "index.md").read_text())
        assert {e["id"] for e in entries} == {"kw-2026-06-08-one", "kw-2026-06-08-two"}


class TestCLI:
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "tools" / "learning_index.py"), *args],
            capture_output=True, text=True,
        )

    def test_append_then_rebuild_cli(self, tmp_path):
        root = tmp_path / ".compound"
        write_learning(root, _learning("kw-2026-06-08-cli", "playbook", "cli learning", ["ops"]))
        path = root / "playbooks" / "kw-2026-06-08-cli.md"

        proc = self._run("append", str(path))
        assert proc.returncode == 0, proc.stderr
        assert "kw-2026-06-08-cli" in (root / "index.md").read_text()

        proc = self._run("rebuild", "--root", str(root))
        assert proc.returncode == 0, proc.stderr
        assert "kw-2026-06-08-cli" in (root / "index.md").read_text()
