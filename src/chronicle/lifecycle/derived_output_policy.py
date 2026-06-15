"""Lifecycle-aware policy helpers for derived outputs."""

from dataclasses import dataclass, field

from chronicle.models.lifecycle import LifecycleAction, LifecycleEvent


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


def lifecycle_state_by_target(events: list[LifecycleEvent]) -> dict[str, LifecycleTargetState]:
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


def package_warnings_for_lifecycle(state: LifecycleTargetState | None) -> list[str]:
    """Return package warnings implied by lifecycle state."""
    if state is None:
        return []
    warnings: list[str] = []
    if state.is_sealed:
        warnings.append("lifecycle_sealed_record")
    return warnings
