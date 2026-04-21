"""Tests for resolve_candidates (tools/resolve_candidates.py)."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from resolve_candidates import parse_extracted_references


class TestParseExtractedReferences:
    def test_parses_entities(self, source_with_refs):
        candidates = parse_extracted_references(source_with_refs, "attention-paper")
        entities = [c for c in candidates if c["kind"] == "entity"]
        assert len(entities) == 3
        assert entities[0]["name"] == "Ashish Vaswani"
        assert entities[0]["entity_type"] == "person"
        assert entities[0]["source_slug"] == "attention-paper"

    def test_parses_concepts(self, source_with_refs):
        candidates = parse_extracted_references(source_with_refs, "attention-paper")
        concepts = [c for c in candidates if c["kind"] == "concept"]
        assert len(concepts) == 2
        assert concepts[0]["name"] == "Attention Mechanisms"

    def test_includes_description(self, source_with_refs):
        candidates = parse_extracted_references(source_with_refs, "attention-paper")
        assert candidates[0]["description"] == "lead author of the transformer paper"

    def test_no_refs_section_returns_empty(self):
        content = "---\ntitle: Test\n---\n\n## Overview\n\nNo refs here."
        assert parse_extracted_references(content, "test") == []

    def test_empty_content_returns_empty(self):
        assert parse_extracted_references("", "test") == []
