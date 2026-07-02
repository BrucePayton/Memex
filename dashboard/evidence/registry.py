"""
Extensible validation dimension registry.

Built-in dimensions are read-only and cannot be deleted. Custom dimensions
are dynamically registered via MCP tools and persisted to .settings.json.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ValidationDimension:
    """A single validation dimension definition."""
    id: str
    name: str
    rule_type: str       # reference | frontmatter | citation | lint | freshness | url_pattern | regex_pattern
    builtin: bool = False
    weight: int = 5
    severity: str = "warning"  # error | warning | info
    description: str = ""
    pattern: str = ""     # regex or URL pattern (for custom dimensions)
    created_at: str = ""
    created_by: str = ""


class ValidationDimensionRegistry:
    """Manage built-in and custom validation dimensions."""

    BUILTIN_DIMENSIONS = {
        "resource_completeness": ValidationDimension(
            id="resource_completeness", name="Resource Completeness",
            rule_type="reference", builtin=True, weight=30,
            description="Validates reachability of all resource references (images/files/links) in raw documents",
        ),
        "card_completeness": ValidationDimension(
            id="card_completeness", name="Card Completeness",
            rule_type="frontmatter", builtin=True, weight=25,
            description="Validates required fields in knowledge cards (missing_sections is empty)",
        ),
        "citation_coverage": ValidationDimension(
            id="citation_coverage", name="Citation Coverage",
            rule_type="citation", builtin=True, weight=20,
            description="Validates [^src-*] citation coverage in wiki pages",
        ),
        "lint_pass_rate": ValidationDimension(
            id="lint_pass_rate", name="Lint Pass Rate",
            rule_type="lint", builtin=True, weight=15,
            description="Proportion of pages passing lint checks",
        ),
        "freshness": ValidationDimension(
            id="freshness", name="Freshness",
            rule_type="freshness", builtin=True, weight=10,
            description="Proportion of active pages with last_updated within 30 days",
        ),
    }

    def __init__(self, project_root: str | Path = ""):
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def _settings_file(self, project_slug: str) -> Path:
        """Get the .settings.json path for a project."""
        return self.project_root / "projects" / project_slug / ".settings.json"

    def _load_custom(self, project_slug: str) -> dict[str, ValidationDimension]:
        """Load custom dimensions from .settings.json."""
        sf = self._settings_file(project_slug)
        if not sf.exists():
            return {}
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            custom = data.get("custom_validation_dimensions", {})
            result = {}
            for dim_id, dim_data in custom.items():
                result[dim_id] = ValidationDimension(
                    id=dim_id, builtin=False, **{k: v for k, v in dim_data.items()
                        if k in ("name", "rule_type", "weight", "severity", "description",
                                 "pattern", "created_at", "created_by")},
                )
            return result
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_custom(self, project_slug: str, custom: dict[str, dict]) -> None:
        """Save custom dimensions to .settings.json."""
        sf = self._settings_file(project_slug)
        sf.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if sf.exists():
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        data["custom_validation_dimensions"] = custom
        sf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_all_dimensions(self, project_slug: str) -> list[ValidationDimension]:
        """Return built-in + custom dimensions, with weights scaled to sum 100."""
        builtin = list(self.BUILTIN_DIMENSIONS.values())
        custom_dims = self._load_custom(project_slug)
        all_dims = builtin + list(custom_dims.values())

        total_weight = sum(d.weight for d in all_dims)
        if total_weight == 0:
            return all_dims

        scale = 100.0 / total_weight
        result = []
        for d in all_dims:
            result.append(ValidationDimension(
                id=d.id, name=d.name, rule_type=d.rule_type,
                builtin=d.builtin,
                weight=round(d.weight * scale, 1),
                severity=d.severity, description=d.description,
                pattern=d.pattern, created_at=d.created_at, created_by=d.created_by,
            ))
        return result

    def add_custom_dimension(self, project_slug: str, dim: ValidationDimension) -> dict:
        """Add a custom validation dimension."""
        custom = self._load_custom(project_slug)
        if dim.id in custom:
            return {"ok": False, "error": f"dimension already exists: {dim.id}"}
        if dim.id in self.BUILTIN_DIMENSIONS:
            return {"ok": False, "error": f"cannot override built-in dimension: {dim.id}"}

        dim.builtin = False
        dim.created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        custom[dim.id] = {
            "name": dim.name, "rule_type": dim.rule_type,
            "weight": dim.weight, "severity": dim.severity,
            "description": dim.description, "pattern": dim.pattern,
            "created_at": dim.created_at, "created_by": dim.created_by,
        }
        self._save_custom(project_slug, custom)
        return {"ok": True, "dimension": dim}

    def remove_custom_dimension(self, project_slug: str, dim_id: str) -> dict:
        """Remove a custom dimension. Built-in dimensions cannot be removed."""
        if dim_id in self.BUILTIN_DIMENSIONS:
            return {"ok": False, "error": f"built-in dimensions cannot be removed: {dim_id}"}
        custom = self._load_custom(project_slug)
        if dim_id not in custom:
            return {"ok": False, "error": f"dimension not found: {dim_id}"}
        removed = custom.pop(dim_id)
        self._save_custom(project_slug, custom)
        return {"ok": True, "removed": removed}

    def update_custom_dimension(self, project_slug: str, dim_id: str, updates: dict) -> dict:
        """Update a custom dimension's configuration."""
        custom = self._load_custom(project_slug)
        if dim_id not in custom:
            return {"ok": False, "error": f"dimension not found: {dim_id}"}
        allowed = {"name", "rule_type", "weight", "severity", "description", "pattern"}
        for k, v in updates.items():
            if k in allowed:
                custom[dim_id][k] = v
        self._save_custom(project_slug, custom)
        return {"ok": True, "dimension": custom[dim_id]}

    def reset_custom_dimensions(self, project_slug: str) -> dict:
        """Remove all custom dimensions, restoring to built-in defaults."""
        sf = self._settings_file(project_slug)
        if sf.exists():
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
                count = len(data.pop("custom_validation_dimensions", {}))
                sf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                return {"ok": True, "restored_count": count}
            except (json.JSONDecodeError, OSError):
                pass
        return {"ok": True, "restored_count": 0}
