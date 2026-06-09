"""Tests for the learn-capture compoundable-moment detector (lib/learning_capture.py).

The Stop hook `hooks/learn-capture` is thin glue (guard on .compound/, gather recent
git subjects + a transcript tail, stage at most one draft stub per session). The
conservative detection — does this session contain a compoundable moment, and of
what type — lives here and is unit-tested, mirroring lib/learning_surface.

Detection is deliberately conservative: explicit user-correction language is the
strongest signal (a correction), a user-blessed procedure is a playbook, and a
bug→fix arc in recent commits is an insight. Priority: correction > playbook >
insight. No signal → None (the common case → the hook does nothing).
"""
import json

from lib.learning_capture import (
    detect_signal,
    scan_transcript,
    scan_git_subjects,
    extract_user_text,
)


class TestScanTranscript:
    def test_user_correction_language(self):
        assert scan_transcript("No, that's wrong — use a set instead.") == "correction"

    def test_blessed_procedure(self):
        assert scan_transcript("nice, that worked! ship it") == "playbook"

    def test_neutral_text(self):
        assert scan_transcript("Here is the function you asked for.") is None

    def test_case_insensitive(self):
        assert scan_transcript("DON'T DO THAT again") == "correction"

    def test_empty(self):
        assert scan_transcript("") is None


class TestScanGitSubjects:
    def test_fix_commit_matches(self):
        assert scan_git_subjects(["fix: handle empty input", "add feature"]) is True

    def test_revert_matches(self):
        assert scan_git_subjects(["revert botched migration"]) is True

    def test_no_fix(self):
        assert scan_git_subjects(["add feature", "docs: update readme"]) is False

    def test_word_boundary_not_substring(self):
        # "prefix" / "suffix" contain "fix" but are not fix commits
        assert scan_git_subjects(["prefix the labels", "suffix tweak"]) is False

    def test_empty(self):
        assert scan_git_subjects([]) is False


class TestExtractUserText:
    """Only the human's typed text should feed detection — not the assistant's
    own words (which may quote correction phrases) and not tool output."""

    def _line(self, role, content):
        return json.dumps({"type": role, "message": {"role": role, "content": content}})

    def test_user_string_content(self):
        text = self._line("user", "no, that's wrong")
        assert "no, that's wrong" in extract_user_text(text)

    def test_user_text_blocks(self):
        text = self._line("user", [{"type": "text", "text": "don't do that"}])
        assert "don't do that" in extract_user_text(text)

    def test_assistant_text_excluded(self):
        text = self._line("assistant", [{"type": "text", "text": "that's wrong, I'll fix it"}])
        assert extract_user_text(text) == ""

    def test_tool_result_blocks_excluded(self):
        # tool results carry role "user" in the API but are not human text
        text = self._line("user", [{"type": "tool_result", "content": "that worked"}])
        assert extract_user_text(text) == ""

    def test_malformed_line_skipped(self):
        good = self._line("user", "actually no, that's not right")
        text = "{partial truncated json\n" + good
        assert "that's not right" in extract_user_text(text)

    def test_empty(self):
        assert extract_user_text("") == ""

    def test_only_user_turns_reach_detection(self):
        # assistant says a correction phrase; user does not -> no signal
        transcript = "\n".join([
            self._line("assistant", [{"type": "text", "text": "no, that's wrong"}]),
            self._line("user", [{"type": "text", "text": "great, thanks"}]),
        ])
        assert scan_transcript(extract_user_text(transcript)) is None


class TestDetectSignal:
    def test_none_when_no_signal(self):
        assert detect_signal([], "just some neutral chatter") is None

    def test_correction_from_transcript(self):
        sig = detect_signal([], "actually no, that's wrong")
        assert sig["type"] == "correction"
        assert sig["signal"] == "user-correction"

    def test_playbook_from_blessed(self):
        sig = detect_signal([], "that worked, perfect")
        assert sig["type"] == "playbook"

    def test_insight_from_fix_commit(self):
        sig = detect_signal(["fix: race condition in cache"], "neutral text")
        assert sig["type"] == "insight"
        assert sig["signal"] == "bugfix-arc"
        assert "fix" in sig["evidence"].lower()

    def test_correction_outranks_fix_commit(self):
        sig = detect_signal(["fix: something"], "no, that's not right")
        assert sig["type"] == "correction"

    def test_blessed_outranks_fix_commit(self):
        sig = detect_signal(["fix: something"], "that worked great")
        assert sig["type"] == "playbook"
