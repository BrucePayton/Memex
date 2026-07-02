"""Unit tests for schema self-evolution prompts and lint pattern extraction."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.llm.prompts import (
    schema_evolution_prompt, schema_ab_blind_review_prompt,
    extract_lint_patterns,
)


class TestSchemaEvolutionPrompt:
    def test_basic_structure(self):
        p = schema_evolution_prompt(
            lint_history="- Missing confidence field\n- Broken wikilink",
            current_schema="type: concept\nconfidence: high",
        )
        assert "Pattern Detection" in p
        assert "Missing confidence" in p
        assert "Root Cause" in p
        assert "Proposed Schema Revision" in p

    def test_with_project(self):
        p = schema_evolution_prompt("", "", project="test-project")
        assert "test-project" in p


class TestABBlindReviewPrompt:
    def test_does_not_reveal_which_is_new(self):
        p = schema_ab_blind_review_prompt(
            proposed_schema="NEW RULES",
            current_schema="OLD RULES",
            test_tasks="Task 1: lint check",
        )
        # Labels must be neutral (Schema A / Schema B)
        assert "Schema A" in p
        assert "Schema B" in p
        # Must instruct LLM NOT to guess which is new/old
        assert "Do NOT try to guess" in p
        assert "IMPORTANT" in p

    def test_scoring_dimensions(self):
        p = schema_ab_blind_review_prompt("A", "B", "tasks")
        assert "Clarity" in p
        assert "Completeness" in p
        assert "Consistency" in p
        assert "Enforceability" in p
        assert "Winner" in p


class TestExtractLintPatterns:
    def test_no_patterns_below_threshold(self):
        log = """## [2026-07-01] lint | audit
- Missing confidence in `page-a.md`
- Broken link in `page-b.md`
"""
        patterns = extract_lint_patterns(log, min_occurrences=2)
        assert len(patterns) == 0

    def test_recurring_pattern_detected(self):
        log = """## [2026-07-01] lint | audit
- Missing confidence in `<page>`
## [2026-07-02] lint | audit
- Missing confidence in `<page>`
## [2026-07-03] lint | audit
- Missing confidence in `<page>`
"""
        patterns = extract_lint_patterns(log, min_occurrences=3)
        assert len(patterns) >= 1
        for k, v in patterns.items():
            if "confidence" in k.lower():
                assert v >= 3

    def test_normalized_page_names(self):
        log = """## [2026-07-01] lint | audit
- Missing confidence in `concepts/ai.md`
## [2026-07-02] lint | audit
- Missing confidence in `entities/ml.md`
"""
        patterns = extract_lint_patterns(log, min_occurrences=2)
        # Both should be normalized to the same pattern
        assert any("confidence" in k.lower() for k in patterns)

    def test_empty_log(self):
        patterns = extract_lint_patterns("", min_occurrences=1)
        assert len(patterns) == 0
