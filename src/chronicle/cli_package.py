"""Auxiliary CLI for controlled integration packages."""

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.event import Actor, Confidence, EventType, ReviewStatus
from chronicle.models.integration_package import IntegrationPackageRecord, IntegrationTargetEnvironment
from chronicle.models.integration_adapter import QueryEngineTrialRecord
from chronicle.models.package_review import PackageReviewStatus
from chronicle.models.source import SourceProvenance
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.integration_package_service import IntegrationPackageService
from chronicle.services.package_review_service import PackageReviewService
from chronicle.services.runtime_service import RuntimeService

package_app = typer.Typer(
    name="chronicle-package",
    help="Chronicle Stack controlled integration package contracts.",
    no_args_is_help=True,
)


def _record_summary(record: IntegrationPackageRecord) -> dict[str, Any]:
    """Return a package record summary without body content."""
    return {
        "record_id": record.record_id,
        "record_kind": record.record_kind,
        "title": record.title,
        "classification_layer": record.classification_layer,
        "sensitivity": record.sensitivity,
        "allowed_operations": record.allowed_operations,
        "content_boundary": record.content_boundary.value,
        "has_content": record.content is not None,
        "warnings": record.warnings,
        "metadata": record.metadata,
    }


def _query_engine_bundle_acceptance_checklist(*, query: str) -> str:
    return "\n".join(
        [
            "# Query-Engine Handoff Bundle Acceptance Checklist",
            "",
            f"- Query: `{query}`",
            "- [ ] `query_engine_handoff.json` is present and parses successfully",
            "- [ ] `query_engine_adapter_skeleton.json` is present and remains descriptive only",
            "- [ ] `graph.json` is present and matches the expected `graph-json` contract version",
            "- [ ] `bundle_manifest.json` is present and lists every emitted file",
            "- [ ] `import_validation.status` is reviewed as a structural signal only",
            "- [ ] no consumer treats derived bundle files as authoritative over `.chronicle/chronicle.jsonl`",
            "- [ ] no consumer assumes hosted query execution, graph runtime, or vector runtime inside Chronicle Stack",
            "- [ ] a downstream implementation repo is requested only if this bundle is insufficient",
            "",
            "Boundary:",
            "- local read-only bundle only",
            "- no downstream import execution inside Chronicle Stack",
            "- no mutation of `.chronicle/chronicle.jsonl`",
        ]
    )


def _query_engine_bundle_trial_report_template(*, query: str) -> str:
    return "\n".join(
        [
            "# Query-Engine Handoff Bundle Trial Report",
            "",
            f"- Query: `{query}`",
            "- Trial date:",
            "- Reviewer:",
            "- Downstream consumer or repo:",
            "",
            "## Files reviewed",
            "",
            "- [ ] `query_engine_handoff.json`",
            "- [ ] `query_engine_adapter_skeleton.json`",
            "- [ ] `graph.json`",
            "- [ ] `bundle_manifest.json`",
            "- [ ] `ACCEPTANCE_CHECKLIST.md`",
            "",
            "## Structural findings",
            "",
            "- Import-validation status observed:",
            "- Contract/version mismatches:",
            "- Missing files or parse errors:",
            "",
            "## Sufficiency decision",
            "",
            "- [ ] Bundle was sufficient for downstream trial",
            "- [ ] Bundle was insufficient for downstream trial",
            "- If insufficient, describe the missing behavior:",
            "",
            "## Boundary confirmation",
            "",
            "- [ ] Chronicle primary records remained authoritative",
            "- [ ] No hosted query execution was expected from Chronicle Stack",
            "- [ ] No downstream import execution was expected inside Chronicle Stack",
            "- [ ] Any requested next step stays outside Chronicle Stack core",
        ]
    )


def _load_bundle_manifest(bundle_dir: Path) -> dict[str, Any]:
    manifest_path = bundle_dir / "bundle_manifest.json"
    if not bundle_dir.exists():
        raise ChronicleError(
            code="QUERY_ENGINE_BUNDLE_DIR_NOT_FOUND",
            message=f"Query-engine bundle directory not found: {bundle_dir}",
            hint="Generate one with `chronicle package query-engine-bundle --query ... --output-dir ...` first.",
        )
    if not manifest_path.exists():
        raise ChronicleError(
            code="QUERY_ENGINE_BUNDLE_MANIFEST_NOT_FOUND",
            message=f"Bundle manifest not found: {manifest_path}",
            hint="Re-generate the bundle so `bundle_manifest.json` is present.",
        )
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ChronicleError(
            code="QUERY_ENGINE_BUNDLE_MANIFEST_INVALID",
            message=f"Bundle manifest is not valid JSON: {manifest_path}",
            hint=str(exc),
        ) from exc


