"""Storage for compound learnings (the learn-* / compound subsystem).

Two tiers, identical layout (this module parameterizes over `root`):

  <project>/.compound/                  # primary, committed, team-shareable
  ~/.claude/compound-knowledge/         # global, opt-in, curated, git-init'd

Each store holds one markdown file per learning under a per-type directory,
plus `.archive/` for superseded learnings and `.drafts/` for un-approved
captures. Retrieval merges both tiers; the project tier shadows global on id
collision.

Writes go through `write_learning` / `edit_learning`, which validate via
lib/learning_format and refuse to persist invalid content — the same gate
lib/page_writer applies to wiki pages. Archival mirrors lib/quarantine's
move-aside + JSON sidecar mechanic (archive, never delete).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from lib.learning_format import validate_learning
from lib.page_format import ValidationResult, parse_frontmatter
from lib.slug import slug_learning

# learning type → directory name within a store.
TYPE_DIRS = {
    "insight": "insights",
    "playbook": "playbooks",
    "correction": "corrections",
    "pattern": "patterns",
}

PROJECT_DIRNAME = ".compound"
ARCHIVE_DIRNAME = ".archive"
DRAFTS_DIRNAME = ".drafts"

# Env var to relocate the global store (defaults to ~/.claude/compound-knowledge).
GLOBAL_HOME_ENV = "COMPOUND_KNOWLEDGE_HOME"


def global_root() -> Path:
    """Resolve the global (cross-project) store root.

    Honours $COMPOUND_KNOWLEDGE_HOME; otherwise ~/.claude/compound-knowledge.
    """
    override = os.environ.get(GLOBAL_HOME_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "compound-knowledge"


def project_root(project_dir: Path | str) -> Path:
    """The project store root: <project_dir>/.compound."""
    return Path(project_dir) / PROJECT_DIRNAME


def resolve_stores(project_dir: Path | str) -> list[tuple[str, Path]]:
    """Return existing stores as (scope, root), project first then global.

    A store that does not exist on disk is omitted — retrieval over the result
    is therefore zero-cost when nothing has been captured.
    """
    stores: list[tuple[str, Path]] = []
    proj = project_root(project_dir)
    if proj.exists():
        stores.append(("project", proj))
    glob = global_root()
    if glob.exists():
        stores.append(("global", glob))
    return stores


def learning_id(headline: str, date: str) -> str:
    """Build a stable learning id: kw-{date}-{slug}."""
    return f"kw-{date}-{slug_learning(headline)}"


def _type_dir(learning_type: str) -> str:
    if learning_type not in TYPE_DIRS:
        raise ValueError(
            f"unknown learning type '{learning_type}', must be one of {sorted(TYPE_DIRS)}"
        )
    return TYPE_DIRS[learning_type]


def dest_path(root: Path | str, content: str) -> Path:
    """Derive the destination path for a learning from its frontmatter.

    `root/<type-dir>/<id>.md`. Raises ValueError if type/id are missing or the
    type is unknown — callers should validate first (write_learning does).
    """
    fm = parse_frontmatter(content)
    learning_type = fm.get("type")
    lid = fm.get("id")
    if not lid:
        raise ValueError("learning is missing 'id' frontmatter")
    return Path(root) / _type_dir(learning_type) / f"{lid}.md"


def write_learning(root: Path | str, content: str) -> ValidationResult:
    """Validate `content` then write it to the derived path under `root`.

    On validation failure nothing is written and any existing file is left
    untouched. The store self-creates its type directory on success.
    """
    result = validate_learning(content)
    if not result.ok:
        return result

    path = dest_path(root, content)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return result


def edit_learning(path: Path | str, old_string: str, new_string: str) -> ValidationResult:
    """Apply a single string substitution to a learning file and re-validate.

    Refuses (leaving the file untouched) if the file is missing, `old_string`
    is absent or ambiguous, or the post-edit content fails validation.
    """
    path = Path(path)
    if not path.exists():
        return ValidationResult(ok=False, errors=[f"file does not exist: {path}"], warnings=[])

    current = path.read_text()
    occurrences = current.count(old_string)
    if occurrences == 0:
        return ValidationResult(ok=False, errors=[f"old_string not found in {path}"], warnings=[])
    if occurrences > 1:
        return ValidationResult(
            ok=False,
            errors=[f"ambiguous edit: old_string appears {occurrences} times in {path}"],
            warnings=[],
        )

    new_content = current.replace(old_string, new_string, 1)
    result = validate_learning(new_content)
    if not result.ok:
        return result

    path.write_text(new_content)
    return result


def archive_path_for(root: Path | str, learning_type: str, lid: str) -> Path:
    """Map an active learning to its archive location.

    root/<type-dir>/<id>.md → root/.archive/<type-dir>/<id>.md
    """
    return Path(root) / ARCHIVE_DIRNAME / _type_dir(learning_type) / f"{lid}.md"


def move_to_archive(
    root: Path | str,
    learning_type: str,
    lid: str,
    reason: str,
    superseded_by: str | None = None,
) -> Path:
    """Move an active learning into `.archive/` with a JSON sidecar.

    Archive, never delete: the body is preserved for audit but drops out of the
    active index. Mirrors lib/quarantine.move_to_quarantine.
    """
    src = Path(root) / _type_dir(learning_type) / f"{lid}.md"
    content = src.read_text()

    dst = archive_path_for(root, learning_type, lid)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content)

    sidecar = dst.with_suffix(".archive.json")
    sidecar.write_text(
        json.dumps(
            {
                "original_path": str(src),
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "superseded_by": superseded_by,
            },
            indent=2,
        )
    )
    src.unlink()
    return dst


def merge_learnings(
    project_items: list[dict],
    global_items: list[dict],
    key: str = "id",
) -> list[dict]:
    """Merge two tiers of learning records, project shadowing global on `key`.

    Items are plain dicts (e.g. parsed index entries). Project items win on
    collision; global items with a colliding key are dropped.
    """
    seen = {item[key] for item in project_items}
    return list(project_items) + [item for item in global_items if item[key] not in seen]
