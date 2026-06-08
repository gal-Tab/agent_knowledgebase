"""End-to-end tests for the kw-capture Stop hook *script* (hooks/kw-capture).

The pure detector is covered by tests/test_kw_capture_hook.py; this exercises the
bash glue itself — the opt-in guard, the once-per-session throttle, draft staging,
and (via the real script) that only the user's transcript text drives detection.
Mirrors the subprocess style of tests/test_learning_write.py.
"""
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
HOOK = PROJECT_ROOT / "hooks" / "kw-capture"


def _jsonl(*entries) -> str:
    return "\n".join(
        json.dumps({"type": role, "message": {"role": role, "content": content}})
        for role, content in entries
    )


def _run(project_dir: Path, tmpdir: Path, payload: dict):
    # TMPDIR always exists in practice; create it so the throttle marker can write.
    tmpdir.mkdir(parents=True, exist_ok=True)
    (tmpdir / "home").mkdir(parents=True, exist_ok=True)
    env = {
        "PATH": __import__("os").environ.get("PATH", ""),
        "HOME": str(tmpdir / "home"),
        "CLAUDE_PROJECT_DIR": str(project_dir),
        "CLAUDE_PLUGIN_ROOT": str(PROJECT_ROOT),
        "TMPDIR": str(tmpdir),
    }
    return subprocess.run(
        ["bash", str(HOOK), "stop"],
        input=json.dumps(payload),
        capture_output=True, text=True, env=env,
    )


def _drafts(project_dir: Path):
    d = project_dir / ".compound" / ".drafts"
    return sorted(d.glob("auto-*.md")) if d.exists() else []


def test_no_store_exits_silently(tmp_path):
    proc = _run(tmp_path, tmp_path / "t", {"session_id": "s1", "transcript_path": ""})
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
    assert _drafts(tmp_path) == []


def test_correction_stages_one_stub(tmp_path):
    (tmp_path / ".compound").mkdir()
    tr = tmp_path / "transcript.jsonl"
    tr.write_text(_jsonl(("user", "no, that's wrong, use a set instead")))
    proc = _run(tmp_path, tmp_path / "t", {"session_id": "s2", "transcript_path": str(tr)})
    assert proc.returncode == 0
    drafts = _drafts(tmp_path)
    assert len(drafts) == 1
    assert "type: correction" in drafts[0].read_text()
    assert "/kw-compound --review" in proc.stdout


def test_throttled_to_one_per_session(tmp_path):
    (tmp_path / ".compound").mkdir()
    tr = tmp_path / "transcript.jsonl"
    tr.write_text(_jsonl(("user", "no, that's wrong")))
    tmpdir = tmp_path / "t"
    payload = {"session_id": "s3", "transcript_path": str(tr)}
    _run(tmp_path, tmpdir, payload)
    _run(tmp_path, tmpdir, payload)  # same session marker dir
    assert len(_drafts(tmp_path)) == 1


def test_neutral_transcript_no_stub(tmp_path):
    (tmp_path / ".compound").mkdir()
    tr = tmp_path / "transcript.jsonl"
    tr.write_text(_jsonl(("user", "please add a helper function")))
    proc = _run(tmp_path, tmp_path / "t", {"session_id": "s4", "transcript_path": str(tr)})
    assert proc.returncode == 0
    assert _drafts(tmp_path) == []


def test_assistant_correction_phrase_does_not_trigger(tmp_path):
    # role filtering: the assistant quoting a correction phrase must NOT stage a draft
    (tmp_path / ".compound").mkdir()
    tr = tmp_path / "transcript.jsonl"
    tr.write_text(_jsonl(
        ("assistant", [{"type": "text", "text": "you might say no, that's wrong"}]),
        ("user", [{"type": "text", "text": "thanks, looks great"}]),
    ))
    proc = _run(tmp_path, tmp_path / "t", {"session_id": "s5", "transcript_path": str(tr)})
    assert proc.returncode == 0
    assert _drafts(tmp_path) == []
