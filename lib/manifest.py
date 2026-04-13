"""Manifest management utilities for LLM Wiki Agent.

Manages raw/.manifest.json — the pipeline state file that tracks
extraction and compilation status of each source file.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUSES = {"new", "extracted", "compiled", "failed"}


def load_manifest(path: str | Path) -> dict:
    """Load manifest from JSON file. Returns empty dict if file doesn't exist."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(path: str | Path, data: dict) -> None:
    """Save manifest to JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def add_entry(manifest: dict, filename: str, sha256: str) -> dict:
    """Add a new entry to the manifest with status='new'.

    Returns the updated manifest.
    """
    manifest[filename] = {
        "status": "new",
        "source_page": None,
        "wiki_pages": [],
        "extracted_at": None,
        "compiled_at": None,
        "sha256": sha256,
        "error": None,
    }
    return manifest


def update_status(manifest: dict, filename: str, status: str, **kwargs) -> dict:
    """Update the status of a manifest entry.

    Valid statuses: new, extracted, compiled, failed.
    Additional kwargs are merged into the entry (e.g., source_page, error).
    Returns the updated manifest.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")
    if filename not in manifest:
        raise KeyError(f"File '{filename}' not found in manifest")

    manifest[filename]["status"] = status

    # Auto-set timestamps
    now = datetime.now(timezone.utc).isoformat()
    if status == "extracted":
        manifest[filename]["extracted_at"] = now
    elif status == "compiled":
        manifest[filename]["compiled_at"] = now

    # Merge additional fields
    for key, value in kwargs.items():
        if key in manifest[filename]:
            manifest[filename][key] = value

    return manifest


def get_pending(manifest: dict) -> list[str]:
    """Get filenames that need compilation.

    Returns files with status 'new', 'extracted' (without compiled_at),
    or 'failed'.
    """
    pending = []
    for filename, entry in manifest.items():
        status = entry.get("status", "new")
        if status == "new":
            pending.append(filename)
        elif status == "extracted" and not entry.get("compiled_at"):
            pending.append(filename)
        elif status == "failed":
            pending.append(filename)
    return pending


def get_by_status(manifest: dict, status: str) -> list[str]:
    """Get filenames matching a given status."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")
    return [
        filename
        for filename, entry in manifest.items()
        if entry.get("status") == status
    ]
