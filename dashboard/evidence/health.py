"""
Health score calculator: computes a composite health score (0-100)
for process knowledge projects based on multiple weighted dimensions.

Dimensions (default weights):
  - resource_completeness (30%): existing_references / total_references
  - card_completeness (25%): complete_cards / total_cards
  - citation_coverage (20%): cited claims / total claims
  - lint_pass_rate (15%): pages passing lint / total pages
  - freshness (10%): active pages updated within 30 days
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .scanner import ReferenceScanner
from .validator import ReferenceValidator


@dataclass
class HealthScore:
    """Composite project health score."""
    overall: float = 0.0                # 0-100
    dimensions: dict = field(default_factory=dict)  # {dim_id: {score, weight, name, ...}}
    missing_items: list = field(default_factory=list)
    trend: list = field(default_factory=list)       # [{date, score}]


class HealthScorer:
    """Compute health scores for Memex knowledge projects."""

    DEFAULT_WEIGHTS = {
        "resource_completeness": 30,
        "card_completeness": 25,
        "citation_coverage": 20,
        "lint_pass_rate": 15,
        "freshness": 10,
    }

    def __init__(self, project_root: str | Path = ""):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.scanner = ReferenceScanner()
        self.validator = ReferenceValidator(project_root)

    def compute(self, wiki_dir: str | Path, raw_dir: str | Path = "") -> HealthScore:
        """Compute comprehensive health score for a project."""
        wiki = Path(wiki_dir)
        raw = Path(raw_dir) if raw_dir else wiki.parent / "raw"

        score = HealthScore()
        dimensions = {}

        # 1. Resource completeness (30%)
        dim_resource = self._score_resource_completeness(raw)
        dimensions["resource_completeness"] = {"score": dim_resource, "weight": 30, "name": "Resource Completeness"}

        # 2. Card completeness (25%)
        dim_card = self._score_card_completeness(wiki)
        dimensions["card_completeness"] = {"score": dim_card, "weight": 25, "name": "Card Completeness"}

        # 3. Citation coverage (20%)
        dim_citation = self._score_citation_coverage(wiki)
        dimensions["citation_coverage"] = {"score": dim_citation, "weight": 20, "name": "Citation Coverage"}

        # 4. Lint pass rate (15%)
        dim_lint = self._score_lint_pass_rate(wiki)
        dimensions["lint_pass_rate"] = {"score": dim_lint, "weight": 15, "name": "Lint Pass Rate"}

        # 5. Freshness (10%)
        dim_fresh = self._score_freshness(wiki)
        dimensions["freshness"] = {"score": dim_fresh, "weight": 10, "name": "Freshness"}

        score.dimensions = dimensions
        score.overall = round(
            sum(d["score"] * d["weight"] / 100 for d in dimensions.values()), 1
        )
        return score

    def _score_resource_completeness(self, raw_dir: Path) -> float:
        """Calculate resource reference completeness."""
        if not raw_dir.is_dir():
            return 100.0
        all_refs = self.scanner.scan_all(raw_dir, self.project_root)
        total = 0
        valid = 0
        for file_path, refs in all_refs.items():
            results = self.validator.validate_all(refs)
            total += len(results)
            valid += sum(1 for r in results if r.status == "valid")
        if total == 0:
            return 100.0
        return round(valid / total * 100, 1)

    def _score_card_completeness(self, wiki_dir: Path) -> float:
        """Calculate knowledge card completeness."""
        from dashboard.models import CARD_TYPES, parse_fm
        total = 0
        complete = 0
        for md_file in wiki_dir.glob("**/*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                meta, _ = parse_fm(text)
                if meta.get("type") in CARD_TYPES:
                    total += 1
                    missing = meta.get("missing_sections", [])
                    if isinstance(missing, str):
                        missing = [missing] if missing else []
                    if not missing:
                        complete += 1
            except Exception:
                pass
        if total == 0:
            return 100.0
        return round(complete / total * 100, 1)

    def _score_citation_coverage(self, wiki_dir: Path) -> float:
        """Calculate citation coverage across wiki pages."""
        from dashboard.models import parse_fm, extract_citations
        pages = 0
        total_claims = 0
        cited_claims = 0
        for md_file in wiki_dir.glob("**/*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                _, body = parse_fm(text)
                citations = extract_citations(body)
                # Count sentences as proxy for claims
                sentences = [s.strip() for s in body.replace("\n", " ").split(".") if s.strip()]
                if len(sentences) > 2:  # skip empty/header-only pages
                    pages += 1
                    total_claims += len(sentences)
                    cited_claims += min(len(citations), len(sentences))
            except Exception:
                pass
        if total_claims == 0:
            return 100.0
        return round(min(cited_claims / total_claims * 100, 100), 1)

    def _score_lint_pass_rate(self, wiki_dir: Path) -> float:
        """Estimate lint pass rate based on basic checks."""
        from dashboard.models import parse_fm
        pages = 0
        passed = 0
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for md_file in wiki_dir.glob("**/*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                meta, _ = parse_fm(text)
                if meta.get("type") in ("overview",):
                    continue  # skip system pages
                pages += 1
                # Basic lint: has frontmatter, has title, has type
                if meta.get("title") and meta.get("type"):
                    passed += 1
            except Exception:
                pass
        if pages == 0:
            return 100.0
        return round(passed / pages * 100, 1)

    def _score_freshness(self, wiki_dir: Path) -> float:
        """Calculate page freshness (active pages updated within 30 days)."""
        from dashboard.models import parse_fm
        from datetime import timedelta
        active_pages = 0
        fresh_pages = 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        for md_file in wiki_dir.glob("**/*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                meta, _ = parse_fm(text)
                if meta.get("status") == "active" and meta.get("type") not in ("overview",):
                    active_pages += 1
                    updated = meta.get("last_updated", "") or meta.get("updated", "")
                    if updated:
                        try:
                            dt = datetime.strptime(updated[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            if dt > cutoff:
                                fresh_pages += 1
                        except ValueError:
                            pass
            except Exception:
                pass
        if active_pages == 0:
            return 100.0
        return round(fresh_pages / active_pages * 100, 1)
