"""
provenance.py — Inline citation parsing, validation, and provenance graph.

Tracks [^src-*] footnote citations in wiki pages. Uses Markdown-aware
parsing to distinguish real prose claims from code blocks, headings,
blockquotes, tables, and list markers.

Citation format:
  Inline: "Attention replaces recurrence[^src-attention-is-all-you-need]."
  Definition: "[^src-attention-is-all-you-need]: [[source-attention]]"
"""

import re
from pathlib import Path

# [^src-slug] reference (inline)
CITE_REF_RE = re.compile(r"\[\^(src-[a-z0-9-]+)\](?!:)")
# [^src-slug]: definition (bottom of page)
CITE_DEF_RE = re.compile(r"^\[\^(src-[a-z0-9-]+)\]:\s*(.+)", re.MULTILINE)

from dashboard.models import FRONTMATTER_RE, is_system_page

# ─── Markdown-aware claim detection ───
# Previously used a single regex that couldn't distinguish code blocks
# from prose. Now uses state-machine line parsing for accuracy.

# Lines that are never claims (structural elements)
_HEADING_RE = re.compile(r"^#{1,6}\s")
_BLOCKQUOTE_RE = re.compile(r"^>\s")
_UNORDERED_LIST_RE = re.compile(r"^\s*[-*+]\s+")
_ORDERED_LIST_RE = re.compile(r"^\s*\d+\.\s+")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*[-:]{3,}\s*\|")  # | --- | --- |
_TABLE_ROW_RE = re.compile(r"^\s*\|")  # | cell | cell |
_LINK_ONLY_RE = re.compile(r"^\s*\[([^\]]+)\](?:\([^)]+\))?\s*$")  # [text](url) only
_CODE_FENCE_RE = re.compile(r"^\s*```")
_FRONTMATTER_END_RE = re.compile(r"^---\s*$")
_EMPTY_RE = re.compile(r"^\s*$")


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter block from text."""
    m = FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def _extract_prose_claims(body: str) -> list[str]:
    """Extract prose claim sentences using Markdown state-machine parsing.

    Accurately excludes: code fences, headings, blockquotes, list items,
    table rows, link-only lines, empty lines, and frontmatter.
    """
    claims = []
    in_code_block = False
    in_frontmatter = False
    fm_end_count = 0  # track frontmatter end markers seen

    for line in body.split("\n"):
        # Track frontmatter boundaries
        if _FRONTMATTER_END_RE.match(line) and fm_end_count == 0:
            fm_end_count += 1
            continue

        # Track code fences
        if _CODE_FENCE_RE.match(line):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Skip structural lines
        if (_HEADING_RE.match(line) or
            _BLOCKQUOTE_RE.match(line) or
            _UNORDERED_LIST_RE.match(line) or
            _ORDERED_LIST_RE.match(line) or
            _TABLE_SEP_RE.match(line) or
            _TABLE_ROW_RE.match(line) or
            _LINK_ONLY_RE.match(line) or
            _EMPTY_RE.match(line)):
            continue

        # Check if line contains a claim-ending sentence
        stripped = line.strip()
        if stripped.endswith(".") or stripped.endswith("。"):
            claims.append(stripped)

    return claims


def parse_citations(page_content: str) -> dict[str, list[int]]:
    """Extract [^src-*] references from page → {source_slug: [char_positions]}"""
    body = _strip_frontmatter(page_content)
    result: dict[str, list[int]] = {}
    for m in CITE_REF_RE.finditer(body):
        slug = m.group(1)
        result.setdefault(slug, []).append(m.start())
    return result


def _get_definitions(page_content: str) -> dict[str, str]:
    """Extract [^src-*]: definitions → {slug: target_text}"""
    body = _strip_frontmatter(page_content)
    return {m.group(1): m.group(2).strip() for m in CITE_DEF_RE.finditer(body)}


def _count_claims(page_content: str) -> tuple[int, int]:
    """Count (total claims, cited claims) using Markdown-aware parsing."""
    body = _strip_frontmatter(page_content)
    claims = _extract_prose_claims(body)
    total = len(claims)
    cited = sum(1 for c in claims if CITE_REF_RE.search(c))
    return total, cited


def validate_page(page_path: Path, wiki_dir: Path) -> dict:
    """Page validation:
    - all [^src-*] references have definitions
    - defined source-summary pages exist
    - ratio of claims without citations
    """
    text = page_path.read_text("utf-8")
    refs = parse_citations(text)
    defs = _get_definitions(text)
    total_claims, cited_claims = _count_claims(text)

    # 1. reference without definition
    undefined_refs = [slug for slug in refs if slug not in defs]

    # 2. whether defined source page exists
    missing_sources = []
    for slug, target in defs.items():
        # extract wikilink from target: [[source-xxx]] or plain text
        wl = re.search(r"\[\[([^\]]+)\]\]", target)
        source_filename = (wl.group(1) if wl else slug.replace("src-", "source-")) + ".md"
        if not (wiki_dir / source_filename).exists():
            missing_sources.append({"slug": slug, "expected": source_filename})

    coverage = (cited_claims / total_claims * 100) if total_claims > 0 else 100.0

    return {
        "page": str(page_path.relative_to(wiki_dir)),
        "total_claims": total_claims,
        "cited_claims": cited_claims,
        "coverage": round(coverage, 1),
        "undefined_refs": undefined_refs,
        "missing_sources": missing_sources,
    }


def build_provenance_graph(wiki_dir: Path) -> list[dict]:
    """Return validation results for all wiki pages"""
    results = []
    for md in sorted(wiki_dir.rglob("*.md")):
        rel = str(md.relative_to(wiki_dir))
        # skip meta pages
        if is_system_page(rel):
            continue
        text = md.read_text("utf-8")
        # skip source-type pages as they are themselves sources
        if re.search(r"^type:\s*source", text, re.MULTILINE):
            continue
        v = validate_page(md, wiki_dir)
        # include pages with 0 claims (overview etc.)
        results.append(v)
    # sort by lowest coverage
    results.sort(key=lambda x: x["coverage"])
    return results
