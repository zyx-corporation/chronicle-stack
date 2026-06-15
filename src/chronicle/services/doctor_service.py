"""Read-only Chronicle health checks."""

import json
from pathlib import Path

import yaml

from chronicle.doctor.audit_lifecycle_checks import check_audit_lifecycle_surfaces
from chronicle.doctor.export_checks import check_exports
from chronicle.doctor.security_checks import check_security_metadata
from chronicle.models.doctor import DoctorCheck, DoctorReport, DoctorSeverity
from chronicle.models.event import ChronicleEvent, EventType
from chronicle.models.metadata import ChronicleMetadata
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
        checks.extend(check_security_metadata(events))
        checks.extend(check_audit_lifecycle_surfaces(self.paths))
        checks.extend(check_exports(self.paths, self.root))

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
