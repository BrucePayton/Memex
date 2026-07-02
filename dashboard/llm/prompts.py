"""
Unified prompt template management for Memex.

Single source of truth for all LLM prompts used by dashboard/server.py,
dashboard/wiki_ops.py, and mcp-server/memex_mcp.py.

Usage:
    from dashboard.llm.prompts import ingest_prompt, lint_prompt, ...
    prompt = ingest_prompt(title="My Doc", content="...", folder="concepts", project="main")
"""

from string import Template
from typing import Optional


# ─── Ingest prompt ───

def ingest_prompt(
    title: str,
    content: str,
    folder: str = "",
    project: str = "",
    index_instruction: str = "",
    cascade_report: str = "",
) -> str:
    """Build the Claude ingest prompt for a new source document.

    cascade_report: optional output from CascadeUpdater.get_stale_report()
                    listing connected pages that have gone stale.
    """
    folder_path = f"wiki/{folder}/" if folder else "wiki/"
    return f"""You are maintaining a Memex wiki for project '{project or "default"}'.

{index_instruction}

## Ingest Task

Read the following source document and create/update wiki pages.

### Source: {title}

{content}

{cascade_report}

### Instructions

1. Read the source carefully
2. Identify key entities, concepts, techniques, and relationships
3. Create new wiki pages under {folder_path} or update existing ones
4. **Cascade refresh**: If cascade report above lists stale connected pages, review them for consistency with this new information and refresh as needed
5. Every factual claim MUST have an inline citation: [^src-{{source-slug}}]
6. Add footnote definitions at the bottom of each page
7. Update wiki/index.md to include new pages
8. Append an entry to wiki/log.md
9. Use the following frontmatter for each new page:

```yaml
---
title: "Page Title"
type: concept  # or entity, technique, source-summary, analysis
tags: [tag1, tag2]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
source_count: N
confidence: high  # high, medium, or low
status: active
---
```

### Contradiction Policy

- If a new source contradicts an existing page, mark the conflict
- Newer source generally supersedes older (unless explicit refutation)
- Create ## Disputed section when dates are close
- Never silently delete contradictory content

### Output

Return the wiki pages you created or updated, with their filenames.
"""


# ─── Lint prompt ───

def lint_prompt(project: str = "") -> str:
    """Full lint audit prompt per CLAUDE.md checklist."""
    return f"""Audit the wiki for project '{project or "default"}' against the following checklist.

## Structure Checks
- [ ] All .md files have valid YAML frontmatter (title, type, tags, created, last_updated)
- [ ] Page types are one of: concept, entity, technique, source-summary, analysis
- [ ] Status values are valid: active, superseded, disputed
- [ ] Confidence values are valid: high, medium, low
- [ ] No orphan pages (pages not linked from any other page or index)

## Citation Checks
- [ ] All factual claims have inline citations [^src-*]
- [ ] All citation footnotes have matching definitions
- [ ] All cited sources have corresponding source-summary pages
- [ ] No undefined source references

## Link Checks
- [ ] All [[wikilinks]] resolve to existing pages
- [ ] No broken links (target page does not exist)
- [ ] index.md and log.md are up to date
- [ ] Backlinks are consistent

## Freshness Checks
- [ ] Pages updated > 90 days ago are reviewed
- [ ] source-summary pages reflect current understanding
- [ ] Superseded pages are properly marked

## Contradiction Checks
- [ ] Disputed pages are documented with both viewpoints
- [ ] Superseded pages point to their replacement
- [ ] Log entries explain contradiction resolutions

Report: Critical issues, Warnings, and Info-level findings.
"""


def lint_fix_prompt() -> str:
    """Auto-fix prompt for lint issues."""
    return """Fix all lint issues found in the previous audit:

1. Add missing frontmatter fields
2. Add citations to uncited factual claims
3. Fix broken wikilinks (update or remove)
4. Mark stale pages for review
5. Update index.md and log.md
6. Resolve contradictions (mark as disputed or superseded)

For each fix, explain what was changed and why.
"""


# ─── Reflect prompt ───

