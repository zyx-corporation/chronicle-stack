"""Build a descriptive downstream query-engine adapter skeleton."""

from chronicle.models.integration_adapter import AdapterSkeletonStep, QueryEngineAdapterSkeleton
from chronicle.models.runtime import RuntimeQueryEngineHandoff


class QueryEngineAdapterSkeletonBuilder:
    """Produce a read-only adapter skeleton from a query-engine handoff contract."""

    def build(self, handoff: RuntimeQueryEngineHandoff) -> QueryEngineAdapterSkeleton:
        import_validation = handoff.import_validation
        return QueryEngineAdapterSkeleton(
            handoff_contract_version=handoff.contract_version,
            import_validation_contract_version=(
                import_validation.contract_version if import_validation is not None else "1.0"
            ),
            primary_record_path=handoff.primary_record_path,
            graph_export_format=handoff.graph_export_format,
            graph_export_contract_version=handoff.graph_export_contract_version,
            required_inputs=[
                "query_engine_handoff.json",
                ".chronicle/chronicle.jsonl",
                "graph.json",
            ],
            recommended_sequence=[
                AdapterSkeletonStep(
                    name="inspect_handoff",
                    command_hint='chronicle runtime retrieve-plan --query "release note context" --json',
                    notes=["confirm referenced records and prohibited assumptions"],
                ),
                AdapterSkeletonStep(
                    name="inspect_graph_contract",
                    command_hint="chronicle graph summary --json",
                    notes=["confirm graph export contract version and incremental mode"],
                ),
                AdapterSkeletonStep(
                    name="materialize_graph_export",
                    command_hint="chronicle export --format graph-json -o graph.json",
                    notes=["materialize the derived graph export for downstream reading"],
                ),
                AdapterSkeletonStep(
                    name="verify_import_validation",
                    command_hint='chronicle runtime retrieve-plan --query "release note context" --json',
                    notes=["check import_validation before any downstream parsing"],
                ),
            ],
            prohibited_capabilities=[
                "do not execute a hosted query engine from Chronicle core",
                "do not mutate Chronicle primary records during adapter import",
                "do not treat derived consumer state as authoritative",
            ],
            non_goals=[
                "query execution",
                "ranking quality certification",
                "semantic correctness certification",
                "runtime orchestration",
            ],
            notes=[
                "this skeleton is descriptive only",
                "downstream implementers must keep import separate from Chronicle core",
                "import validation remains a structural preflight rather than an execution step",
            ],
        )
