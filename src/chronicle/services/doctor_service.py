"""Read-only Chronicle health checks."""

import json
from pathlib import Path

import yaml

from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.models.classification import AllowedOperation, ClassificationLayer
from chronicle.models.context import Context
from chronicle.models.doctor import DoctorCheck, DoctorReport, DoctorSeverity
from chronicle.models.event import ChronicleEvent, EventType
from chronicle.models.metadata import ChronicleMetadata
from chronicle.security.prompt_injection import scan_text_for_prompt_injection
from chronicle.services.graph_export_service import GraphExportService
from chronicle.store.audit_log_store import AuditLogStore
from chronicle.store.lifecycle_store import LifecycleStore
from chronicle.store.paths import ChroniclePaths


class DoctorService:
    """Run read-only diagnostics against a Chronicle project."""

    def __init__(self, root: Path | None = None) -> None:
        self.paths = ChroniclePaths(root)
        self.root = self.paths.root

    def run(self) -> DoctorReport:
        checks: list[DoctorCheck] = []
        metadata = self._load_metadata(checks)
        events = self._read_events(checks)
        chronicle_id = metadata.chronicle_id if metadata else None

        self._check_required_files(checks)
        self._check_known_event_types(checks, events)
        self._check_indexes(checks)
        self._check_artifact_files(checks, events)
        self._check_injection_plan_refs(checks, events)
        self._check_security_metadata(checks, events)
        self._check_audit_lifecycle_surfaces(checks)
        self._check_exports(checks)

        return DoctorReport.from_checks(checks, chronicle_id=chronicle_id)

    @staticmethod
    def _check(
        check_id: str,
        severity: DoctorSeverity,
        summary: str,
        detail: str = "",
        recommendation: str = "",
    ) -> DoctorCheck:
        return DoctorCheck(
            check_id=check_id,
            severity=severity,
            summary=summary,
            detail=detail,
            recommendation=recommendation,
        )

    def _ok(self, check_id: str, summary: str, detail: str = "") -> DoctorCheck:
        return self._check(check_id, DoctorSeverity.OK, summary, detail)

    def _warn(
        self,
        check_id: str,
        summary: str,
        detail: str = "",
        recommendation: str = "",
    ) -> DoctorCheck:
        return self._check(
            check_id,
            DoctorSeverity.WARNING,
            summary,
            detail,
            recommendation,
        )

    def _err(
        self,
        check_id: str,
        summary: str,
        detail: str = "",
        recommendation: str = "",
    ) -> DoctorCheck:
        return self._check(
            check_id,
            DoctorSeverity.ERROR,
            summary,
            detail,
            recommendation,
        )

    def _check_required_files(self, checks: list[DoctorCheck]) -> None:
        if self.paths.chronicle_dir.exists():
            checks.append(self._ok("chronicle_dir_exists", ".chronicle directory exists"))
        else:
            checks.append(
                self._err(
                    "chronicle_dir_exists",
                    ".chronicle directory is missing",
                    recommendation="run `chronicle init --title ...`",
                )
            )

        if self.paths.events_file.exists():
            checks.append(self._ok("chronicle_jsonl_exists", "chronicle.jsonl exists"))
        else:
            checks.append(
                self._err(
                    "chronicle_jsonl_exists",
                    "chronicle.jsonl is missing",
                    recommendation="run `chronicle init --title ...`",
                )
            )

        if self.paths.metadata_file.exists():
            checks.append(self._ok("metadata_exists", "metadata.yaml exists"))
        else:
            checks.append(
                self._warn(
                    "metadata_exists",
                    "metadata.yaml is missing",
                    recommendation="restore metadata.yaml or re-initialize carefully",
                )
            )

    def _load_metadata(self, checks: list[DoctorCheck]) -> ChronicleMetadata | None:
        if not self.paths.metadata_file.exists():
            return None
        try:
            raw = yaml.safe_load(self.paths.metadata_file.read_text(encoding="utf-8"))
            metadata = ChronicleMetadata.model_validate(raw)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            checks.append(
                self._err(
                    "metadata_parseable",
                    "metadata.yaml could not be parsed",
                    detail=str(exc),
                )
            )
            return None
        checks.append(self._ok("metadata_parseable", "metadata.yaml is parseable"))
        return metadata

    def _read_events(self, checks: list[DoctorCheck]) -> list[ChronicleEvent]:
        if not self.paths.events_file.exists():
            return []

        events: list[ChronicleEvent] = []
        errors: list[str] = []
        with self.paths.events_file.open(encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    events.append(ChronicleEvent.model_validate(data))
                except (json.JSONDecodeError, ValueError) as exc:
                    errors.append(f"line {line_number}: {exc}")

        if errors:
            checks.append(
                self._err(
                    "jsonl_parseable",
                    "chronicle.jsonl contains parse errors",
                    detail="; ".join(errors),
                    recommendation="repair or remove corrupted JSONL lines",
                )
            )
        else:
            detail = f"{len(events)} event(s)"
            checks.append(self._ok("jsonl_parseable", "chronicle.jsonl is parseable", detail))
        return events

    def _check_known_event_types(
        self,
        checks: list[DoctorCheck],
        events: list[ChronicleEvent],
    ) -> None:
        known = {event_type.value for event_type in EventType}
        unknown = sorted({event.event_type.value for event in events if event.event_type.value not in known})
        if unknown:
            checks.append(
                self._warn(
                    "known_event_types",
                    "chronicle.jsonl contains unknown event types",
                    detail=", ".join(unknown),
                )
            )
        else:
            checks.append(self._ok("known_event_types", "all event types are known"))

    def _check_indexes(self, checks: list[DoctorCheck]) -> None:
        expected = [
            self.paths.artifact_index_file,
            self.paths.context_index_file,
            self.paths.decision_index_file,
            self.paths.rde_index_file,
            self.paths.boundary_rule_index_file,
        ]
        missing = [path.name for path in expected if not path.exists()]
        if missing:
            checks.append(
                self._warn(
                    "indexes_present",
                    "one or more derived indexes are missing",
                    detail=", ".join(missing),
                    recommendation="run `chronicle index rebuild`",
                )
            )
        else:
            checks.append(self._ok("indexes_present", "derived indexes are present"))

    def _check_artifact_files(
        self,
        checks: list[DoctorCheck],
        events: list[ChronicleEvent],
    ) -> None:
        missing: set[str] = set()
        for artifact_id, version_id in self._artifact_refs(events):
            if not self.paths.artifact_current(artifact_id).exists():
                missing.add(f"{artifact_id}: current.md")
            if version_id:
                version_path = self.paths.artifact_version_path(artifact_id, version_id)
                if not version_path.exists():
                    missing.add(f"{artifact_id}: versions/{version_id}.md")

        if missing:
            checks.append(
                self._warn(
                    "artifact_files_present",
                    "one or more artifact files are missing",
                    detail="; ".join(sorted(missing)),
                )
            )
        else:
            checks.append(self._ok("artifact_files_present", "artifact files are present"))

    @staticmethod
    def _artifact_refs(events: list[ChronicleEvent]) -> set[tuple[str, str | None]]:
        refs: set[tuple[str, str | None]] = set()
        for event in events:
            artifact = event.payload.get("artifact")
            if isinstance(artifact, dict) and artifact.get("artifact_id"):
                refs.add((artifact["artifact_id"], None))
            version = event.payload.get("version")
            if isinstance(version, dict) and version.get("artifact_id"):
                refs.add((version["artifact_id"], version.get("version_id")))
        return refs

    def _check_injection_plan_refs(
        self,
        checks: list[DoctorCheck],
        events: list[ChronicleEvent],
    ) -> None:
        context_ids = self._context_ids(events)
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
            checks.append(
                self._warn(
                    "recorded_injection_plan_context_refs",
                    "recorded InjectionPlans reference missing Contexts",
                    detail="; ".join(sorted(missing)),
                )
            )
        else:
            checks.append(
                self._ok(
                    "recorded_injection_plan_context_refs",
                    "recorded InjectionPlan Context references are valid",
                )
            )

    @staticmethod
    def _context_ids(events: list[ChronicleEvent]) -> set[str]:
        ids: set[str] = set()
        for event in events:
            context = event.payload.get("context")
            if isinstance(context, dict) and context.get("context_id"):
                ids.add(context["context_id"])
        return ids

    def _check_security_metadata(self, checks: list[DoctorCheck], events: list[ChronicleEvent]) -> None:
        contexts = self._contexts(events)
        self._check_context_classification(checks, contexts)
        self._check_layer4_context_body_storage(checks, contexts)
        self._check_context_use_policy_metadata(checks, contexts)
        self._check_prompt_injection_markers(checks, contexts)
        self._check_integrity_metadata_presence(checks, contexts)

    @staticmethod
    def _contexts(events: list[ChronicleEvent]) -> list[Context]:
        contexts: list[Context] = []
        for event in events:
            context = event.payload.get("context")
            if isinstance(context, dict):
                try:
                    contexts.append(Context.model_validate(context))
                except ValueError:
                    continue
        return contexts

    def _check_context_classification(self, checks: list[DoctorCheck], contexts: list[Context]) -> None:
        unclassified = sorted(ctx.context_id for ctx in contexts if ctx.classification is None)
        if unclassified:
            checks.append(
                self._warn(
                    "security_context_classification_present",
                    "one or more Context records are missing classification metadata",
                    detail=", ".join(unclassified),
                    recommendation="add ClassificationMetadata before export or model-context workflows",
                )
            )
        else:
            checks.append(self._ok("security_context_classification_present", "Context classification metadata is present"))

    def _check_layer4_context_body_storage(self, checks: list[DoctorCheck], contexts: list[Context]) -> None:
        layer4 = sorted(
            ctx.context_id
            for ctx in contexts
            if ctx.classification is not None and ctx.classification.layer == ClassificationLayer.RESTRICTED_SECRET
        )
        if layer4:
            checks.append(
                self._warn(
                    "security_layer4_body_storage",
                    "Layer 4 Context records are present in Chronicle body storage",
                    detail=", ".join(layer4),
                    recommendation="store Layer 4 secrets as references to a dedicated secret manager instead of body text",
                )
            )
        else:
            checks.append(self._ok("security_layer4_body_storage", "no Layer 4 Context body storage detected"))

    def _check_context_use_policy_metadata(self, checks: list[DoctorCheck], contexts: list[Context]) -> None:
        risky = sorted(
            ctx.context_id
            for ctx in contexts
            if ctx.classification is not None
            and ctx.classification.layer >= ClassificationLayer.SENSITIVE_CONTEXT
            and (
                AllowedOperation.INJECT in ctx.classification.allowed_operations
                or ctx.classification.llm_policy.external_allowed
            )
        )
        if risky:
            checks.append(
                self._warn(
                    "security_sensitive_context_use_policy",
                    "sensitive Context records are marked for model-context or external use",
                    detail=", ".join(risky),
                    recommendation="review LlmPolicy and allowed_operations before context-use workflows",
                )
            )
        else:
            checks.append(self._ok("security_sensitive_context_use_policy", "no sensitive external/model-context policy risk detected"))

    def _check_prompt_injection_markers(self, checks: list[DoctorCheck], contexts: list[Context]) -> None:
        findings: list[str] = []
        for ctx in contexts:
            text = f"{ctx.title}\n{ctx.summary}"
            report = scan_text_for_prompt_injection(text, source_id=ctx.context_id)
            if report.findings:
                findings.extend(f"{finding.source_id}:{finding.pattern_id}" for finding in report.findings)
        if findings:
            checks.append(
                self._warn(
                    "security_prompt_injection_markers",
                    "stored Context text contains instruction-like markers",
                    detail="; ".join(sorted(findings)),
                    recommendation="treat stored content as data and use Chronicle data block boundaries for model-facing workflows",
                )
            )
        else:
            checks.append(self._ok("security_prompt_injection_markers", "no prompt-injection markers detected in Context text"))

    def _check_integrity_metadata_presence(self, checks: list[DoctorCheck], contexts: list[Context]) -> None:
        missing = sorted(
            ctx.context_id
            for ctx in contexts
            if ctx.classification is not None and not ctx.classification.integrity.hash
        )
        if missing:
            checks.append(
                self._warn(
                    "security_integrity_metadata_present",
                    "classified Context records are missing integrity metadata hashes",
                    detail=", ".join(missing),
                    recommendation="use integrity metadata helpers before packaging or controlled export workflows",
                )
            )
        else:
            checks.append(self._ok("security_integrity_metadata_present", "classified Context integrity metadata is present or no classified Contexts exist"))

    def _check_audit_lifecycle_surfaces(self, checks: list[DoctorCheck]) -> None:
        self._check_audit_log_surface(checks)
        self._check_lifecycle_surface(checks)

    def _check_audit_log_surface(self, checks: list[DoctorCheck]) -> None:
        store = AuditLogStore(self.paths.audit_file)
        corrupt = store.count_corrupt_lines()
        if corrupt:
            checks.append(
                self._warn(
                    "security_audit_log_parseable",
                    "audit.jsonl contains parse errors",
                    detail=f"{corrupt} corrupt line(s)",
                    recommendation="repair or remove corrupted audit JSONL lines",
                )
            )
        elif self.paths.audit_file.exists():
            checks.append(self._ok("security_audit_log_parseable", "audit.jsonl is parseable"))
        else:
            checks.append(self._warn("security_audit_log_parseable", "audit.jsonl is not present", recommendation="record audit events for export, context-use, and reinterpretation workflows"))

    def _check_lifecycle_surface(self, checks: list[DoctorCheck]) -> None:
        store = LifecycleStore(self.paths.lifecycle_file)
        corrupt = store.count_corrupt_lines()
        if corrupt:
            checks.append(
                self._warn(
                    "security_lifecycle_log_parseable",
                    "lifecycle.jsonl contains parse errors",
                    detail=f"{corrupt} corrupt line(s)",
                    recommendation="repair or remove corrupted lifecycle JSONL lines",
                )
            )
        elif self.paths.lifecycle_file.exists():
            checks.append(self._ok("security_lifecycle_log_parseable", "lifecycle.jsonl is parseable"))
        else:
            checks.append(self._warn("security_lifecycle_log_parseable", "lifecycle.jsonl is not present", recommendation="record lifecycle events for redact, seal, tombstone, and retention workflows"))

    def _check_exports(self, checks: list[DoctorCheck]) -> None:
        if not self.paths.is_initialized():
            checks.append(
                self._warn(
                    "graph_export_available",
                    "graph export cannot be checked before initialization",
                )
            )
            checks.append(
                self._warn(
                    "html_export_available",
                    "HTML export cannot be checked before initialization",
                )
            )
            return

        self._check_graph_export(checks)
        self._check_html_export(checks)

    def _check_graph_export(self, checks: list[DoctorCheck]) -> None:
        try:
            graph = GraphExportService(self.root).export_graph()
        except Exception as exc:
            checks.append(
                self._warn(
                    "graph_export_available",
                    "graph export could not be generated",
                    detail=str(exc),
                )
            )
            return
        detail = f"{len(graph.nodes)} node(s), {len(graph.edges)} edge(s)"
        checks.append(self._ok("graph_export_available", "graph export can be generated", detail))

    def _check_html_export(self, checks: list[DoctorCheck]) -> None:
        try:
            html = HtmlDashboardExporter(self.root).export()
        except Exception as exc:
            checks.append(
                self._warn(
                    "html_export_available",
                    "HTML dashboard export could not be generated",
                    detail=str(exc),
                )
            )
            return
        detail = f"{len(html)} character(s)"
        checks.append(self._ok("html_export_available", "HTML dashboard export can be generated", detail))
