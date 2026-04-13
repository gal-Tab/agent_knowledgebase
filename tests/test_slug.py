"""Tests for slug generation (lib/slug.py)."""
import pytest

from lib.slug import slug_source, slug_entity, slug_concept, slug_comparison


class TestSlugSource:
    def test_basic_title(self):
        assert slug_source("Scaling Laws for Neural Language Models") == "scaling-laws-neural-lm"

    def test_removes_stopwords(self):
        result = slug_source("The Art of War")
        assert "the" not in result.split("-")[1:]  # first word kept

    def test_abbreviates_language_models(self):
        result = slug_source("Training Large Language Models Efficiently")
        assert "lm" in result

    def test_hyphenated_output(self):
        result = slug_source("Attention Is All You Need")
        assert " " not in result
        assert result == result.lower()

    def test_special_characters_removed(self):
        result = slug_source("GPT-4: A Technical Report!")
        assert ":" not in result
        assert "!" not in result

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            slug_source("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            slug_source("   ")

    def test_long_title_truncated(self):
        long_title = " ".join(["word"] * 50)
        result = slug_source(long_title)
        assert len(result) <= 80

    def test_unicode_normalized(self):
        result = slug_source("Résumé of Naïve Approaches")
        assert result.isascii()


class TestSlugEntity:
    def test_person_lastname_first(self):
        assert slug_entity("Jared Kaplan", "person") == "kaplan-jared"

    def test_person_single_name(self):
        assert slug_entity("Vaswani", "person") == "vaswani"

    def test_org_lowercase(self):
        assert slug_entity("OpenAI", "org") == "openai"

    def test_org_with_spaces(self):
        assert slug_entity("Google DeepMind", "org") == "google-deepmind"

    def test_product_type(self):
        assert slug_entity("GPT-4", "product") == "gpt-4"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            slug_entity("", "person")

    def test_default_type_is_person(self):
        assert slug_entity("John Smith") == "smith-john"


class TestSlugConcept:
    def test_basic_concept(self):
        assert slug_concept("Scaling Laws") == "scaling-laws"

    def test_lowercase(self):
        result = slug_concept("Compute-Optimal Training")
        assert result == result.lower()

    def test_special_chars_stripped(self):
        result = slug_concept("Attention (Self-Attention)")
        # Parentheses removed
        assert "(" not in result
        assert ")" not in result

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            slug_concept("")


class TestSlugComparison:
    def test_basic_comparison(self):
        result = slug_comparison("GPT-4", "Claude")
        assert "vs" in result
        assert result.endswith("comparison")

    def test_format(self):
        result = slug_comparison("GPT-4", "Claude")
        assert result == "gpt-4-vs-claude-comparison"

    def test_empty_a_raises(self):
        with pytest.raises(ValueError):
            slug_comparison("", "Claude")

    def test_empty_b_raises(self):
        with pytest.raises(ValueError):
            slug_comparison("GPT-4", "")

    def test_long_names_truncated(self):
        long_a = "A" * 50
        long_b = "B" * 50
        result = slug_comparison(long_a, long_b)
        assert len(result) <= 80
