"""Visibility hint for Context and Artifact records (v0.2).

This is NOT a permission or access-control system — it is a
lightweight hint for export filtering, injection planning, and
sensitive-content warnings.
"""

from enum import StrEnum


class VisibilityHint(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    SENSITIVE = "sensitive"
    UNKNOWN = "unknown"