def reflect_prompt(window: str = "last-10-ingests", project: str = "") -> str:
    """Meta-analysis prompt for wiki pattern detection."""
    return f"""Analyze the wiki for project '{project or "default"}' over window '{window}'.

## Analysis Tasks

1. Review recent ingest reports and log entries
2. Identify patterns:
   - Frequently mentioned entities without dedicated pages
   - Concepts that appear across multiple source-summaries
   - Gaps in cross-referencing
3. Suggest:
   - New wiki pages to create
   - Schema updates for CLAUDE.md
   - Sources to prioritize for ingest
   - Improvements to contradiction policy
4. Check wiki health:
   - Which page types are growing fastest?
   - Are any areas under-documented?
   - Is citation coverage improving or declining?

Output: structured recommendations with rationale.
"""


# ─── Write prompt ───

def write_prompt(
    topic: str,
    length: str = "medium",
    style: str = "blog",
    project: str = "",
) -> str:
    """Writing assistant prompt."""
    length_guide = {
        "short": "~500 words, 3-5 paragraphs",
        "medium": "~1500 words, 5-8 sections",
        "long": "~3000 words, 8-12 sections with subsections",
    }.get(length, "~1500 words")

    style_guide = {
        "blog": "Conversational, engaging, use analogies and examples. Lead with a strong hook.",
        "paper": "Academic tone, structured abstractions, rigorous citations. Lead with an abstract.",
        "explainer": "Educational, progressive disclosure, start simple then go deep. Use concrete examples.",
    }.get(style, "Conversational and engaging")

    return f"""Write a {length} wiki page ({length_guide}) on: {topic}

Style: {style_guide}

## Requirements

1. Draw ONLY from existing wiki pages in project '{project or "default"}'
2. Every factual claim must cite its source: [^src-{{source-slug}}]
3. Include [[wikilinks]] to related pages
4. Use proper YAML frontmatter
5. Structure with ## headings for readability
6. If information is insufficient, note the gaps explicitly
"""


# ─── Schema evolution prompt ───

def schema_evolution_prompt(
    lint_history: str,
    current_schema: str,
    project: str = "",
) -> str:
    """Schema self-evolution prompt: detect lint patterns, propose CLAUDE.md revisions.

    Args:
        lint_history: recent lint findings (from wiki/log.md)
        current_schema: current CLAUDE.md content
    """
    return f"""Analyze the following lint history and current schema for project '{project or "default"}'.

## Recent Lint Findings

{lint_history}

## Current CLAUDE.md Schema

{current_schema}

## Task

1. **Pattern Detection**: Identify recurring lint issues (same type appearing ≥3 times).
   - Example: "Missing 'confidence' field" found in 5 lint runs → pattern.
   - Example: "Broken wikilinks to source-summary pages" found 3 times → pattern.

2. **Root Cause**: For each pattern, determine the root cause.
   - Is the schema rule unclear?
   - Is a required field missing from the frontmatter spec?
   - Is the threshold too strict?

3. **Proposed Schema Revision**: Draft a specific change to CLAUDE.md that would prevent this pattern.
   - Add/modify a frontmatter field requirement
   - Clarify a rule
   - Adjust a threshold
   - Add a new check

4. **Expected Impact**: Estimate the % reduction in this lint pattern after the change.

Output format:
```
## Pattern: <name> (occurrences: N)
- Root cause: <explanation>
- Proposed change: <specific CLAUDE.md diff>
- Expected reduction: X%

## Pattern: <name> (occurrences: N)
...
```
"""


