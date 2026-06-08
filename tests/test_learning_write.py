"""Tests for the validate-write-index CLI (tools/learning_write.py)."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

VALID = (
    "---\n"
    "id: kw-2026-06-08-jitter\n"
    "type: correction\n"
    "scope: project\n"
    'headline: "Add jitter to retry backoff"\n'
    "tags: [retries]\n"
    "confidence: STATED\n"
    "created: 2026-06-08\n"
    "updated: 2026-06-08\n"
    "status: active\n"
    "---\n"
    "\n## Learning\nx\n\n## Context\ny\n\n## Implication\nz\n"
)
INVALID = VALID.replace("type: correction", "type: rumor")


def _run(*args):
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "learning_write.py"), *args],
        capture_output=True, text=True,
    )


def test_valid_learning_written_and_indexed(tmp_path):
    root = tmp_path / ".compound"
    draft = tmp_path / "draft.md"
    draft.write_text(VALID)

    proc = _run(str(draft), "--root", str(root))
    assert proc.returncode == 0, proc.stderr
    assert (root / "corrections" / "kw-2026-06-08-jitter.md").exists()
    assert "kw-2026-06-08-jitter" in (root / "index.md").read_text()


def test_invalid_learning_writes_nothing(tmp_path):
    root = tmp_path / ".compound"
    draft = tmp_path / "draft.md"
    draft.write_text(INVALID)

    proc = _run(str(draft), "--root", str(root))
    assert proc.returncode == 1
    assert "INVALID" in proc.stderr
    assert not (root.exists() and any(root.rglob("*.md")))
