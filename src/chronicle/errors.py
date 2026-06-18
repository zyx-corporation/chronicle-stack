"""Chronicle error types."""

from dataclasses import dataclass


@dataclass
class ChronicleError(Exception):
    code: str
    message: str
    hint: str = ""

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\nHint: {self.hint}"
        return self.message

    def to_dict(self) -> dict:
        result: dict = {"code": self.code, "message": self.message}
        if self.hint:
            result["hint"] = self.hint
        return {"error": result}


class ChronicleNotInitializedError(ChronicleError):
    def __init__(self) -> None:
        super().__init__(
            code="CHRONICLE_NOT_INITIALIZED",
            message="Chronicle is not initialized in this directory.",
            hint=(
                "Run `chronicle init --title \"Your Project\"`"
                " to create one."
            ),
        )


class ChronicleJsonlNotFoundError(ChronicleError):
    def __init__(self) -> None:
        super().__init__(
            code="CHRONICLE_JSONL_NOT_FOUND",
            message="chronicle.jsonl not found.",
            hint="Run `chronicle init` to create a new Chronicle.",
        )


class ArtifactNotFoundError(ChronicleError):
    def __init__(self, artifact_id: str) -> None:
        super().__init__(
            code="ARTIFACT_NOT_FOUND",
            message=f"Artifact not found: {artifact_id}",
            hint=(
                "Run `chronicle artifact list`"
                " to see available artifacts."
            ),
        )


class ArtifactContentMissingError(ChronicleError):
    def __init__(self) -> None:
        super().__init__(
            code="ARTIFACT_CONTENT_MISSING",
            message="Artifact update requires either --file or --content.",
            hint="Pass --file <path> to a source file, or --content <string> to update.",
        )


class VersionNotFoundError(ChronicleError):
    def __init__(self, version_id: str) -> None:
        super().__init__(
            code="VERSION_NOT_FOUND",
            message=f"Version not found: {version_id}",
            hint=(
                "Run `chronicle artifact history --artifact <id>`"
                " to see versions."
            ),
        )


class DecisionTargetNotFoundError(ChronicleError):
    def __init__(self, target: str) -> None:
        super().__init__(
            code="DECISION_TARGET_NOT_FOUND",
            message=f"Decision target not found: {target}",
            hint=(
                "Ensure the artifact or event exists"
                " before recording a decision."
            ),
        )


class RdeVersionNotFoundError(ChronicleError):
    def __init__(self, version_id: str) -> None:
        super().__init__(
            code="RDE_VERSION_NOT_FOUND",
            message=f"RDE version not found: {version_id}",
            hint=(
                "Verify from_version and to_version"
                " exist in artifact history."
            ),
        )


class EmptyArtifactContentError(ChronicleError):
    def __init__(self, artifact_id: str) -> None:
        super().__init__(
            code="EMPTY_ARTIFACT_CONTENT",
            message=(
                f"Cannot update artifact {artifact_id}"
                " with empty content."
            ),
            hint=(
                "Provide --file or content"
                " to specify the new artifact body."
            ),
        )


class JsonlParseError(ChronicleError):
    def __init__(self, line_number: int, detail: str) -> None:
        super().__init__(
            code="JSONL_PARSE_ERROR",
            message=(
                f"Failed to parse JSONL line {line_number}: {detail}"
            ),
            hint=(
                "Repair or remove the corrupted line;"
                " other events remain readable."
            ),
        )


class SourceFileNotFoundError(ChronicleError):
    def __init__(self, path: str) -> None:
        super().__init__(
            code="SOURCE_FILE_NOT_FOUND",
            message=f"Source file not found: {path}",
            hint="Check the file path and try again.",
        )


class AiIndexRecordNotFoundError(ChronicleError):
    def __init__(self, record_id: str) -> None:
        super().__init__(
            code="AI_INDEX_RECORD_NOT_FOUND",
            message=f"Chronicle record not found for ai-index operation: {record_id}",
            hint="Use a Chronicle event, context, artifact, decision, RDE, boundary, audit, lifecycle, or chronicle ID.",
        )


class InvalidMetadataOptionError(ChronicleError):
    def __init__(self, option_name: str, value: str) -> None:
        super().__init__(
            code="INVALID_METADATA_OPTION",
            message=f"Invalid {option_name} value: {value}",
            hint=f"Pass repeated --{option_name} options as key=value.",
        )


class UIHostNotLoopbackError(ChronicleError):
    def __init__(self, host: str) -> None:
        super().__init__(
            code="UI_HOST_NOT_LOOPBACK",
            message=f"UI host must remain loopback-only until auth/authz is implemented: {host}",
            hint="Use `127.0.0.1`, `localhost`, or `::1` for the local read-only UI.",
        )
