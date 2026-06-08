"""Tests for the kw-surface gating logic (lib/learning_surface.py).

The bash hook `hooks/kw-surface` is thin glue (read stdin JSON, resolve stores,
manage the per-session seen-file, print). The decision logic that matters —
tokenize the prompt, score against the index tag column, gate, prioritise, cap —
lives in lib/learning_surface and is tested here, mirroring how
tests/test_hook_status.py tests the pure parser rather than the bash script.
"""
from lib.learning_surface import (
    extract_tokens,
    count_tag_hits,
    qualifies,
    select,
    render,
    surface,
)
from lib.learning_index import build_index


def _entry(type_, id_, tags, headline, date="2026-06-08", confidence="STATED"):
    return {
        "type": type_,
        "id": id_,
        "tags": tags,
        "headline": headline,
        "confidence": confidence,
        "date": date,
    }


def _index(*entries):
    return build_index(list(entries))


class TestExtractTokens:
    def test_lowercases_and_drops_short_and_stopwords(self):
        tokens = extract_tokens("How do I add JITTER to the Retry?")
        assert tokens == {"add", "jitter", "retry"}

    def test_empty_prompt(self):
        assert extract_tokens("") == set()

    def test_splits_on_punctuation(self):
        assert "backoff" in extract_tokens("retry-backoff, please")


class TestCountTagHits:
    def test_exact_tag_match(self):
        assert count_tag_hits(["retries", "networking"], {"retries"}) == 1

    def test_two_tags_hit(self):
        assert count_tag_hits(["retries", "backoff"], {"retries", "backoff"}) == 2

    def test_no_hit(self):
        assert count_tag_hits(["retries"], {"testing", "docker"}) == 0

    def test_hyphenated_tag_part_matches(self):
        # tag "thundering-herd" hits when the prompt mentions one part
        assert count_tag_hits(["thundering-herd"], {"herd", "problem"}) == 1

    def test_each_tag_counts_at_most_once(self):
        # both parts present, but the single tag still contributes only 1
        assert count_tag_hits(["thundering-herd"], {"thundering", "herd"}) == 1


class TestQualifies:
    def test_two_hits_qualifies_for_any_type(self):
        assert qualifies("insight", 2) is True

    def test_one_hit_insight_does_not_qualify(self):
        assert qualifies("insight", 1) is False

    def test_one_hit_correction_qualifies(self):
        assert qualifies("correction", 1) is True

    def test_zero_hits_never_qualifies(self):
        assert qualifies("correction", 0) is False


class TestSelect:
    def test_below_threshold_returns_empty(self):
        entries = [_entry("insight", "kw-1", ["retries", "networking"], "Insight one")]
        # only one tag hits -> insight needs 2
        assert select(entries, "retries are flaky") == []

    def test_two_hit_insight_selected(self):
        entries = [_entry("insight", "kw-1", ["retries", "backoff"], "Use backoff")]
        out = select(entries, "tune retries with backoff")
        assert [e["id"] for e in out] == ["kw-1"]

    def test_correction_single_hit_selected(self):
        entries = [_entry("correction", "kw-c", ["retries"], "Add jitter")]
        out = select(entries, "our retries hammer the server")
        assert [e["id"] for e in out] == ["kw-c"]

    def test_corrections_sorted_first(self):
        entries = [
            _entry("insight", "kw-i", ["docker", "build"], "Insight"),
            _entry("correction", "kw-c", ["docker", "build"], "Correction"),
        ]
        out = select(entries, "docker build is slow")
        assert [e["id"] for e in out] == ["kw-c", "kw-i"]

    def test_capped_at_three(self):
        entries = [
            _entry("insight", f"kw-{i}", ["docker", "build"], f"Insight {i}")
            for i in range(5)
        ]
        out = select(entries, "docker build issues")
        assert len(out) == 3

    def test_seen_ids_excluded(self):
        entries = [
            _entry("correction", "kw-a", ["docker"], "A"),
            _entry("correction", "kw-b", ["docker"], "B"),
        ]
        out = select(entries, "docker problem", seen_ids={"kw-a"})
        assert [e["id"] for e in out] == ["kw-b"]


class TestRender:
    def test_empty_entries_render_to_empty_string(self):
        assert render([]) == ""

    def test_renders_headline_lines_with_type_code(self):
        entries = [_entry("correction", "kw-c", ["x"], "Add jitter to retry backoff")]
        out = render(entries)
        assert "[C]" in out
        assert "Add jitter to retry backoff" in out

    def test_caps_at_three_bullet_lines(self):
        entries = [_entry("insight", f"kw-{i}", ["x"], f"H {i}") for i in range(3)]
        out = render(entries)
        bullets = [ln for ln in out.splitlines() if ln.startswith("- [")]
        assert len(bullets) == 3


class TestSurface:
    def test_no_index_text_yields_nothing(self):
        out, ids = surface([], "anything goes here")
        assert out == ""
        assert ids == []

    def test_generic_prompt_injects_nothing(self):
        idx = _index(_entry("insight", "kw-1", ["retries", "backoff"], "Use backoff"))
        out, ids = surface([idx], "write me a haiku about the sea")
        assert out == ""
        assert ids == []

    def test_matching_prompt_surfaces_and_reports_ids(self):
        idx = _index(_entry("correction", "kw-c", ["retries"], "Add jitter"))
        out, ids = surface([idx], "our retries are hammering the API")
        assert "Add jitter" in out
        assert ids == ["kw-c"]

    def test_both_tiers_merged_and_deduped_by_id(self):
        shared = _entry("correction", "kw-c", ["docker"], "Project version")
        proj = _index(shared)
        glob = _index(_entry("correction", "kw-c", ["docker"], "Global version"))
        out, ids = surface([proj, glob], "docker build problem")
        # id appears once; project (passed first) shadows global
        assert ids == ["kw-c"]
        assert "Project version" in out
        assert "Global version" not in out

    def test_seen_ids_suppress_repeat_in_session(self):
        idx = _index(_entry("correction", "kw-c", ["docker"], "Docker lesson"))
        out, ids = surface([idx], "docker build problem", seen_ids={"kw-c"})
        assert out == ""
        assert ids == []

    def test_output_stays_within_token_budget(self):
        # Three corrections with max-length (100-char) headlines is the worst case.
        # Headline-only + lean header/pointer must stay near the ~90-token cap;
        # 4 chars/token heuristic -> assert the block is well under 130 tokens.
        long = "x" * 100
        entries = [_entry("correction", f"kw-{i}", ["docker"], long) for i in range(3)]
        idx = _index(*entries)
        out, ids = surface([idx], "docker build problem")
        assert len([ln for ln in out.splitlines() if ln.startswith("- [")]) == 3
        assert len(out) / 4 < 130
