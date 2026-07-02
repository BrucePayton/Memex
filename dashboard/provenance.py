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
    """페이지 검증:
    - 모든 [^src-*] 참조에 정의가 있는지
    - 정의된 source-summary 페이지가 존재하는지
    - claim 중 citation 없는 비율
    """
    text = page_path.read_text("utf-8")
    refs = parse_citations(text)
    defs = _get_definitions(text)
    total_claims, cited_claims = _count_claims(text)

    # 1. 참조인데 정의 없음
    undefined_refs = [slug for slug in refs if slug not in defs]

    # 2. 정의된 source 페이지 존재 여부
    missing_sources = []
    for slug, target in defs.items():
        # target에서 wikilink 추출: [[source-xxx]] 또는 그냥 텍스트
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
    """모든 wiki 페이지 검증 결과 리스트 반환"""
    results = []
    for md in sorted(wiki_dir.rglob("*.md")):
        rel = str(md.relative_to(wiki_dir))
        # 메타 페이지는 스킵
        if is_system_page(rel):
            continue
        text = md.read_text("utf-8")
        # source 타입 페이지는 그 자체가 출처이므로 스킵
        if re.search(r"^type:\s*source", text, re.MULTILINE):
            continue
        v = validate_page(md, wiki_dir)
        # claim이 0인 페이지도 포함 (overview 등)
        results.append(v)
    # 커버리지 낮은 순 정렬
    results.sort(key=lambda x: x["coverage"])
    return results
