"""Tests for tools/validate_wiki.py."""
import subprocess
import sys
from pathlib import Path

import pytest

# Import the module under test by path so we can call its functions directly.
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
import validate_wiki  # noqa: E402

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "tools" / "validate_wiki.py"


VALID_ENTITY = (
    "---\n"
    "title: Test\n"
    "type: entity\n"
    "source_refs:\n"
    "  - slug: paper-x\n"
    "    confidence: STATED\n"
    "created: 2026-05-01\n"
    "updated: 2026-05-01\n"
    "---\n"
    "\n"
    "## See Also\n"
    "- [Other](../entities/other.md) [STATED]\n"
)

INVALID_ENTITY = VALID_ENTITY.replace(
    "  - slug: paper-x\n    confidence: STATED\n",
    "  - paper-x\n",
)


@pytest.fixture
def wiki_root(tmp_path):
    wiki = tmp_path / "wiki"
    for d in ("sources", "entities", "concepts", "comparisons"):
        (wiki / d).mkdir(parents=True)
    return wiki


class TestValidatePaths:
    def test_returns_ok_for_valid_files(self, wiki_root):
        p = wiki_root / "entities" / "good.md"
        p.write_text(VALID_ENTITY)
        results = validate_wiki.validate_paths([p])
        assert results[p].ok

    def test_returns_errors_for_invalid_files(self, wiki_root):
        p = wiki_root / "entities" / "bad.md"
        p.write_text(INVALID_ENTITY)
        results = validate_wiki.validate_paths([p])
        assert not results[p].ok
        assert len(results[p].errors) > 0

    def test_skips_non_md_files(self, wiki_root):
        p = wiki_root / "entities" / "notes.txt"
        p.write_text("plain text")
        results = validate_wiki.validate_paths([p])
        assert p not in results

    def test_skips_paths_outside_known_categories(self, wiki_root):
        p = wiki_root / "random" / "x.md"
        p.parent.mkdir()
        p.write_text(VALID_ENTITY)
        results = validate_wiki.validate_paths([p])
        # No category → not validatable, silently skipped.
        assert p not in results


class TestDiscoverWikiPaths:
    def test_walks_wiki_root(self, wiki_root):
        (wiki_root / "entities" / "a.md").write_text(VALID_ENTITY)
        (wiki_root / "concepts" / "b.md").write_text(VALID_ENTITY)
        paths = validate_wiki.discover_wiki_paths(wiki_root)
        assert len(paths) == 2

    def test_excludes_quarantine(self, wiki_root):
        (wiki_root / "entities" / "a.md").write_text(VALID_ENTITY)
        (wiki_root / ".quarantine" / "entities").mkdir(parents=True)
        (wiki_root / ".quarantine" / "entities" / "bad.md").write_text(INVALID_ENTITY)
        paths = validate_wiki.discover_wiki_paths(wiki_root)
        assert len(paths) == 1

    def test_excludes_index_md(self, wiki_root):
        # index.md is generated, has no frontmatter; not a validatable page.
        (wiki_root / "index.md").write_text("# Index\n")
        (wiki_root / "entities" / "a.md").write_text(VALID_ENTITY)
        paths = validate_wiki.discover_wiki_paths(wiki_root)
        assert all(p.name != "index.md" for p in paths)


class TestCLI:
    def _run(self, *args, cwd=None):
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            cwd=str(cwd or PROJECT_ROOT),
        )

    def test_all_valid_exits_zero(self, wiki_root):
        (wiki_root / "entities" / "a.md").write_text(VALID_ENTITY)
        proc = self._run("--all", "--root", str(wiki_root))
        assert proc.returncode == 0, proc.stderr

    def test_any_invalid_exits_nonzero(self, wiki_root):
        (wiki_root / "entities" / "a.md").write_text(VALID_ENTITY)
        (wiki_root / "entities" / "b.md").write_text(INVALID_ENTITY)
        proc = self._run("--all", "--root", str(wiki_root))
        assert proc.returncode != 0
        assert "b.md" in proc.stdout or "b.md" in proc.stderr

    def test_explicit_paths(self, wiki_root):
        good = wiki_root / "entities" / "a.md"
        good.write_text(VALID_ENTITY)
        bad = wiki_root / "entities" / "b.md"
        bad.write_text(INVALID_ENTITY)
        proc = self._run("--root", str(wiki_root), str(bad))
        assert proc.returncode != 0
        assert "b.md" in proc.stdout

    def test_explicit_paths_all_valid_exits_zero(self, wiki_root):
        good = wiki_root / "entities" / "a.md"
        good.write_text(VALID_ENTITY)
        proc = self._run("--root", str(wiki_root), str(good))
        assert proc.returncode == 0

    def test_empty_wiki_exits_zero(self, wiki_root):
        proc = self._run("--all", "--root", str(wiki_root))
        assert proc.returncode == 0
