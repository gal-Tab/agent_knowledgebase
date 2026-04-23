"""Tests for resolve_candidates (tools/resolve_candidates.py)."""
import pytest
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from resolve_candidates import parse_extracted_references, deduplicate_candidates, classify_candidates, format_brief, batch_candidates


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


class TestClassifyCandidates:
    def _make_wiki(self, tmp_path, index_content, pages=None):
        """Helper: create a wiki dir with index and optional pages."""
        wiki = tmp_path / "wiki"
        for subdir in ("sources", "entities", "concepts", "comparisons"):
            (wiki / subdir).mkdir(parents=True, exist_ok=True)
        (wiki / "index.md").write_text(index_content)
        if pages:
            for rel_path, content in pages.items():
                p = wiki / rel_path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)
        return wiki

    def test_new_candidate_classified_as_create(self, tmp_path, sample_index):
        wiki = self._make_wiki(tmp_path, sample_index)
        candidates = [{
            "kind": "entity", "name": "Meta AI", "slug": "meta-ai",
            "entity_type": "org", "sources": ["efficient-inference"],
            "descriptions": {"efficient-inference": "developed Llama"},
        }]
        result = classify_candidates(candidates, wiki, {})
        assert len(result["create"]) == 1
        assert result["create"][0]["slug"] == "meta-ai"

    def test_existing_entity_new_source_classified_as_update(
        self, tmp_path, sample_index, sample_entity_page
    ):
        wiki = self._make_wiki(tmp_path, sample_index, {
            "entities/kaplan-jared.md": sample_entity_page,
        })
        candidates = [{
            "kind": "entity", "name": "Jared Kaplan", "slug": "kaplan-jared",
            "entity_type": "person", "sources": ["efficient-inference"],
            "descriptions": {"efficient-inference": "referenced for compute findings"},
        }]
        result = classify_candidates(candidates, wiki, {})
        assert len(result["update"]) == 1
        assert result["update"][0]["slug"] == "kaplan-jared"

    def test_existing_entity_same_source_classified_as_skip(
        self, tmp_path, sample_index, sample_entity_page
    ):
        wiki = self._make_wiki(tmp_path, sample_index, {
            "entities/kaplan-jared.md": sample_entity_page,
        })
        candidates = [{
            "kind": "entity", "name": "Jared Kaplan", "slug": "kaplan-jared",
            "entity_type": "person", "sources": ["scaling-laws-neural-lm"],
            "descriptions": {"scaling-laws-neural-lm": "lead author"},
        }]
        result = classify_candidates(candidates, wiki, {})
        assert len(result["skip"]) == 1

    def test_stale_detection(self, tmp_path, sample_index):
        wiki = self._make_wiki(tmp_path, sample_index)
        manifest = {
            "attention-paper.pdf": {
                "status": "compiled",
                "wiki_pages": [
                    "wiki/sources/attention-paper.md",
                    "wiki/entities/google-brain.md",
                ],
            }
        }
        candidates = [{
            "kind": "entity", "name": "OpenAI", "slug": "openai",
            "entity_type": "org", "sources": ["attention-paper"],
            "descriptions": {"attention-paper": "GPT series"},
        }]
        result = classify_candidates(
            candidates, wiki, manifest,
            recompiled_sources={"attention-paper": "attention-paper.pdf"},
        )
        assert len(result["stale"]) == 1
        assert "google-brain" in result["stale"][0]["slug"]

    def test_empty_candidates(self, tmp_path, sample_index):
        wiki = self._make_wiki(tmp_path, sample_index)
        result = classify_candidates([], wiki, {})
        assert result == {"create": [], "update": [], "skip": [], "stale": []}

    def test_alias_match_classifies_as_update(self, tmp_path, sample_index):
        entity_with_alias = (
            '---\ntitle: "Jared Kaplan"\ntype: entity\naliases:\n'
            '  - "J. Kaplan"\nsource_refs:\n  - "scaling-laws-neural-lm"\n'
            'created: 2026-04-01\nupdated: 2026-04-01\ntags: []\n---\n\n'
            '## Overview\n\nResearcher.\n\n## See Also\n\n'
        )
        wiki = self._make_wiki(tmp_path, sample_index, {
            "entities/kaplan-jared.md": entity_with_alias,
        })
        candidates = [{
            "kind": "entity", "name": "J. Kaplan", "slug": "kaplan-j",
            "entity_type": "person", "sources": ["new-paper"],
            "descriptions": {"new-paper": "co-author"},
        }]
        result = classify_candidates(candidates, wiki, {})
        assert len(result["update"]) == 1
        assert result["update"][0]["existing_slug"] == "kaplan-jared"


