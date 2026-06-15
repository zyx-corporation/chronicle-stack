"""Read-only Chronicle health checks."""

import json
from pathlib import Path

import yaml

from chronicle.doctor.artifact_checks import check_artifact_files
from chronicle.doctor.audit_lifecycle_checks import check_audit_lifecycle_surfaces
from chronicle.doctor.export_checks import check_exports
from chronicle.doctor.injection_checks import check_injection_plan_refs
from chronicle.doctor.security_checks import check_security_metadata
from chronicle.doctor.storage_checks import check_indexes, check_known_event_types, check_required_files
from chronicle.models.doctor import DoctorCheck, DoctorReport, DoctorSeverity
from chronicle.models.event import ChronicleEvent
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

        checks.extend(check_required_files(self.paths))
        checks.append(check_known_event_types(events))
        checks.append(check_indexes(self.paths))
        checks.append(check_artifact_files(self.paths, events))
        checks.append(check_injection_plan_refs(events))
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
            checks.append(self._check("jsonl_parseable", DoctorSeverity.OK, "chronicle.jsonl is parseable", detail))
        return events
