"""Package review service for v0.8 verified export workflows."""

from chronicle.models.integration_package import IntegrationPackage, IntegrationTargetEnvironment
from chronicle.models.package_review import PackageReviewFinding, PackageReviewReport, PackageReviewStatus
from chronicle.services.integration_package_service import IntegrationPackageService


BLOCKING_WARNING_CODES = {
    "external_sensitive_context_not_allowed",
    "prompt_marker:ignore_previous_instructions",
    "prompt_marker:export_secrets",
    "prompt_marker:system_override",
}

WARNING_RECOMMENDATIONS = {
    "unclassified_context": "classify the Context before package or export review",
    "layer4_reference_only": "verify the reference-only boundary before sharing the package",
    "external_sensitive_context_not_allowed": "review LlmPolicy and target environment before external use",
    "lifecycle_tombstoned_records_excluded": "review lifecycle markers and selected record IDs",
}


class PackageReviewService:
    """Review controlled packages before persistence or external handoff."""

    def __init__(self) -> None:
        self.packages = IntegrationPackageService()

    def review_context_package(
        self,
        *,
        purpose: str,
        target_environment: IntegrationTargetEnvironment = IntegrationTargetEnvironment.LOCAL,
        context_ids: list[str] | None = None,
    ) -> PackageReviewReport:
        package = self.packages.build_context_package(
            purpose=purpose,
            target_environment=target_environment,
            context_ids=context_ids,
        )
        return self.review_package(package)

    def review_persisted_package(self, package_id: str) -> PackageReviewReport:
        package = self.packages.load_package(package_id)
        return self.review_package(package)

    def review_package(self, package: IntegrationPackage) -> PackageReviewReport:
        findings: list[PackageReviewFinding] = []
        record_warning_codes = {
            warning
            for record in package.records
            for warning in record.warnings
        }

        for warning in package.manifest.warnings:
            if warning in record_warning_codes:
                continue
            findings.append(_finding_for_warning(warning))

        for record in package.records:
            for warning in record.warnings:
                findings.append(_finding_for_warning(warning, record_id=record.record_id))

        status = _status_for_findings(findings)
        return PackageReviewReport(
            status=status,
            purpose=package.manifest.purpose,
            target_environment=package.manifest.target_environment.value,
            record_count=len(package.records),
            output_classification=package.manifest.output_classification,
            package_warnings=package.manifest.warnings,
            findings=findings,
        )


def _finding_for_warning(warning: str, record_id: str | None = None) -> PackageReviewFinding:
    severity = PackageReviewStatus.BLOCKED if warning in BLOCKING_WARNING_CODES else PackageReviewStatus.WARNING
    return PackageReviewFinding(
        severity=severity,
        code=warning,
        summary=_summary_for_warning(warning),
        record_id=record_id,
        recommendation=WARNING_RECOMMENDATIONS.get(warning, "review the package boundary before handoff"),
    )


def _summary_for_warning(warning: str) -> str:
    if warning.startswith("prompt_marker:"):
        return "Context text contains an instruction-like marker"
    return warning.replace("_", " ")


def _status_for_findings(findings: list[PackageReviewFinding]) -> PackageReviewStatus:
    if any(finding.severity == PackageReviewStatus.BLOCKED for finding in findings):
        return PackageReviewStatus.BLOCKED
    if findings:
        return PackageReviewStatus.WARNING
    return PackageReviewStatus.PASS
