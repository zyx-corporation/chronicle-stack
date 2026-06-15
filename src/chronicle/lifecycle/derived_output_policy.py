"""Lifecycle-aware policy helpers for derived outputs."""

from dataclasses import dataclass, field
from typing import Any

from chronicle.models.event import ChronicleEvent
from chronicle.models.lifecycle import LifecycleAction, LifecycleEvent

LIFECYCLE_SEALED_RECORD_WARNING = "lifecycle_sealed_record"


@dataclass(frozen=True)
class LifecycleTargetState:
    """Effective lifecycle state for one target record."""

    target_id: str
    actions: frozenset[LifecycleAction] = field(default_factory=frozenset)

    @property
    def is_tombstoned(self) -> bool:
        return LifecycleAction.TOMBSTONE in self.actions or LifecycleAction.HARD_DELETE in self.actions

    @property
    def is_sealed(self) -> bool:
        return LifecycleAction.SEAL in self.actions


LifecycleStateMap = dict[str, LifecycleTargetState]


def lifecycle_state_by_target(events: list[LifecycleEvent]) -> LifecycleStateMap:
    """Build effective lifecycle target states from append-only events.

    This helper is advisory. It does not mutate primary Chronicle records.
    """
    action_map: dict[str, set[LifecycleAction]] = {}
    for event in events:
        action_map.setdefault(event.target_id, set()).add(event.action)
    return {
        target_id: LifecycleTargetState(target_id=target_id, actions=frozenset(actions))
        for target_id, actions in action_map.items()
    }


def lifecycle_state_for(target_id: str, lifecycle_states: LifecycleStateMap) -> LifecycleTargetState:
    """Return the effective lifecycle state for a target, defaulting to active."""
    return lifecycle_states.get(target_id, LifecycleTargetState(target_id))


def is_lifecycle_tombstoned(target_id: str, lifecycle_states: LifecycleStateMap) -> bool:
    """Return whether a target should be omitted from derived outputs."""
    return lifecycle_state_for(target_id, lifecycle_states).is_tombstoned


def lifecycle_seal_metadata(target_id: str, lifecycle_states: LifecycleStateMap) -> dict[str, str]:
    """Return graph/export metadata implied by a sealed lifecycle state."""
    if lifecycle_state_for(target_id, lifecycle_states).is_sealed:
        return {"lifecycle_warning": LIFECYCLE_SEALED_RECORD_WARNING}
    return {}


def event_lifecycle_target_ids(event: ChronicleEvent, *, include_event_fields: bool = False) -> set[str]:
    """Extract lifecycle target IDs directly referenced by a Chronicle event.

    The helper only inspects explicit event fields and known payload containers. It
    does not infer semantic references from free text.
    """
    target_ids: set[str] = set()
    if include_event_fields:
        if event.artifact_id:
            target_ids.add(event.artifact_id)
        if event.decision_id:
            target_ids.add(event.decision_id)
        if event.rde_record_id:
            target_ids.add(event.rde_record_id)
    for key in ("context", "artifact", "decision", "boundary_rule"):
        value = event.payload.get(key)
        if isinstance(value, dict):
            for id_key in ("context_id", "artifact_id", "decision_id", "rule_id"):
                record_id = value.get(id_key)
                if isinstance(record_id, str):
                    target_ids.add(record_id)
    for id_key in ("context_id", "artifact_id", "decision_id", "rule_id", "target_id"):
        record_id = event.payload.get(id_key)
        if isinstance(record_id, str):
            target_ids.add(record_id)
    return target_ids


def event_references_tombstoned_target(
    event: ChronicleEvent,
    lifecycle_states: LifecycleStateMap,
    *,
    include_event_fields: bool = False,
) -> bool:
    """Return whether an event directly references an omitted lifecycle target."""
    return any(
        is_lifecycle_tombstoned(target_id, lifecycle_states)
        for target_id in event_lifecycle_target_ids(event, include_event_fields=include_event_fields)
    )


def count_sealed_targets(target_ids: list[str] | set[str], lifecycle_states: LifecycleStateMap) -> int:
    """Count target IDs with an advisory sealed lifecycle marker."""
    return sum(1 for target_id in target_ids if lifecycle_state_for(target_id, lifecycle_states).is_sealed)


def mark_lifecycle_sealed_warning(
    data: dict[str, Any],
    state: LifecycleTargetState | None,
) -> dict[str, Any]:
    """Return a copy of a dumped record with an advisory sealed warning."""
    if state is None or not state.is_sealed:
        return data
    marked = dict(data)
    warnings = list(marked.get("warnings", []))
    if LIFECYCLE_SEALED_RECORD_WARNING not in warnings:
        warnings.append(LIFECYCLE_SEALED_RECORD_WARNING)
    marked["warnings"] = warnings
    return marked


def package_warnings_for_lifecycle(state: LifecycleTargetState | None) -> list[str]:
    """Return package warnings implied by lifecycle state."""
    if state is None:
        return []
    warnings: list[str] = []
    if state.is_sealed:
        warnings.append(LIFECYCLE_SEALED_RECORD_WARNING)
    return warnings
