"""Tests for hook output parsing (lib/hook_parser.py)."""
from lib.hook_parser import parse_hook_output


class TestParseHookOutput:
    def test_empty_output(self):
        result = parse_hook_output("")
        assert result["has_header"] is False
        assert result["new_files"] == []
        assert result["has_work"] is False

    def test_none_output(self):
        result = parse_hook_output(None)
        assert result["has_work"] is False

    def test_full_output(self):
        output = """=== KB Status ===
New files in raw/: paper.pdf, notes.md
Updated files: old-paper.pdf
Last session: abc1234 [session] End: compiled 2 sources | wiki: 35pp
Wiki: 35 pages (15s/12e/6c/2x)
ACTION: Compile these files now. Use /kb-compile or say "compile the new files"."""
        result = parse_hook_output(output)

        assert result["has_header"] is True
        assert result["new_files"] == ["paper.pdf", "notes.md"]
        assert result["updated_files"] == ["old-paper.pdf"]
        assert result["has_work"] is True
        assert result["last_session"] is not None
        assert "abc1234" in result["last_session"]
        assert result["wiki_stats"]["total"] == 35
        assert result["wiki_stats"]["sources"] == 15
        assert result["wiki_stats"]["entities"] == 12
        assert result["wiki_stats"]["concepts"] == 6
        assert result["wiki_stats"]["comparisons"] == 2

    def test_no_work_needed(self):
        output = """=== KB Status ===
No new or updated files in raw/
Last session: (none)
Wiki: 0 pages (0s/0e/0c/0x)"""
        result = parse_hook_output(output)

        assert result["has_header"] is True
        assert result["has_work"] is False
        assert result["new_files"] == []
        assert result["last_session"] is None
        assert result["wiki_stats"]["total"] == 0

    def test_pending_files(self):
        output = """=== KB Status ===
Pending compilation: half-done.pdf
Last session: (none)
Wiki: 5 pages (3s/1e/1c/0x)"""
        result = parse_hook_output(output)

        assert result["pending_files"] == ["half-done.pdf"]
        assert result["has_work"] is True

    def test_multiple_new_files(self):
        output = """=== KB Status ===
New files in raw/: a.pdf, b.md, c.txt
Last session: (none)
Wiki: 0 pages (0s/0e/0c/0x)"""
        result = parse_hook_output(output)

        assert len(result["new_files"]) == 3
        assert result["new_files"] == ["a.pdf", "b.md", "c.txt"]

    def test_action_line_captured(self):
        output = """=== KB Status ===
New files in raw/: paper.pdf
ACTION: Compile these files now. Use /kb-compile or say "compile the new files"."""
        result = parse_hook_output(output)

        assert result["action"] is not None
        assert "ACTION" in result["action"]
