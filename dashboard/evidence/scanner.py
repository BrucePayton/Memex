"""
Reference scanner: detects all resource references in raw markdown documents.

Supports 7 reference types:
  - image_md:    Markdown images ![alt](path)
  - image_html:  HTML images <img src="...">
  - file_link:   Markdown file links [text](path)
  - url:         External HTTP/HTTPS URLs
  - sheet_embed: Feishu sheet <sheet sheet-id="...">
  - cite_ref:    Feishu document citation <cite doc-id="...">
  - figure_ref:  Feishu figure <figure href="...">
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Reference:
    """A single resource reference found in a document."""
    ref_type: str          # image_md | image_html | file_link | url | sheet_embed | cite_ref | figure_ref
    location: str          # line number or "L{n}"
    raw_text: str          # the matched text
    target: str            # extracted target (path, URL, or object ID)
    expected_path: str = ""  # resolved local path (for file references)
    line_no: int = 0


class ReferenceScanner:
    """Scan raw markdown documents for resource references."""

    PATTERNS = {
        "image_md": re.compile(r'!\[.*?\]\(([^)]+)\)'),
        "image_html": re.compile(r'<img[^>]+src="([^"]+)"'),
        "file_link": re.compile(r'\[([^\]]+)\]\(([^)]+)\)'),
        "url": re.compile(r'https?://[^\s<>"\']+'),
        "sheet_embed": re.compile(r'<sheet[^>]*sheet-id="([^"]+)"'),
        "cite_ref": re.compile(r'<cite[^>]*doc-id="([^"]+)"'),
        "figure_ref": re.compile(r'<figure[^>]*href="([^"]+)"'),
    }

    # File extensions that are likely local file references (not URLs or images)
    FILE_EXTENSIONS = {".csv", ".pdf", ".doc", ".docx", ".xls", ".xlsx",
                       ".pptx", ".zip", ".json", ".xml", ".txt", ".py",
                       ".md", ".sql", ".png", ".jpg", ".jpeg", ".gif", ".svg"}

    def scan(self, raw_file_path: str | Path, project_root: str | Path = "") -> list[Reference]:
        """Scan a single raw file and return all references found."""
        fpath = Path(raw_file_path)
        if not fpath.exists():
            return []

        text = fpath.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        root = Path(project_root) if project_root else fpath.parent.parent  # default: project root
        references = []

        # line-by-line scan for positional accuracy
        for line_no, line in enumerate(lines, 1):
            # URL detection (exclude markdown image/file link captures)
            for m in self.PATTERNS["url"].finditer(line):
                url = m.group(0)
                # Skip if already captured by image_md or file_link
                if line[m.start()-1:m.start()] == "(" and line[m.start()-2:m.start()-1] == "]":
                    continue
                references.append(Reference(
                    ref_type="url", location=f"L{line_no}",
                    raw_text=url, target=url, line_no=line_no,
                ))

            # Markdown images
            for m in self.PATTERNS["image_md"].finditer(line):
                path = m.group(1)
                if path.startswith("http"):
                    continue  # external URL image, handled by url scanner
                expected = str((root / "raw" / "assets" / Path(path).name).resolve())
                references.append(Reference(
                    ref_type="image_md", location=f"L{line_no}",
                    raw_text=m.group(0), target=path,
                    expected_path=expected, line_no=line_no,
                ))

            # Markdown file links (exclude images)
            for m in self.PATTERNS["file_link"].finditer(line):
                if line[m.start()-1:m.start()] == "!":
                    continue  # it's an image, already handled
                path = m.group(2)
                if path.startswith("http"):
                    continue
                ext = Path(path).suffix.lower()
                if ext in self.FILE_EXTENSIONS:
                    expected = str((root / "raw" / "assets" / Path(path).name).resolve())
                    references.append(Reference(
                        ref_type="file_link", location=f"L{line_no}",
                        raw_text=m.group(0), target=path,
                        expected_path=expected, line_no=line_no,
                    ))

            # HTML images
            for m in self.PATTERNS["image_html"].finditer(line):
                references.append(Reference(
                    ref_type="image_html", location=f"L{line_no}",
                    raw_text=m.group(0), target=m.group(1), line_no=line_no,
                ))

            # Feishu sheet embeds
            for m in self.PATTERNS["sheet_embed"].finditer(line):
                references.append(Reference(
                    ref_type="sheet_embed", location=f"L{line_no}",
                    raw_text=m.group(0), target=m.group(1), line_no=line_no,
                ))

            # Feishu document citations
            for m in self.PATTERNS["cite_ref"].finditer(line):
                references.append(Reference(
                    ref_type="cite_ref", location=f"L{line_no}",
                    raw_text=m.group(0), target=m.group(1), line_no=line_no,
                ))

            # Feishu figure references
            for m in self.PATTERNS["figure_ref"].finditer(line):
                references.append(Reference(
                    ref_type="figure_ref", location=f"L{line_no}",
                    raw_text=m.group(0), target=m.group(1), line_no=line_no,
                ))

        return references

    def scan_all(self, raw_dir: str | Path, project_root: str | Path = "") -> dict[str, list[Reference]]:
        """Scan all files in a raw/ directory and return per-file reference maps."""
        raw_path = Path(raw_dir)
        if not raw_path.is_dir():
            return {}

        result = {}
        for f in sorted(raw_path.glob("**/*")):
            if f.is_file() and f.suffix in (".md", ".txt", ".html"):
                refs = self.scan(f, project_root)
                if refs:
                    result[str(f.relative_to(raw_path.parent))] = refs
        return result
