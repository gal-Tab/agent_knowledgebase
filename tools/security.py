"""Security utilities for LLM Wiki Agent.

Path validation, slug sanitization, content size limits, and gitignore audit.
"""
import os
import re
from pathlib import Path


def validate_wiki_path(path: str, wiki_root: str) -> bool:
    """Verify that a resolved path is inside the wiki directory.

    Prevents path traversal attacks (../../etc/passwd).
    Returns True if safe, raises ValueError if not.
    """
    resolved = os.path.realpath(path)
    wiki_resolved = os.path.realpath(wiki_root)
    if not resolved.startswith(wiki_resolved + os.sep) and resolved != wiki_resolved:
        raise ValueError(
            f"Path escapes wiki directory: {path!r} resolves to {resolved!r}, "
            f"which is outside {wiki_resolved!r}"
        )
    return True


def sanitize_slug(raw_name: str) -> str:
    """Sanitize a string into a safe filesystem slug.

    - Lowercase
    - Replace spaces/underscores with hyphens
    - Remove characters outside [a-z0-9-]
    - Collapse multiple hyphens
    - Strip leading/trailing hyphens
    - Truncate to 80 characters
    - Reject empty results
    """
    if not raw_name or not raw_name.strip():
        raise ValueError("Input cannot be empty")
    slug = raw_name.lower()
    slug = re.sub(r"[\s_/]+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    slug = slug[:80].rstrip("-")
    if not slug:
        raise ValueError(f"Input produces empty slug: {raw_name!r}")
    return slug


def check_file_size(path: str, max_mb: float = 1.0) -> dict:
    """Check if a file exceeds size limits.

    Returns dict with: path, size_mb, exceeds_limit, warning.
    """
    size_bytes = os.path.getsize(path)
    size_mb = size_bytes / (1024 * 1024)
    exceeds = size_mb > max_mb
    warning = None
    if exceeds:
        warning = f"File {path!r} is {size_mb:.2f}MB, exceeds {max_mb}MB limit"
    return {
        "path": path,
        "size_mb": round(size_mb, 4),
        "exceeds_limit": exceeds,
        "warning": warning,
    }


def audit_gitignore(project_root: str) -> list[str]:
    """Audit .gitignore for security-relevant patterns.

    Returns list of missing patterns that should be added.
    """
    gitignore_path = os.path.join(project_root, ".gitignore")
    expected_patterns = [
        "*.pdf",
        "raw/.extracted/",
        ".env",
    ]

    if not os.path.exists(gitignore_path):
        return expected_patterns

    with open(gitignore_path, "r") as f:
        content = f.read()

    lines = {line.strip() for line in content.split("\n")}
    missing = []
    for pattern in expected_patterns:
        if pattern not in lines:
            missing.append(pattern)
    return missing


def validate_manifest_entry(entry: dict) -> list[str]:
    """Validate a manifest entry for security concerns.

    Checks:
    - filename doesn't contain path traversal
    - status is a valid value
    - sha256 looks like a valid hash (64 hex chars)
    Returns list of issues found.
    """
    issues = []
    valid_statuses = {"new", "extracted", "compiled", "failed"}

    status = entry.get("status")
    if status and status not in valid_statuses:
        issues.append(f"Invalid status: {status!r}")

    sha = entry.get("sha256")
    if sha and not re.match(r"^[a-f0-9]{64}$", sha):
        issues.append(f"Invalid sha256 hash: {sha!r}")

    source_page = entry.get("source_page")
    if source_page and (".." in source_page or source_page.startswith("/")):
        issues.append(f"Suspicious source_page path: {source_page!r}")

    return issues


if __name__ == "__main__":
    import tempfile

    print("Running security self-tests...\n")
    passed = 0
    failed = 0

    # Test 1: validate_wiki_path — safe path
    try:
        with tempfile.TemporaryDirectory() as td:
            wiki = os.path.join(td, "wiki")
            os.makedirs(wiki)
            safe = os.path.join(wiki, "sources", "test.md")
            os.makedirs(os.path.dirname(safe))
            Path(safe).touch()
            assert validate_wiki_path(safe, wiki) is True
            print("  [PASS] validate_wiki_path: safe path accepted")
            passed += 1
    except Exception as e:
        print(f"  [FAIL] validate_wiki_path safe: {e}")
        failed += 1

    # Test 2: validate_wiki_path — traversal blocked
    try:
        with tempfile.TemporaryDirectory() as td:
            wiki = os.path.join(td, "wiki")
            os.makedirs(wiki)
            bad = os.path.join(wiki, "..", "etc", "passwd")
            try:
                validate_wiki_path(bad, wiki)
                print("  [FAIL] validate_wiki_path: traversal not blocked")
                failed += 1
            except ValueError:
                print("  [PASS] validate_wiki_path: traversal blocked")
                passed += 1
    except Exception as e:
        print(f"  [FAIL] validate_wiki_path traversal: {e}")
        failed += 1

    # Test 3: sanitize_slug
    try:
        assert sanitize_slug("Hello World!") == "hello-world"
        assert sanitize_slug("../../etc/passwd") == "etc-passwd"
        assert sanitize_slug("Résumé") == "rsum"  # non-ascii stripped
        print("  [PASS] sanitize_slug: basic cases")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] sanitize_slug: {e}")
        failed += 1

    # Test 4: sanitize_slug — empty input
    try:
        sanitize_slug("")
        print("  [FAIL] sanitize_slug: empty input not rejected")
        failed += 1
    except ValueError:
        print("  [PASS] sanitize_slug: empty input rejected")
        passed += 1

    # Test 5: check_file_size
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            f.write(b"x" * 1000)
            f.flush()
            result = check_file_size(f.name, max_mb=1.0)
            assert result["exceeds_limit"] is False
            os.unlink(f.name)
        print("  [PASS] check_file_size: small file OK")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] check_file_size: {e}")
        failed += 1

    # Test 6: validate_manifest_entry
    try:
        issues = validate_manifest_entry({
            "status": "compiled",
            "sha256": "a" * 64,
            "source_page": "wiki/sources/test.md",
        })
        assert issues == []

        issues = validate_manifest_entry({
            "status": "bogus",
            "sha256": "not-a-hash",
            "source_page": "../../etc/passwd",
        })
        assert len(issues) == 3
        print("  [PASS] validate_manifest_entry: valid and invalid entries")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] validate_manifest_entry: {e}")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        exit(1)
    print("All security self-tests passed.")
