"""Compoundable-moment detection for the kw-capture Stop hook.

A Stop hook fires at the end of *every* turn, so detection must be cheap and
conservative — most turns contain no durable lesson and must yield nothing. When
a signal *is* present, the hook stages a single draft stub for later approval via
`/kw-compound --review`; it never writes a real learning and never touches the
index. (Approval-gated capture is the locked design.)

Signals, strongest first:
- **correction** — explicit user-correction language in the transcript ("no,
  that's wrong", "don't do that"). The highest-value lesson: a mistake not to
  repeat.
- **playbook** — a user-blessed procedure ("that worked", "ship it").
- **insight** — a bug→fix arc visible in recent commit subjects (fix/revert).

The bash hook gathers recent git subjects + a transcript tail and calls
`detect_signal`; this module owns the (testable) decision.
"""
from __future__ import annotations

import re

# Lowercased substrings that signal the user correcting the agent.
_CORRECTION_PHRASES = (
    "no, that's wrong",
    "that's wrong",
    "that's not right",
    "that's incorrect",
    "that's not what",
    "not what i asked",
    "don't do that",
    "do not do that",
    "you should have",
    "you shouldn't have",
    "undo that",
    "revert that",
    "stop doing that",
    "that's a mistake",
)

# Lowercased substrings that signal the user blessing a procedure/result.
_BLESSED_PHRASES = (
    "that worked",
    "works now",
    "ship it",
    "lgtm",
    "that's exactly",
    "exactly right",
    "that did it",
    "perfect, ship",
)

# Bug→fix arc in commit subjects (word-boundaried so "prefix"/"suffix" don't hit).
_FIX_RE = re.compile(
    r"\b(fix|fixes|fixed|fixing|revert|reverts|reverted|bugfix|hotfix)\b",
    re.IGNORECASE,
)


def scan_transcript(text: str) -> str | None:
    """Return 'correction', 'playbook', or None from transcript text.

    Correction language outranks blessing language when both appear.
    """
    if not text:
        return None
    low = text.lower()
    if any(p in low for p in _CORRECTION_PHRASES):
        return "correction"
    if any(p in low for p in _BLESSED_PHRASES):
        return "playbook"
    return None


def scan_git_subjects(subjects: list[str]) -> bool:
    """Whether recent commit subjects show a bug→fix arc."""
    return any(_FIX_RE.search(s or "") for s in (subjects or []))


def detect_signal(git_subjects: list[str], transcript_text: str) -> dict | None:
    """Detect a single compoundable moment, or None.

    Priority: user-correction (correction) > blessed-procedure (playbook) >
    bugfix-arc (insight). Returns {type, signal, evidence} for the bash hook to
    stamp into a draft stub.
    """
    kind = scan_transcript(transcript_text)
    if kind == "correction":
        return {"type": "correction", "signal": "user-correction",
                "evidence": "explicit user-correction language in this session"}
    if kind == "playbook":
        return {"type": "playbook", "signal": "blessed-procedure",
                "evidence": "user blessed a procedure/result in this session"}

    if scan_git_subjects(git_subjects):
        hit = next((s for s in git_subjects if _FIX_RE.search(s or "")), "")
        return {"type": "insight", "signal": "bugfix-arc",
                "evidence": f"bug→fix arc in recent commit: {hit.strip()}"}

    return None


def main():
    """Thin CLI for the bash hook: signals come via env, result printed TSV.

    Reads KW_GIT (newline-separated commit subjects) and KW_TRANSCRIPT (text);
    prints "<type>\\t<signal>\\t<evidence>" if a moment is detected, else nothing.
    """
    import os
    import sys

    subjects = [s for s in (os.environ.get("KW_GIT", "").splitlines()) if s.strip()]
    transcript = os.environ.get("KW_TRANSCRIPT", "")
    sig = detect_signal(subjects, transcript)
    if not sig:
        sys.exit(0)
    print(f"{sig['type']}\t{sig['signal']}\t{sig['evidence']}")


if __name__ == "__main__":
    main()
