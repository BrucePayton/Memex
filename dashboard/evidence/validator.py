"""
Reference validator: checks reachability of resource references.

Validation strategies:
  - Local files: os.path.exists()
  - External URLs: HTTP HEAD request
  - Feishu objects: format validation (token/sheet-id format check)
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

from .scanner import Reference


@dataclass
class ValidationResult:
    """Validation result for a single reference."""
    ref: Reference
    status: str           # valid | broken | unreachable | unknown
    reason: str = ""
    fix_path: str = ""    # suggested fix path or action


class ReferenceValidator:
    """Validate resource references for reachability."""

    # Feishu token/doc-id format patterns
    FEISHU_SHEET_ID_RE = re.compile(r'^[a-zA-Z0-9_-]{4,32}$')
    FEISHU_DOC_ID_RE = re.compile(r'^[a-zA-Z0-9_-]{4,64}$')

    def __init__(self, project_root: str | Path = "", timeout: int = 5):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.timeout = timeout

    def validate(self, ref: Reference) -> ValidationResult:
        """Validate a single reference and return the result."""
        if ref.ref_type in ("image_md", "file_link"):
            return self._validate_local_file(ref)
        elif ref.ref_type == "url":
            return self._validate_url(ref)
        elif ref.ref_type == "sheet_embed":
            return self._validate_sheet(ref)
        elif ref.ref_type in ("cite_ref", "figure_ref"):
            return self._validate_doc(ref)
        elif ref.ref_type == "image_html":
            target = ref.target
            if target.startswith("http"):
                url_ref = Reference(ref_type="url", location=ref.location,
                                    raw_text=ref.raw_text, target=target, line_no=ref.line_no)
                return self._validate_url(url_ref)
            return self._validate_local_file(ref)
        return ValidationResult(ref=ref, status="unknown", reason=f"unhandled type: {ref.ref_type}")

    def _validate_local_file(self, ref: Reference) -> ValidationResult:
        """Check if a local file exists."""
        check_path = ref.expected_path or ref.target
        fp = Path(check_path)
        if fp.exists():
            return ValidationResult(ref=ref, status="valid")
        # Check in raw/assets/ relative to project root
        alt = self.project_root / "raw" / "assets" / Path(ref.target).name
        if alt.exists():
            return ValidationResult(ref=ref, status="valid")
        return ValidationResult(
            ref=ref, status="broken",
            reason=f"file not found: {ref.target}",
            fix_path=f"Place {Path(ref.target).name} in raw/assets/ or re-export from source document",
        )

    def _validate_url(self, ref: Reference) -> ValidationResult:
        """Check external URL reachability via HEAD request."""
        try:
            req = Request(ref.target, method="HEAD")
            req.add_header("User-Agent", "Memex-Evidence-Validator/1.0")
            resp = urlopen(req, timeout=self.timeout)
            if resp.status < 400:
                return ValidationResult(ref=ref, status="valid")
            return ValidationResult(
                ref=ref, status="broken",
                reason=f"HTTP {resp.status}",
                fix_path="Check URL is correct and accessible",
            )
        except URLError as e:
            return ValidationResult(
                ref=ref, status="unreachable",
                reason=str(e.reason) if hasattr(e, "reason") else str(e),
                fix_path="Verify URL or check network connectivity",
            )
        except Exception as e:
            return ValidationResult(ref=ref, status="unknown", reason=str(e))

    def _validate_sheet(self, ref: Reference) -> ValidationResult:
        """Check Feishu sheet ID format validity."""
        if self.FEISHU_SHEET_ID_RE.match(ref.target):
            return ValidationResult(
                ref=ref, status="unknown",
                reason="sheet ID format valid but local cache not checked",
                fix_path=f"Export from Feishu sheet {ref.target} to CSV, place in embedded_sheets/",
            )
        return ValidationResult(
            ref=ref, status="broken",
            reason=f"invalid sheet ID format: {ref.target}",
            fix_path="Check the sheet-id attribute is correct",
        )

    def _validate_doc(self, ref: Reference) -> ValidationResult:
        """Check Feishu document citation ID format."""
        if self.FEISHU_DOC_ID_RE.match(ref.target):
            return ValidationResult(
                ref=ref, status="unknown",
                reason="doc ID format valid but remote verification not available",
                fix_path="Verify the document is accessible in Feishu workspace",
            )
        return ValidationResult(
            ref=ref, status="broken",
            reason=f"invalid doc ID format: {ref.target}",
            fix_path="Check the doc-id attribute is correct",
        )

    def validate_all(self, refs: list[Reference]) -> list[ValidationResult]:
        """Validate a list of references."""
        return [self.validate(r) for r in refs]

    def summary(self, results: list[ValidationResult]) -> dict:
        """Summarize validation results."""
        counts = {"valid": 0, "broken": 0, "unreachable": 0, "unknown": 0}
        for r in results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return {
            "total": len(results),
            **counts,
            "completeness": round(counts["valid"] / max(len(results), 1), 2),
        }
