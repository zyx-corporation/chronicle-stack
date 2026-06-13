"""Export manifest metadata for derived export outputs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExportManifest(BaseModel):
    """Provenance metadata for a derived export.

    This is a traceability record, not a cryptographic proof.
    """

    schema_version: str = "0.4"
    export_format: str
    generated_at: datetime
    chronicle_id: str
    chronicle_title: str = ""
    tool_name: str = "chronicle-stack"
    tool_version: str = "0.0.0+unknown"
    event_count: int = 0
    export_options: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
