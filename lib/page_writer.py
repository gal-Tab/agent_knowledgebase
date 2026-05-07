"""Validating wrapper around wiki page writes.

Every pipeline write to wiki/ should go through `write_page` or `edit_page`.
The functions validate the post-write content against schema rules and refuse
to persist invalid pages — the existing file (if any) is left untouched.

Callers handle the failure: typically retry the resolver with the validation
errors as feedback (one-shot), and quarantine on second failure (see
lib/quarantine.py).
"""
from __future__ import annotations

from pathlib import Path

from lib.page_format import ValidationResult, validate_page

# wiki/<dir> → page_type
_DIR_TO_TYPE = {
    "sources": "source",
    "entities": "entity",
    "concepts": "concept",
    "comparisons": "comparison",
}


def infer_page_type(path: Path | str) -> str:
    """Derive page_type from a wiki/<dir>/<slug>.md path.

    Raises ValueError if the parent directory is not one of the known
    wiki page directories.
    """
    parent = Path(path).parent.name
    if parent not in _DIR_TO_TYPE:
        raise ValueError(
            f"cannot infer page type from path '{path}': parent directory "
            f"'{parent}' is not one of {sorted(_DIR_TO_TYPE)}"
        )
    return _DIR_TO_TYPE[parent]


def write_page(
    path: Path | str,
    content: str,
    page_type: str | None = None,
) -> ValidationResult:
    """Validate `content` then write to `path` if valid.

    On validation failure, the file at `path` is left untouched (if it exists)
    and the new content is not written. The returned ValidationResult carries
    the errors for the caller to feed back into a retry or to quarantine.
    """
    path = Path(path)
    if page_type is None:
        page_type = infer_page_type(path)

    result = validate_page(content, page_type)
    if not result.ok:
        return result

    path.write_text(content)
    return result


def edit_page(
    path: Path | str,
    old_string: str,
    new_string: str,
    page_type: str | None = None,
) -> ValidationResult:
    """Apply a single string substitution and validate the result.

    Refuses to apply the edit if:
      - the file does not exist
      - `old_string` does not appear in the file
      - `old_string` appears more than once (ambiguous)
      - the post-edit content fails validation

    The file on disk is unchanged if any of the above hold.
    """
    path = Path(path)
    if page_type is None:
        page_type = infer_page_type(path)

    if not path.exists():
        return ValidationResult(
            ok=False,
            errors=[f"file does not exist: {path}"],
            warnings=[],
        )

    current = path.read_text()
    occurrences = current.count(old_string)
    if occurrences == 0:
        return ValidationResult(
            ok=False,
            errors=[f"old_string not found in {path}"],
            warnings=[],
        )
    if occurrences > 1:
        return ValidationResult(
            ok=False,
            errors=[
                f"ambiguous edit: old_string appears {occurrences} times in {path} "
                f"(must be unique)"
            ],
            warnings=[],
        )

    new_content = current.replace(old_string, new_string, 1)
    result = validate_page(new_content, page_type)
    if not result.ok:
        return result

    path.write_text(new_content)
    return result
