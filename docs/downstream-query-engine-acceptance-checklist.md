# Downstream Query-Engine Acceptance Checklist

Use this checklist to decide whether the local handoff bundle is sufficient or whether a separate downstream adapter implementation repo is actually needed.

## Accept if

- the bundle files parse and stay mutually consistent
- `import_validation` is enough for structural preflight
- the downstream consumer can proceed without adding executable Chronicle-side import logic
- Chronicle primary records remain authoritative in every review and demo

## Do not accept yet if

- the consumer needs Chronicle Stack to execute imports
- the consumer needs Chronicle Stack to host query execution
- the consumer needs derived bundle files to become authoritative
- the consumer needs runtime behavior that belongs in an external GraphRAG or query-engine stack

## Escalate to a separate implementation repo only if

- the descriptive bundle is repeatedly insufficient in real downstream trials
- the missing behavior clearly belongs outside Chronicle Stack core
- the proposed repo can keep Chronicle Stack as a read-only record layer

Use `docs/downstream-query-engine-trial-report-template.md` to record each real trial before escalating.
