"""Quarantine for wiki pages that fail validation after the retry budget.

When a resolver write fails validation twice (initial + one retry), the
content is moved to `wiki/.quarantine/{category}/{slug}.md` with a sidecar
`.errors.json` describing the failure. The original target path is left
untouched so the existing wiki state stays consistent.

`kb-status` surfaces the quarantine count at session start so users see the
backlog. `recover_from_quarantine` re-validates a quarantined page after
manual fixing and moves it back into place when valid.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lib.page_format import ValidationResult, validate_page
from lib.page_writer import infer_page_type

QUARANTINE_DIRNAME = ".quarantine"


def _quarantine_path_for(target: Path, wiki_root: Path) -> Path:
    """Map wiki/<category>/<slug>.md → wiki/.quarantine/<category>/<slug>.md."""
    category = target.parent.name
    return wiki_root / QUARANTINE_DIRNAME / category / target.name


def move_to_quarantine(
    target: Path,
    content: str,
    errors: list[str],
    wiki_root: Path,
) -> Path:
    """Persist failing content under wiki/.quarantine/ with an errors sidecar.

    Does NOT modify the original target path — if it exists, it remains as is.
    Returns the path the content was written to.
    """
    q_path = _quarantine_path_for(target, wiki_root)
    q_path.parent.mkdir(parents=True, exist_ok=True)
    q_path.write_text(content)

    sidecar = q_path.with_suffix(".errors.json")
    payload = {
        "original_path": str(target),
        "quarantined_at": datetime.now(timezone.utc).isoformat(),
        "errors": list(errors),
    }
    sidecar.write_text(json.dumps(payload, indent=2))
    return q_path


def count_quarantined(wiki_root: Path) -> int:
    """Count quarantined wiki pages (md files only, not sidecars)."""
    qdir = wiki_root / QUARANTINE_DIRNAME
    if not qdir.exists():
        return 0
    return sum(1 for _ in qdir.rglob("*.md"))


def list_quarantined(wiki_root: Path) -> list[Path]:
    """Return paths of all quarantined wiki pages."""
    qdir = wiki_root / QUARANTINE_DIRNAME
    if not qdir.exists():
        return []
    return sorted(qdir.rglob("*.md"))


def recover_from_quarantine(q_path: Path, wiki_root: Path) -> ValidationResult:
    """Re-validate a quarantined file and move it back to its target on success.

    The target path is reconstructed from the quarantine path's category +
    filename — i.e. `wiki/.quarantine/entities/foo.md` recovers to
    `wiki/entities/foo.md`. On validation failure, nothing moves: the
    quarantined file remains in place for further manual fixing.
    """
    content = q_path.read_text()
    category = q_path.parent.name
    target = wiki_root / category / q_path.name

    page_type = infer_page_type(target)
    result = validate_page(content, page_type)
    if not result.ok:
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    q_path.unlink()
    sidecar = q_path.with_suffix(".errors.json")
    if sidecar.exists():
        sidecar.unlink()
    return result
