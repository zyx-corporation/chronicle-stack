"""Search service for events, artifacts, and decisions."""

from pathlib import Path

from chronicle.services.chronicle_service import ChronicleService


class SearchResult:
    def __init__(self, kind: str, identifier: str, summary: str, detail: str = "") -> None:
        self.kind = kind
        self.identifier = identifier
        self.summary = summary
        self.detail = detail


class SearchService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def search(self, query: str) -> list[SearchResult]:
        self.chronicle.require_initialized()
        query_lower = query.lower()
        results: list[SearchResult] = []

        for event in self.chronicle.jsonl.read_all():
            haystack = f"{event.summary} {event.event_type} {event.payload}".lower()
            if query_lower in haystack:
                results.append(
                    SearchResult(
                        kind="event",
                        identifier=event.event_id,
                        summary=event.summary,
                        detail=event.event_type.value,
                    )
                )

        artifacts, _ = self.chronicle.index.load_artifacts()
        for artifact in artifacts.values():
            haystack = f"{artifact.title} {artifact.artifact_type} {' '.join(artifact.tags)} {artifact.source}".lower()
            if query_lower in haystack:
                results.append(
                    SearchResult(
                        kind="artifact",
                        identifier=artifact.artifact_id,
                        summary=artifact.title,
                        detail=f"{artifact.artifact_type.value},visibility={artifact.visibility_hint.value}",
                    )
                )

        decisions = self.chronicle.index.load_decisions()
        for decision in decisions.values():
            haystack = f"{decision.reason} {decision.decision_type} {decision.notes}".lower()
            if query_lower in haystack:
                results.append(
                    SearchResult(
                        kind="decision",
                        identifier=decision.decision_id,
                        summary=decision.reason or decision.decision_type.value,
                        detail=decision.decision_type.value,
                    )
                )

        contexts = self.chronicle.index.load_contexts()
        for context in contexts.values():
            haystack = f"{context.title} {context.summary} {' '.join(context.tags)} {context.source}".lower()
            if query_lower in haystack:
                results.append(
                    SearchResult(
                        kind="context",
                        identifier=context.context_id,
                        summary=context.title,
                        detail=f"{context.scope.value},visibility={context.visibility_hint.value}: {context.summary}",
                    )
                )

        rde_records = self.chronicle.index.load_rde_records()
        for rde in rde_records.values():
            haystack = (
                f"{rde.summary} {' '.join(rde.preserved)} "
                f"{' '.join(rde.transformed)} {' '.join(rde.supplemented)} "
                f"{' '.join(rde.unresolved)} {' '.join(rde.deviation_risks)} "
                f"{' '.join(rde.next_update_policy)}"
            ).lower()
            if query_lower in haystack:
                results.append(
                    SearchResult(
                        kind="rde",
                        identifier=rde.rde_record_id,
                        summary=rde.summary or f"RDE: {rde.from_version_id} -> {rde.to_version_id}",
                        detail=f"RDE diff record for {rde.artifact_id}",
                    )
                )

        return results