def schema_ab_blind_review_prompt(
    proposed_schema: str,
    current_schema: str,
    test_tasks: str,
) -> str:
    """A/B blind review: evaluate old vs new schema on same tasks.

    The LLM evaluates both schemas WITHOUT knowing which is old/new.
    """

    return f"""You are evaluating two wiki maintenance schemas. You do NOT know which is "Schema A" or "Schema B".

## Test Tasks (same for both schemas)

{test_tasks}

## Schema A

{proposed_schema}

## Schema B

{current_schema}

## Evaluation

For each schema, score these dimensions (1-5):

1. **Clarity**: How clear and unambiguous are the rules?
2. **Completeness**: Do the rules cover all necessary frontmatter fields and checks?
3. **Consistency**: Are there conflicting or overlapping rules?
4. **Enforceability**: Can the rules be mechanically checked (by lint)?

Then provide:
- **Winner**: Schema A or Schema B (or Tie)
- **Key difference**: What is the most impactful difference?
- **Recommendation**: Should we adopt Schema A? (yes/no)

IMPORTANT: Evaluate purely on schema quality. Do NOT try to guess which is the new vs old version.
"""


# ─── Compare prompt ───

def compare_prompt(
    page_a: str,
    page_b: str,
    save_as: str = "",
    project: str = "",
) -> str:
    """Two-page comparison prompt."""
    save_instr = f"Save the comparison as '{save_as}'." if save_as else ""
    return f"""Compare these two wiki pages from project '{project or "default"}':

- Page A: {page_a}
- Page B: {page_b}

## Structure

1. **Common Ground**: What do both pages agree on? Shared facts, entities, concepts.
2. **Differences**: Where do they diverge? Conflicting claims, different perspectives, missing coverage.
3. **Relationship**: How do they relate? Does one extend/contradict/supplement the other?
4. **Synthesis**: What's the integrated view? How should a reader understand both together?

{save_instr}
"""


# ─── Loop prompt ───

def loop_prompt(
    steps: list[str],
    include_ingest: bool = False,
    reflect_window: str = "last-10-ingests",
    project: str = "",
) -> str:
    """Maintenance loop prompt."""
    steps_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    ingest_note = "\nAlso check for new uncited sources in raw/ and ingest them." if include_ingest else ""

    return f"""Execute the following maintenance steps sequentially for project '{project or "default"}':

{steps_str}
{ingest_note}

## Progress Tracking

For each step, report:
- Status: completed / failed / skipped
- Key findings or changes made
- Files modified

## Reflect Window

Use reflect window: {reflect_window}

Continue to next step even if current step fails (continue_on_error=True).
"""


# ─── Lint pattern extraction ───

def extract_lint_patterns(log_content: str, min_occurrences: int = 3) -> dict[str, int]:
    """Extract recurring lint issue patterns from wiki/log.md.

    Returns {issue_description: occurrence_count} for issues
    appearing >= min_occurrences times.
    """
    import re
    from collections import Counter

    # Match lint entries: "## [YYYY-MM-DD] lint | ..."
    lint_entries = re.findall(
        r"## \[\d{4}-\d{2}-\d{2}\] lint.*?\n(.*?)(?=\n## \[|\Z)",
        log_content, re.DOTALL,
    )

    # Extract issue descriptions (lines starting with "- " after lint entries)
    issues = []
    for entry in lint_entries:
        for line in entry.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                # Normalize: remove page-specific details
                normalized = re.sub(r"\([^)]+\)", "", line)
                normalized = re.sub(r"`[^`]+`", "`<page>`", normalized)
                issues.append(normalized.strip("- *").strip())

    counter = Counter(issues)
    return {k: v for k, v in counter.items() if v >= min_occurrences}


# ─── Index navigation instruction ───

def index_instruction(mode: str, page_count: int) -> str:
    """Generate navigation instructions based on index strategy."""
    if mode == "flat":
        return f"""## Index Navigation

The wiki has {page_count} pages. The index is a single `wiki/index.md` file.
Read it to understand the wiki structure before making changes.
"""
    elif mode == "hierarchical":
        return f"""## Index Navigation

The wiki has {page_count} pages (hierarchical mode).
- `wiki/index.md` — summary index with per-type overviews
- `wiki/index-*.md` — type-specific sub-indexes (index-concepts.md, index-entities.md, etc.)

Read the summary index first, then the relevant sub-indexes.
"""
    else:  # indexed
        return f"""## Index Navigation

The wiki has {page_count} pages (indexed mode with >200 pages).
- Use the search function for targeted queries
- Read `wiki/index.md` for structural overview
- BM25/vector search is recommended for large wikis
"""
