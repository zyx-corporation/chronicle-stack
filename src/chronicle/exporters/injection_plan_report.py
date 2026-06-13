"""Markdown formatter for InjectionPlan."""

from chronicle.models.injection import InjectionPlan


def format_injection_plan(plan: InjectionPlan) -> str:
    lines = [
        f"# Context Injection Plan: {plan.plan_id}",
        "",
        f"Task: {plan.task}",
        "",
        "## Selected",
        "",
    ]
    if plan.selected:
        for ctx in plan.selected:
            warnings = f"  ⚠ {', '.join(ctx.warnings)}" if ctx.warnings else ""
            lines.append(
                f"- `{ctx.context_id}` **{ctx.title}** "
                f"(scope={ctx.scope}, visibility={ctx.visibility_hint})"
            )
            lines.append(f"  reason: {ctx.reason}")
            if warnings:
                lines.append(f"  {warnings}")
    else:
        lines.append("(none)")

    lines.extend(["", "## Warned", ""])
    if plan.warned:
        for ctx in plan.warned:
            warnings = ", ".join(ctx.warnings)
            lines.append(
                f"- `{ctx.context_id}` **{ctx.title}** "
                f"(scope={ctx.scope}, visibility={ctx.visibility_hint})"
            )
            lines.append(f"  warning: {warnings}")
    else:
        lines.append("(none)")

    lines.extend(["", "## Excluded", ""])
    if plan.excluded:
        for ctx in plan.excluded:
            lines.append(
                f"- `{ctx.context_id}` **{ctx.title}** "
                f"(scope={ctx.scope}, visibility={ctx.visibility_hint})"
            )
            lines.append(f"  reason: {ctx.reason}")
    else:
        lines.append("(none)")

    if plan.notes:
        lines.extend(["", "## Notes", ""])
        for note in plan.notes:
            lines.append(f"- {note}")

    return "\n".join(lines)
