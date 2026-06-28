# Chronicle Stack v1.66 Smoke Test

## Local graph retrieval adapter

- confirm `chronicle graph retrieve --query "graph context" --json` returns `contract_version`
- confirm `chronicle runtime retrieve-plan --query "graph context" --json` returns `graph_adapter`
- confirm no external runtime or GraphRAG engine is invoked
