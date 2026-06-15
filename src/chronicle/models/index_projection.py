"""Derived index projection models."""

from dataclasses import dataclass, field

from chronicle.models.artifact import Artifact, ArtifactVersion
from chronicle.models.boundary import BoundaryRule
from chronicle.models.context import Context
from chronicle.models.decision import Decision
from chronicle.models.rde import RdeDiffRecord


@dataclass
class IndexProjection:
    """Typed projection data produced from Chronicle events."""

    artifacts: dict[str, Artifact] = field(default_factory=dict)
    versions: dict[str, list[ArtifactVersion]] = field(default_factory=dict)
    contexts: dict[str, Context] = field(default_factory=dict)
    decisions: dict[str, Decision] = field(default_factory=dict)
    rde_records: dict[str, RdeDiffRecord] = field(default_factory=dict)
    boundary_rules: dict[str, BoundaryRule] = field(default_factory=dict)
