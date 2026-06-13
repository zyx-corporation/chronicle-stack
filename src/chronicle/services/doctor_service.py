"""Read-only Chronicle health checks (v0.4)."""

import json
from pathlib import Path

import yaml

from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.models.doctor import DoctorCheck, DoctorReport, DoctorSeverity
from chronicle.models.event import ChronicleEvent, EventType
from chronicle.models.metadata import ChronicleMetadata
from chronicle.services.graph_export_service import GraphExportService
from chronicle.store.paths import ChroniclePaths


class DoctorService:
    """Run read-only diagnostics against a Chronicle project."""

    def __init__(self, root: Path | None = None) -> None:
        self.paths = ChroniclePaths(root)
        self.root = self.paths.root

    def run(self) -> DoctorReport:
        """Run all doctor checks without mutating Chronicle records."""
        checks: list[DoctorCheck] = []
        metadata = self._load_metadata(checks)
        chronicle_id = metadata.chronicle_id if metadata else None
        events = self._read_events(checks)

        self._check_chronicle_dir(checks)
        self._check_jsonl_exists(checks)
        self._check_metadata_exists(checks)
        self._check_known_event_types(checks, events)
        self._check_indexes_present(checks)
        self._check_artifact_files(checks, events)
        self._check_injection_plan_context_refs(checks, events)
        self._check_graph_export(checks)
        self._check_html_export(checks)

        return DoctorReport.from_checks(checks, chronicle_id=chronicle_id)

    def _ok(self, check_id: str, summary: str, detail: str = "") -> DoctorCheck:
        return DoctorCheck(
            check_id=check_id,
            severity=DoctorSeverity.OK,
            summary=summary,
            detail=detail,
        )

    def _warning(
        self,
        check_id: str,
        summary: str,
        detail: str = "",
        recommendation: str = "",
    ) -> DoctorCheck:
        return DoctorCheck(
            check_id=check_id,
            severity=DoctorSeverity.WARNING,
            summary=summary,
            detail=detail,
            recommendation=recommendation,
        )

    def _error(
        self,
        check_id: str,
        summary: str,
        detail: str = "",
        recommendation: str = "",
    ) -> DoctorCheck:
        return DoctorCheck(
            check_id=check_id,
            severity=DoctorSeverity.ERROR,
            summary=summary,
            detail=detail,
            recommendation=recommendation,
        )

    def _check_chronicle_dir(self, checks: list[DoctorCheck]) -> None:
        if self.paths.chronicle_dir.exists():
            checks.append(self._ok("chronicle_dir_exists", ".chronicle directory exists"))
        else:
            checks.append(
                self._error(
                    "chronicle_dir_exists",
                    ".chronicle directory is missing",
                    recommendation='run `chronicle init --title "Your Project"`',
                )
            )

    def _check_jsonl_exists(self, checks: list[DoctorCheck]) -> None:
        if self.paths.events_file.exists():
            checks.append(self._ok("chronicle_jsonl_exists", "chronicle.jsonl exists"))
        else:
            checks.append(
                self._error(
                    "chronicle_jsonl_exists",
                    "chronicle.jsonl is missing",
                    recommendation="run `chronicle init --title ...`",
                )
            )

    def _check_metadata_exists(self, checks: list[DoctorCheck]) -> None:
        if self.paths.metadata_file.exists():
            checks.append(self._ok("metadata_exists", "metadata.yaml exists"))
        else:
            checks.append(
                self._warning(
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
            checks.append(self._ok("metadata_parseable", "metadata.yaml is parseable"))
            return metadata
        except Exception as exc:
            checks.append(
                self._error(
                    "metadata_parseable",
                    "metadata.yaml could not be parsed",
                    detail=str(exc),
                )
            )
            return None

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
                except Exception as exc:
                    errors.append(f"line {line_number}: {exc}")

        if errors:
            checks.append(
                self._error(
                    "jsonl_parseable",
                    "chronicle.jsonl contains parse errors",
                    detail="; ".join(errors),
                    recommendation="repair or remove corrupted JSONL lines",
                )
            )
        else:
            checks.append(
                self._ok(
                    "jsonl_parseable",
                    "chronicle.jsonl is parseable",
                    detail=f"{len(events)} event(s)",
                )
            )
        return events

    def _check_known_event_types(
        self,
        checks: list[DoctorCheck],
        events: list[ChronicleEvent],
    ) -> None:
        known = {event_type.value for event_type in EventType}
        unknown = [
            event.event_type.value
            for event in events
            if event.event_type.value not in known
        ]
        if unknown:
            checks.append(
                self._warning(
                    "known_event_types",
                    "chronicle.jsonl contains unknown event types",
                    detail=", ".join(sorted(set(unknown))),
                    recommendation="verify compatibility with this Chronicle Stack version",
                )
            )
        else:
            checks.append(self._ok("known_event_types", "all event types are known"))

    def _check_indexes_present(self, checks: list[DoctorCheck]) -> None:
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
                self._warning(
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
        missing: list[str] = []
        for artifact_id, version_id in self._artifact_refs(events):
            if artifact_id and not self.paths.artifact_current(artifact_id).exists():
                missing.append(f"{artifact_id}: current.md")
            if artifact_id and version_id:
                version_path = self.paths.artifact_version_path(artifact_id, version_id)
                if not version_path.exists():
                    missing.append(f"{artifact_id}: versions/{version_id}.md")

        if missing:
            checks.append(
                self._warning(
                    "artifact_files_present",
                    "one or more artifact files are missing",
                    detail="; ".join(sorted(set(missing))),
                )
            )
        else:
            checks.append(self._ok("artifact_files_present", "artifact files are present"))

    def _artifact_refs(self, events: list[ChronicleEvent]) -> set[tuple[str, str | None]]:
        refs: set[tuple[str, str | None]] = set()
        for event in events:
            payload = event.payload
            artifact = payload.get("artifact")
            if isinstance(artifact, dict) and artifact.get("artifact_id"):
                refs.add((artifact["artifact_id"], None))
            version = payload.get("version")
            if isinstance(version, dict) and version.get("artifact_id"):
                refs.add((version["artifact_id"], version.get("version_id")))
        return refs

    def _check_injection_plan_context_refs(
        self,
        checks: list[DoctorCheck],
        events: list[ChronicleEvent],
    ) -> None:
        context_ids = self._context_ids(events)
        missing: list[str] = []
        for event in events:
            plan = event.payload.get("injection_plan")
            if event.event_type.value != "injection_plan_recorded" or not isinstance(plan, dict):
                continue
            plan_id = plan.get("plan_id", "unknown")
            for section in ("selected", "warned", "excluded"):
                for ref in plan.get(section, []):
                    if not isinstance(ref, dict):
                        continue
                    context_id = ref.get("context_id")
                    if context_id and context_id not in context_ids:
                        missing.append(f"{plan_id}:{section}:{context_id}")

        if missing:
            checks.append(
                self._warning(
                    "recorded_injection_plan_context_refs",
                    "recorded InjectionPlans reference missing Contexts",
                    detail="; ".join(sorted(set(missing))),
                )
            )
        else:
            checks.append(
                self._ok(
                    "recorded_injection_plan_context_refs",
                    "recorded InjectionPlan Context references are valid",
                )
            )

    def _context_ids(self, events: list[ChronicleEvent]) -> set[str]:
        context_ids: set[str] = set()
        for event in events:
            context = event.payload.get("context")
            if isinstance(context, dict) and context.get("context_id"):
                context_ids.add(context["context_id"])
        return context_ids

    def _check_graph_export(self, checks: list[DoctorCheck]) -> None:
        if not self.paths.is_initialized():
            checks.append(
                self._warning(
                    "graph_export_available",
                    "graph export cannot be checked before initialization",
                )
            )
            return
        try:
            graph = GraphExportService(self.root).export_graph()
            checks.append(
                self._ok(
                    "graph_export_available",
                    "graph export can be generated",
                    detail=f"{len(graph.nodes)} node(s), {len(graph.edges)} edge(s)",
                )
            )
        except Exception as exc:
            checks.append(
                self._warning(
                    "graph_export_available",
                    "graph export could not be generated",
                    detail=str(exc),
                )
            )

    def _check_html_export(self, checks: list[DoctorCheck]) -> None:
        if not self.paths.is_initialized():
            checks.append(
                self._warning(
                    "html_export_available",
                    "HTML export cannot be checked before initialization",
                )
            )
            return
        try:
            html = HtmlDashboardExporter(self.root).export()
            checks.append(
                self._ok(
                    "html_export_available",
                    "HTML dashboard export can be generated",
                    detail=f"{len(html)} character(s)",
                )
            )
        except Exception as exc:
            checks.append(
                self._warning(
                    "html_export_available",
                    "HTML dashboard export could not be generated",
                    detail=str(exc),
                )
            )
