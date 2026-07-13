"""Runtime and capability registry doctor checks."""

from pathlib import Path
from urllib.parse import urlparse

from chronicle.doctor.check_factory import err, ok, warn
from chronicle.models.doctor import DoctorCheck
from chronicle.models.runtime import RuntimeProviderKind
from chronicle.services.capability_registry_service import CapabilityRegistryService
from chronicle.services.runtime_config_service import RuntimeConfigService


def check_capability_registry() -> list[DoctorCheck]:
    service = CapabilityRegistryService()
    manifests = service.list_capabilities()
    duplicates = service.duplicate_ids()
    checks: list[DoctorCheck] = []

    if duplicates:
        checks.append(
            warn(
                "runtime_capability_registry_unique_ids",
                "static capability registry contains duplicate capability IDs",
                detail=", ".join(duplicates),
                recommendation="remove duplicate capability IDs from the static registry.",
            )
        )
    else:
        checks.append(ok("runtime_capability_registry_unique_ids", "static capability registry IDs are unique"))

    runtime_manifests = [manifest for manifest in manifests if manifest.operation_family == "runtime"]
    if runtime_manifests:
        checks.append(
            ok(
                "runtime_capability_registry_runtime_present",
                "runtime capability registry entries are available",
                detail=", ".join(manifest.capability_id for manifest in runtime_manifests),
            )
        )
    else:
        checks.append(
            warn(
                "runtime_capability_registry_runtime_present",
                "runtime capability registry has no runtime entries",
                recommendation="register built-in runtime capabilities before expanding Stage 2 execution flows.",
            )
        )
    return checks


def check_runtime_configuration(root: Path) -> list[DoctorCheck]:
    """Report dangerous stored runtime settings without invoking the runtime."""

    state = RuntimeConfigService(root).show()
    config = state.config
    checks: list[DoctorCheck] = []
    if config.provider_kind != RuntimeProviderKind.HTTP:
        checks.append(ok("runtime_external_network_disabled", "external HTTP runtime is not configured"))
        return checks

    if not config.allow_network:
        checks.append(ok("runtime_external_network_disabled", "configured HTTP runtime network access is disabled"))
    else:
        checks.append(
            warn(
                "runtime_external_network_disabled",
                "configured HTTP runtime permits explicit external network access",
                detail=config.base_url or "base URL not set",
                recommendation="disable runtime network access when external execution is not required.",
            )
        )

    parsed = urlparse(config.base_url or "")
    if config.allow_network and parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        checks.append(
            err(
                "runtime_http_transport_secure",
                "external HTTP runtime uses a non-TLS endpoint",
                detail=config.base_url or "base URL not set",
                recommendation="use HTTPS or a loopback-only endpoint.",
            )
        )
    else:
        checks.append(ok("runtime_http_transport_secure", "HTTP runtime transport boundary is local or TLS-protected"))

    if config.review_required:
        checks.append(ok("runtime_generated_output_review", "runtime-generated output requires review"))
    else:
        checks.append(
            err(
                "runtime_generated_output_review",
                "runtime-generated output review is disabled",
                recommendation="set review_required to true before runtime execution.",
            )
        )
    return checks
