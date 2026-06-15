"""Recorded injection plan doctor checks."""

from chronicle.doctor.check_factory import ok, warn
from chronicle.models.doctor import DoctorCheck
from chronicle.models.event import ChronicleEvent


def check_injection_plan_refs(events: list[ChronicleEvent]) -> DoctorCheck:
    context_ids = _context_ids(events)
    missing: set[str] = set()
    for event in events:
        plan = event.payload.get("injection_plan")
        if event.event_type.value != "injection_plan_recorded" or not isinstance(plan, dict):
            continue
        plan_id = plan.get("plan_id", "unknown")
        for section in ("selected", "warned", "excluded"):
            for ref in plan.get(section, []):
                if isinstance(ref, dict) and ref.get("context_id") not in context_ids:
                    missing.add(f"{plan_id}:{section}:{ref.get('context_id')}")

    if missing:
        return warn(
            "recorded_injection_plan_context_refs",
            "recorded InjectionPlans reference missing Contexts",
            detail="; ".join(sorted(missing)),
        )
    return ok(
        "recorded_injection_plan_context_refs",
        "recorded InjectionPlan Context references are valid",
    )


def _context_ids(events: list[ChronicleEvent]) -> set[str]:
    ids: set[str] = set()
    for event in events:
        context = event.payload.get("context")
        if isinstance(context, dict) and context.get("context_id"):
            ids.add(context["context_id"])
    return ids
