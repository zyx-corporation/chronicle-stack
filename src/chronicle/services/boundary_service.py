"""Context Boundary Rule service (v0.2)."""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.ids import generate_id
from chronicle.models.boundary import (
    BoundaryConditionField,
    BoundaryEvaluation,
    BoundaryOperator,
    BoundaryRule,
    BoundaryRuleType,
)
from chronicle.models.context import Context
from chronicle.models.event import Actor, EventType
from chronicle.services.chronicle_service import ChronicleService


class BoundaryService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def add_rule(
        self,
        rule_type: BoundaryRuleType,
        field: BoundaryConditionField,
        operator: BoundaryOperator,
        value: str | list[str],
        reason: str = "",
        tags: list[str] | None = None,
    ) -> BoundaryRule:
        self.chronicle.require_initialized()
        now = datetime.now(timezone.utc).astimezone()
        rule = BoundaryRule(
            rule_id=generate_id("boundary_rule"),
            rule_type=rule_type,
            field=field,
            operator=operator,
            value=value,
            reason=reason,
            created_at=now,
            tags=tags or [],
        )
        self.chronicle.record_event(
            event_type=EventType.BOUNDARY_RULE_ADDED,
            actor=Actor.USER,
            summary=f"Boundary rule added: {rule_type.value} on {field.value}",
            payload={"boundary_rule": rule.model_dump(mode="json")},
        )
        self.chronicle.rebuild_indexes()
        return rule

    def list_rules(self) -> list[BoundaryRule]:
        self.chronicle.require_initialized()
        return list(self.chronicle.index.load_boundary_rules().values())

    def _get_context_value(self, context: Context, field: BoundaryConditionField) -> str | list[str]:
        """Extract the value from a Context for a given field."""
        if field == BoundaryConditionField.SCOPE:
            return context.scope.value
        elif field == BoundaryConditionField.VISIBILITY:
            return context.visibility_hint.value
        elif field == BoundaryConditionField.SOURCE_TYPE:
            return context.source_type
        elif field == BoundaryConditionField.SOURCE_TOOL:
            if context.source:
                return context.source.source_tool or ""
            return ""
        elif field == BoundaryConditionField.SOURCE_SESSION:
            if context.source:
                return context.source.source_session or ""
            return ""
        elif field == BoundaryConditionField.SOURCE_MODEL:
            if context.source:
                return context.source.source_model or ""
            return ""
        elif field == BoundaryConditionField.TAG:
            return context.tags
        return ""

    def _evaluate_rule(self, rule: BoundaryRule, context: Context) -> BoundaryEvaluation:
        ctx_val = self._get_context_value(context, rule.field)

        matched = False
        if rule.operator == BoundaryOperator.EQUALS:
            matched = ctx_val == rule.value
        elif rule.operator == BoundaryOperator.NOT_EQUALS:
            matched = ctx_val != rule.value
        elif rule.operator == BoundaryOperator.IN:
            if isinstance(rule.value, list):
                matched = ctx_val in rule.value
            else:
                # Single string value — check if it's in the list-context value
                if isinstance(ctx_val, list):
                    matched = rule.value in ctx_val
                else:
                    matched = ctx_val == rule.value
        elif rule.operator == BoundaryOperator.CONTAINS:
            if isinstance(ctx_val, list):
                if isinstance(rule.value, list):
                    matched = any(v in ctx_val for v in rule.value)
                else:
                    matched = rule.value in ctx_val
            else:
                if isinstance(rule.value, list):
                    matched = any(v in ctx_val for v in rule.value)
                else:
                    matched = rule.value in str(ctx_val)

        return BoundaryEvaluation(
            rule_id=rule.rule_id,
            rule_type=rule.rule_type,
            matched=matched,
            reason=rule.reason if matched else "",
        )

    def evaluate_context(self, context: Context) -> list[BoundaryEvaluation]:
        rules = self.list_rules()
        return [self._evaluate_rule(rule, context) for rule in rules]
