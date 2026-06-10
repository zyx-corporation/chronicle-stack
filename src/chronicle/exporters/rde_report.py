"""RDE Diff Record report formatter.

Rendering logic lives here, not in the domain service, so that
section labels can be externalized for i18n (ADR-002).
"""

from chronicle.models.rde import RdeDiffRecord


def format_rde_report(record: RdeDiffRecord) -> str:
    sections = [
        ("Summary", [record.summary] if record.summary else []),
        ("Preserved", record.preserved),
        ("Transformed", record.transformed),
        ("Supplemented", record.supplemented),
        ("Unresolved", record.unresolved),
        ("Deviation Risks", record.deviation_risks),
        ("Next Update Policy", record.next_update_policy),
    ]
    lines = [
        f"# RDE Diff Record: {record.rde_record_id}",
        "",
        f"- Artifact: {record.artifact_id}",
        f"- From: {record.from_version_id}",
        f"- To: {record.to_version_id}",
        f"- Created: {record.created_at.isoformat()}",
        "",
    ]
    for title, items in sections:
        lines.append(f"## {title}")
        lines.append("")
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("(none)")
        lines.append("")
    return "\n".join(lines)