def _query_engine_trial_record_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {}).get("query_engine_trial_record", {})
    return {
        "event_id": event.get("event_id", ""),
        "summary": event.get("summary", ""),
        "query": payload.get("query", ""),
        "reviewer": payload.get("reviewer", ""),
        "downstream_consumer": payload.get("downstream_consumer", ""),
        "sufficient": bool(payload.get("sufficient", False)),
        "import_validation_status": payload.get("import_validation_status", "advisory_only"),
        "import_ready": bool(payload.get("import_ready", False)),
        "missing_behavior": payload.get("missing_behavior", ""),
    }


def _list_query_engine_trial_records() -> list[dict[str, Any]]:
    events = ChronicleService().jsonl.read_all(skip_corrupt=True)
    records: list[dict[str, Any]] = []
    for event in events:
        dumped = event.model_dump(mode="json")
        payload = dumped.get("payload", {})
        trial_payload = payload.get("query_engine_trial_record")
        if dumped.get("event_type") != EventType.ASSISTANT_OUTPUT.value or not isinstance(trial_payload, dict):
            continue
        if trial_payload.get("record_kind") != "query_engine_bundle_trial":
            continue
        records.append(dumped)
    records.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return records


@package_app.command("context")
def context_package_cmd(
    purpose: Annotated[str, typer.Option("--purpose", help="Purpose for building the package.")],
    target: Annotated[IntegrationTargetEnvironment, typer.Option("--target", help="Target environment: local or external.")] = IntegrationTargetEnvironment.LOCAL,
    context_id: Annotated[list[str] | None, typer.Option("--context", help="Context ID to include. Repeatable. If omitted, all contexts are included.")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    persist: Annotated[bool, typer.Option("--persist", help="Persist the package under .chronicle/packages.")] = False,
) -> None:
    """Build a controlled context package.

    This command does not call models, graph databases, vector databases, or
    external runtimes.
    """
    service = IntegrationPackageService()
    package = service.build_context_package(
        purpose=purpose,
        target_environment=target,
        context_ids=context_id,
    )
    if persist:
        package_dir = service.save_package(package)
        typer.echo(f"Package persisted: {package.manifest.package_id}")
        typer.echo(f"  Path: {package_dir}")
        return

    payload = json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if output:
        output.write_text(payload, encoding="utf-8")
        typer.echo(f"Package written to {output}")
    else:
        typer.echo(payload)


@package_app.command("query-engine-adapter")
def query_engine_adapter_cmd(
    query: Annotated[str, typer.Option("--query", help="Query to assemble a local downstream adapter skeleton for.")],
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum hits per retrieval surface.")] = 5,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """Build a descriptive downstream query-engine adapter skeleton.

    This command stays local, dry-run, and read-only. It does not execute
    imports, hosted query engines, or external runtimes.
    """
    try:
        plan = RuntimeService().retrieve_plan(query=query, limit=limit, record=False)
        handoff = plan.query_engine_handoff
        if handoff is None:
            raise ChronicleError(
                code="QUERY_ENGINE_HANDOFF_UNAVAILABLE",
                message="Query-engine handoff is unavailable for this retrieval plan.",
                hint="Run `chronicle runtime retrieve-plan --query ... --json` to inspect the current dry-run handoff surface.",
            )
        skeleton = IntegrationPackageService().build_query_engine_adapter_skeleton(handoff)
        payload = json.dumps(skeleton.model_dump(mode="json"), ensure_ascii=False, indent=2)
        if output:
            output.write_text(payload, encoding="utf-8")
            typer.echo(f"Adapter skeleton written to {output}")
            return
        typer.echo(payload)
    except ChronicleError as exc:
        handle_error(exc, json_output=True)


@package_app.command("query-engine-bundle")
def query_engine_bundle_cmd(
    query: Annotated[str, typer.Option("--query", help="Query to assemble a local downstream handoff bundle for.")],
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Directory to write the downstream handoff bundle into.")],
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum hits per retrieval surface.")] = 5,
) -> None:
    """Write a local downstream handoff bundle.

    The bundle is descriptive only: handoff JSON, adapter skeleton, graph export,
    and a small bundle manifest. It does not execute imports or hosted runtimes.
    """
    try:
        plan = RuntimeService().retrieve_plan(query=query, limit=limit, record=False)
        handoff = plan.query_engine_handoff
        if handoff is None:
            raise ChronicleError(
                code="QUERY_ENGINE_HANDOFF_UNAVAILABLE",
                message="Query-engine handoff is unavailable for this retrieval plan.",
                hint="Run `chronicle runtime retrieve-plan --query ... --json` to inspect the current dry-run handoff surface.",
            )
        service = IntegrationPackageService()
        graph_export = GraphExportService().export_graph()
        skeleton = service.build_query_engine_adapter_skeleton(handoff)
        manifest = service.build_query_engine_handoff_bundle_manifest(handoff, graph_export)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "query_engine_handoff.json").write_text(
            json.dumps(handoff.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "query_engine_adapter_skeleton.json").write_text(
            json.dumps(skeleton.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "graph.json").write_text(
            json.dumps(graph_export.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "bundle_manifest.json").write_text(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "ACCEPTANCE_CHECKLIST.md").write_text(
            _query_engine_bundle_acceptance_checklist(query=query),
            encoding="utf-8",
        )
        (output_dir / "TRIAL_REPORT_TEMPLATE.md").write_text(
            _query_engine_bundle_trial_report_template(query=query),
            encoding="utf-8",
        )
        typer.echo(f"Query-engine handoff bundle written to {output_dir}")
    except ChronicleError as exc:
        handle_error(exc, json_output=True)


@package_app.command("query-engine-trial-record")
def query_engine_trial_record_cmd(
    bundle_dir: Annotated[Path, typer.Option("--bundle-dir", help="Existing downstream handoff bundle directory.")],
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer recording the downstream trial result.")],
    downstream_consumer: Annotated[str, typer.Option("--consumer", help="Downstream consumer or repo name.")],
    sufficient: Annotated[bool, typer.Option("--sufficient/--insufficient", help="Whether the bundle was sufficient for the downstream trial.")] = False,
    missing_behavior: Annotated[str, typer.Option("--missing-behavior", help="Describe missing behavior if the bundle was insufficient.")] = "",
    note: Annotated[list[str] | None, typer.Option("--note", help="Additional review note. Repeatable.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a downstream query-engine bundle trial as a Chronicle assistant_output event."""
    try:
        manifest = _load_bundle_manifest(bundle_dir)
        trial_record = QueryEngineTrialRecord(
            query=str(manifest.get("query", "")),
            bundle_dir=str(bundle_dir),
            reviewer=reviewer,
            downstream_consumer=downstream_consumer,
            sufficient=sufficient,
            files_reviewed=[str(item) for item in manifest.get("files", [])],
            import_validation_status=str(manifest.get("import_validation_status", "advisory_only")),
            import_ready=bool(manifest.get("import_ready", False)),
            missing_behavior=missing_behavior if not sufficient else "",
            notes=list(note or []),
        )
        event = ChronicleService().record_event(
            event_type=EventType.ASSISTANT_OUTPUT,
            actor=Actor.ASSISTANT,
            summary=(
                f"Query-engine bundle trial recorded: {'sufficient' if sufficient else 'insufficient'}"
            ),
            payload={
                "query_engine_trial_record": trial_record.model_dump(mode="json"),
                "bundle_manifest_path": str(bundle_dir / "bundle_manifest.json"),
            },
            source=SourceProvenance(
                source_type="file",
                source_ref=str(bundle_dir),
                source_tool="chronicle-package",
                source_file=str(bundle_dir / "TRIAL_REPORT_TEMPLATE.md"),
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
            confidence=Confidence.LOW,
        )
        if json_output:
            typer.echo(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return
        typer.echo(f"Trial record event: {event.event_id}")
        typer.echo(f"  Reviewer: {reviewer}")
        typer.echo(f"  Consumer: {downstream_consumer}")
        typer.echo(f"  Sufficient: {sufficient}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@package_app.command("query-engine-trial-list")
def query_engine_trial_list_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List recorded downstream query-engine bundle trials."""
    try:
        ChronicleService().require_initialized()
        records = [_query_engine_trial_record_summary(event) for event in _list_query_engine_trial_records()]
        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return
        if not records:
            typer.echo("No query-engine trial records found.")
            return
        for record in records:
            typer.echo(
                f"{record['event_id']}  sufficient={record['sufficient']}  "
                f"reviewer={record['reviewer']}  consumer={record['downstream_consumer']}"
            )
    except ChronicleError as exc:
        handle_error(exc, json_output)


@package_app.command("query-engine-trial-show")
def query_engine_trial_show_cmd(
    event_id: Annotated[str, typer.Option("--event", help="Recorded query-engine trial event ID.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show one recorded downstream query-engine bundle trial."""
    try:
        ChronicleService().require_initialized()
        for event in _list_query_engine_trial_records():
            if event.get("event_id") == event_id:
                if json_output:
                    typer.echo(json.dumps(event, ensure_ascii=False, indent=2))
                    return
                record = _query_engine_trial_record_summary(event)
                typer.echo(f"Trial event: {record['event_id']}")
                typer.echo(f"  Query: {record['query']}")
                typer.echo(f"  Reviewer: {record['reviewer']}")
                typer.echo(f"  Consumer: {record['downstream_consumer']}")
                typer.echo(f"  Sufficient: {record['sufficient']}")
                typer.echo(f"  Import validation: {record['import_validation_status']}")
                if record["missing_behavior"]:
                    typer.echo(f"  Missing behavior: {record['missing_behavior']}")
                return
        raise ChronicleError(
            code="QUERY_ENGINE_TRIAL_RECORD_NOT_FOUND",
            message=f"Query-engine trial record not found: {event_id}",
            hint="Run `chronicle package query-engine-trial-list --json` to inspect available trial events.",
        )
    except ChronicleError as exc:
        handle_error(exc, json_output)


@package_app.command("review")
def review_package_cmd(
    purpose: Annotated[str | None, typer.Option("--purpose", help="Purpose for reviewing a new context package.")] = None,
    target: Annotated[IntegrationTargetEnvironment, typer.Option("--target", help="Target environment: local or external.")] = IntegrationTargetEnvironment.LOCAL,
    context_id: Annotated[list[str] | None, typer.Option("--context", help="Context ID to include. Repeatable. If omitted, all contexts are checked.")] = None,
    package: Annotated[str | None, typer.Option("--package", help="Persisted package ID to review.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Review a package before persistence or handoff.

    Review is diagnostic. It does not call external runtimes and does not certify correctness.
    """
    service = PackageReviewService()
    if package:
        report = service.review_persisted_package(package)
    else:
        report = service.review_context_package(
            purpose=purpose or "package review",
            target_environment=target,
            context_ids=context_id,
        )

    if json_output:
        typer.echo(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        typer.echo("Chronicle Package Review")
        typer.echo(f"Status: {report.status.value}")
        typer.echo(f"Purpose: {report.purpose}")
        typer.echo(f"Target: {report.target_environment}")
        typer.echo(f"Records: {report.record_count}")
        typer.echo(f"Output classification: {report.output_classification}")
        for finding in report.findings:
            prefix = finding.record_id or "package"
            typer.echo(f"[{finding.severity.value}] {prefix}: {finding.code}")
            if finding.recommendation:
                typer.echo(f"  Recommendation: {finding.recommendation}")
        typer.echo("Boundary: package review is diagnostic, not certification.")

    if report.status == PackageReviewStatus.BLOCKED:
        raise typer.Exit(code=1)


@package_app.command("list")
def list_packages_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List persisted integration packages."""
    manifests = IntegrationPackageService().list_package_manifests()
    if json_output:
        typer.echo(json.dumps([manifest.model_dump(mode="json") for manifest in manifests], ensure_ascii=False, indent=2))
        return

    if not manifests:
        typer.echo("No persisted packages found.")
        return

    for manifest in manifests:
        typer.echo(
            f"{manifest.package_id}  {manifest.package_kind.value}  "
            f"{manifest.output_classification}  {len(manifest.referenced_records)} record(s)"
        )


@package_app.command("show")
def show_package_cmd(
    package: Annotated[str, typer.Option("--package", help="Package ID to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show a persisted package manifest."""
    manifest = IntegrationPackageService().load_package_manifest(package)
    if json_output:
        typer.echo(json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    typer.echo(f"Package: {manifest.package_id}")
    typer.echo(f"  Kind: {manifest.package_kind.value}")
    typer.echo(f"  Purpose: {manifest.purpose}")
    typer.echo(f"  Target: {manifest.target_environment.value}")
    typer.echo(f"  Output classification: {manifest.output_classification}")
    typer.echo(f"  Referenced records: {len(manifest.referenced_records)}")
    if manifest.warnings:
        typer.echo(f"  Warnings: {', '.join(manifest.warnings)}")


@package_app.command("records")
def package_records_cmd(
    package: Annotated[str, typer.Option("--package", help="Package ID to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show persisted package record summaries without body content."""
    records = IntegrationPackageService().load_package_records(package)
    summaries = [_record_summary(record) for record in records]
    if json_output:
        typer.echo(json.dumps(summaries, ensure_ascii=False, indent=2))
        return

    if not summaries:
        typer.echo("No records found.")
        return
    for summary in summaries:
        typer.echo(
            f"{summary['record_id']}  {summary['record_kind']}  "
            f"{summary['content_boundary']}  has_content={summary['has_content']}"
        )
        if summary["warnings"]:
            typer.echo(f"  Warnings: {', '.join(summary['warnings'])}")


if __name__ == "__main__":
    package_app()
