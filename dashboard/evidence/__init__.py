"""
Evidence chain integrity validation for Memex knowledge projects.

Validates resource references (images, files, URLs, embedded objects)
in raw documents, computes health scores, and manages extensible
validation dimensions.
"""

from .scanner import ReferenceScanner, Reference
from .validator import ReferenceValidator, ValidationResult
from .health import HealthScorer, HealthScore
from .registry import ValidationDimensionRegistry, ValidationDimension

__all__ = [
    "ReferenceScanner", "Reference",
    "ReferenceValidator", "ValidationResult",
    "HealthScorer", "HealthScore",
    "ValidationDimensionRegistry", "ValidationDimension",
]
