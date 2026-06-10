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
