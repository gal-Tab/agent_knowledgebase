"""Shared pytest fixtures for LLM Wiki Agent tests."""
import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_manifest():
    """Load the sample manifest fixture."""
    with open(FIXTURES_DIR / "sample_manifest.json") as f:
        return json.load(f)


@pytest.fixture
def sample_source_page():
    """Load the sample source page fixture."""
    return (FIXTURES_DIR / "sample_source_page.md").read_text()


@pytest.fixture
def sample_entity_page():
    """Load the sample entity page fixture."""
    return (FIXTURES_DIR / "sample_entity_page.md").read_text()


@pytest.fixture
def sample_concept_page():
    """Load the sample concept page fixture."""
    return (FIXTURES_DIR / "sample_concept_page.md").read_text()


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project structure with raw/ and wiki/ directories."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / ".extracted").mkdir()
    wiki_dir = tmp_path / "wiki"
    for subdir in ("sources", "entities", "concepts", "comparisons"):
        (wiki_dir / subdir).mkdir(parents=True)
    return tmp_path
