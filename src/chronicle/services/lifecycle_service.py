"""Lifecycle service for redact / seal / tombstone events."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.lifecycle import LifecycleAction, LifecycleEvent, LifecycleReasonClass, LifecycleVisibility
from chronicle.services.chronicle_service import ChronicleService
from chronicle.store.lifecycle_store import LifecycleStore


class LifecycleService:
    """Append and read lifecycle events.

    Lifecycle events record decisions about redaction, sealing, expiration,
    tombstones, and hard-delete markers. They do not mutate original records by
    themselves.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.store = LifecycleStore(self.chronicle.paths.lifecycle_file)

    def record(
        self,
        *,
        action: LifecycleAction,
        target_id: str,
        target_kind: str = "unknown",
        actor: str = "unknown",
        reason_class: LifecycleReasonClass = LifecycleReasonClass.OTHER,
        reason: str = "",
        replacement_ref: str | None = None,
        visible_detail_level: LifecycleVisibility = LifecycleVisibility.TOMBSTONE_ONLY,
        preserve_tombstone: bool = True,
        metadata: dict[str, str] | None = None,
    ) -> LifecycleEvent:
        chronicle_metadata = self.chronicle.require_initialized()
        event = LifecycleEvent(
            lifecycle_id=generate_id("lifecycle"),
            chronicle_id=chronicle_metadata.chronicle_id,
            created_at=datetime.now(timezone.utc).astimezone(),
            action=action,
            target_id=target_id,
            target_kind=target_kind,
            actor=actor,
            reason_class=reason_class,
            reason=reason,
            replacement_ref=replacement_ref,
            visible_detail_level=visible_detail_level,
            preserve_tombstone=preserve_tombstone,
            metadata=metadata or {},
        )
        self.store.append(event)
        return event

    def list_events(self) -> list[LifecycleEvent]:
        self.chronicle.require_initialized()
        return self.store.read_all()

    def count_corrupt_lines(self) -> int:
        self.chronicle.require_initialized()
        return self.store.count_corrupt_lines()
