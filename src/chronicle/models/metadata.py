"""Chronicle metadata model."""

from datetime import datetime

from pydantic import BaseModel


class ChronicleMetadata(BaseModel):
    chronicle_id: str
    title: str
    created_at: datetime
    version: str = "0.1"
    schema_version: str = "chronicle-core-0.1"
    default_timezone: str = "Asia/Tokyo"
