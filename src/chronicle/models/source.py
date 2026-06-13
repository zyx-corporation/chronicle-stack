"""Source provenance metadata (v0.2).

Captures structured information about where an Event, Context, or
Artifact originated.  This is a *record* of provenance, not a
cryptographic proof of truth.
"""

from datetime import datetime

from pydantic import BaseModel


class SourceProvenance(BaseModel):
    """Structured source metadata.

    The minimal fields ``source_type`` and ``source_ref`` are
    compatible with v0.1 :class:`SourceRef`.

    All additional fields are optional — provenance is recorded only
    when explicitly provided.
    """

    source_type: str = "unknown"
    source_ref: str = ""
    source_tool: str | None = None
    source_session: str | None = None
    source_model: str | None = None
    source_file: str | None = None
    source_url: str | None = None
    captured_at: datetime | None = None
    imported_at: datetime | None = None
