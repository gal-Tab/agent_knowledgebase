"""Tests for resolve_candidates (tools/resolve_candidates.py)."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from resolve_candidates import parse_extracted_references, deduplicate_candidates


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


class TestDeduplicateCandidates:
    def test_merges_same_entity_from_two_sources(self, source_with_refs, source_with_refs_2):
        c1 = parse_extracted_references(source_with_refs, "attention-paper")
        c2 = parse_extracted_references(source_with_refs_2, "efficient-inference")
        deduped = deduplicate_candidates(c1 + c2)
        openai = [d for d in deduped if d["slug"] == "openai"]
        assert len(openai) == 1
        assert len(openai[0]["sources"]) == 2
        assert "attention-paper" in openai[0]["sources"]
        assert "efficient-inference" in openai[0]["sources"]

    def test_merges_same_concept_from_two_sources(self, source_with_refs, source_with_refs_2):
        c1 = parse_extracted_references(source_with_refs, "attention-paper")
        c2 = parse_extracted_references(source_with_refs_2, "efficient-inference")
        deduped = deduplicate_candidates(c1 + c2)
        scaling = [d for d in deduped if d["slug"] == "scaling-laws"]
        assert len(scaling) == 1
        assert len(scaling[0]["sources"]) == 2

    def test_unique_candidates_not_merged(self, source_with_refs, source_with_refs_2):
        c1 = parse_extracted_references(source_with_refs, "attention-paper")
        c2 = parse_extracted_references(source_with_refs_2, "efficient-inference")
        deduped = deduplicate_candidates(c1 + c2)
        google = [d for d in deduped if d["slug"] == "google-brain"]
        meta = [d for d in deduped if d["slug"] == "meta-ai"]
        assert len(google) == 1
        assert len(meta) == 1

    def test_preserves_all_descriptions(self, source_with_refs, source_with_refs_2):
        c1 = parse_extracted_references(source_with_refs, "attention-paper")
        c2 = parse_extracted_references(source_with_refs_2, "efficient-inference")
        deduped = deduplicate_candidates(c1 + c2)
        openai = [d for d in deduped if d["slug"] == "openai"][0]
        assert len(openai["descriptions"]) == 2

    def test_empty_input(self):
        assert deduplicate_candidates([]) == []

    def test_single_candidate(self, source_with_refs):
        c = parse_extracted_references(source_with_refs, "attention-paper")[:1]
        deduped = deduplicate_candidates(c)
        assert len(deduped) == 1
        assert len(deduped[0]["sources"]) == 1
