"""Context Injection Plan service (v0.2)."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.event import Actor, ChronicleEvent, EventType
from chronicle.models.injection import InjectionPlan, InjectionPlanContextRef
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService


class InjectionPlanService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.boundary = BoundaryService(root)

    def generate_plan(self, task: str) -> InjectionPlan:
        self.chronicle.require_initialized()
        now = datetime.now(timezone.utc).astimezone()

        contexts = self.chronicle.index.load_contexts()
        rules = [r for r in self.boundary.list_rules() if r.enabled]

        plan = InjectionPlan(
            plan_id=generate_id("injection_plan"),
            task=task,
            created_at=now,
        )

        for ctx in contexts.values():
            ref = InjectionPlanContextRef(
                context_id=ctx.context_id,
                title=ctx.title,
                scope=ctx.scope.value,
                visibility_hint=ctx.visibility_hint.value,
            )

            exclude_reasons: list[str] = []
            warn_reasons: list[str] = []
            include_reasons: list[str] = []

            for rule in rules:
                evaluation = self.boundary._evaluate_rule(rule, ctx)
                if not evaluation.matched:
                    continue
                if rule.rule_type.value == "exclude":
                    exclude_reasons.append(evaluation.reason)
                elif rule.rule_type.value == "warn":
                    warn_reasons.append(evaluation.reason)
                elif rule.rule_type.value == "include":
                    include_reasons.append(evaluation.reason)

            if exclude_reasons:
                ref.reason = "; ".join(exclude_reasons)
                plan.excluded.append(ref)
            else:
                if include_reasons:
                    ref.reason = "; ".join(include_reasons)
                    ref.matched_rules = include_reasons
                else:
                    ref.reason = "default candidate"
                plan.selected.append(ref)

                if warn_reasons:
                    ref.warnings = warn_reasons
                    plan.warned.append(ref)

        plan.notes.append(
            "This plan is a human-reviewable suggestion. It does NOT inject context into any LLM. "
            "It does NOT persist to chronicle.jsonl by default."
        )
        return plan

    def record_plan(self, plan: InjectionPlan) -> ChronicleEvent:
        """Record an InjectionPlan as a persisted event in chronicle.jsonl."""
        self.chronicle.require_initialized()
        event = self.chronicle.record_event(
            event_type=EventType.INJECTION_PLAN_RECORDED,
            actor=Actor.SYSTEM,
            summary=f"Injection plan recorded: {plan.task}",
            payload={"injection_plan": plan.model_dump(mode="json")},
        )
        return event