class TestFormatBrief:
    def test_create_section(self):
        classified = {
            "create": [{
                "kind": "entity", "name": "Meta AI", "slug": "meta-ai",
                "entity_type": "org", "sources": ["efficient-inference"],
                "descriptions": {"efficient-inference": "developed Llama"},
            }],
            "update": [], "skip": [], "stale": [],
        }
        brief = format_brief(classified)
        assert "## CREATE (1)" in brief
        assert "### Entity: Meta AI (org)" in brief
        assert "meta-ai" in brief
        assert "developed Llama" in brief

    def test_update_section(self):
        classified = {
            "create": [],
            "update": [{
                "kind": "entity", "name": "OpenAI", "slug": "openai",
                "entity_type": "org", "sources": ["new-paper"],
                "existing_slug": "openai", "existing_category": "entities",
                "descriptions": {"new-paper": "inference work"},
            }],
            "skip": [], "stale": [],
        }
        brief = format_brief(classified)
        assert "## UPDATE (1)" in brief
        assert "Sources adding: new-paper" in brief

    def test_stale_section(self):
        classified = {
            "create": [], "update": [], "skip": [],
            "stale": [{
                "slug": "google-brain",
                "page": "wiki/entities/google-brain.md",
                "source": "attention-paper",
                "reason": "absent from re-extraction of attention-paper",
            }],
        }
        brief = format_brief(classified)
        assert "## STALE (1)" in brief
        assert "google-brain" in brief

    def test_skip_not_in_output(self):
        classified = {
            "create": [], "update": [],
            "skip": [{"slug": "openai", "name": "OpenAI"}],
            "stale": [],
        }
        brief = format_brief(classified)
        assert "openai" not in brief.lower() or "SKIP" not in brief

    def test_all_empty_returns_empty(self):
        classified = {"create": [], "update": [], "skip": [], "stale": []}
        assert format_brief(classified) == ""


class TestBatchCandidates:
    def test_under_limits_single_batch(self):
        classified = {
            "create": [
                {"slug": f"entity-{i}", "sources": ["src-1"]}
                for i in range(5)
            ],
            "update": [], "skip": [], "stale": [],
        }
        batches = batch_candidates(classified, max_sources=5, max_candidates=30)
        assert len(batches) == 1

    def test_exceeds_candidate_cap_splits(self):
        classified = {
            "create": [
                {"slug": f"entity-{i}", "sources": [f"src-{i % 3}"]}
                for i in range(35)
            ],
            "update": [], "skip": [], "stale": [],
        }
        batches = batch_candidates(classified, max_sources=5, max_candidates=30)
        assert len(batches) >= 2
        for batch in batches:
            total = len(batch["create"]) + len(batch["update"])
            assert total <= 30

    def test_stale_only_in_first_batch(self):
        classified = {
            "create": [
                {"slug": f"entity-{i}", "sources": [f"src-{i % 3}"]}
                for i in range(35)
            ],
            "update": [], "skip": [],
            "stale": [{"slug": "old", "page": "wiki/entities/old.md"}],
        }
        batches = batch_candidates(classified, max_sources=5, max_candidates=30)
        assert len(batches[0]["stale"]) == 1
        for batch in batches[1:]:
            assert len(batch["stale"]) == 0


class TestCLI:
    def test_runs_and_outputs_brief(self, tmp_path, source_with_refs, sample_index):
        wiki = tmp_path / "wiki"
        for subdir in ("sources", "entities", "concepts"):
            (wiki / subdir).mkdir(parents=True)
        (wiki / "index.md").write_text(sample_index)

        results_dir = tmp_path / "raw" / ".compile-results"
        results_dir.mkdir(parents=True)

        (wiki / "sources" / "attention-paper.md").write_text(source_with_refs)

        import json
        result_json = {
            "source_file": "attention-paper.pdf",
            "slug": "attention-paper",
            "source_page": "wiki/sources/attention-paper.md",
            "status": "success",
        }
        (results_dir / "attention-paper.json").write_text(json.dumps(result_json))

        manifest = tmp_path / "raw" / ".manifest.json"
        manifest.write_text("{}")

        script = str(Path(__file__).parent.parent / "tools" / "resolve_candidates.py")
        proc = subprocess.run(
            ["python3", script, str(wiki), str(results_dir), str(manifest)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        assert proc.returncode == 0
        assert "## CREATE" in proc.stdout
        assert "Ashish Vaswani" in proc.stdout

    def test_no_candidates_empty_output(self, tmp_path, sample_index):
        wiki = tmp_path / "wiki"
        for subdir in ("sources", "entities", "concepts"):
            (wiki / subdir).mkdir(parents=True)
        (wiki / "index.md").write_text(sample_index)

        results_dir = tmp_path / "raw" / ".compile-results"
        results_dir.mkdir(parents=True)

        source_no_refs = "---\ntitle: Test\ntype: source\n---\n\n## Overview\n\nNothing.\n\n## See Also\n\n"
        (wiki / "sources" / "empty.md").write_text(source_no_refs)
        import json
        (results_dir / "empty.json").write_text(json.dumps({
            "source_file": "empty.md", "slug": "empty",
            "source_page": "wiki/sources/empty.md", "status": "success",
        }))

        manifest = tmp_path / "raw" / ".manifest.json"
        manifest.write_text("{}")

        script = str(Path(__file__).parent.parent / "tools" / "resolve_candidates.py")
        proc = subprocess.run(
            ["python3", script, str(wiki), str(results_dir), str(manifest)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""
