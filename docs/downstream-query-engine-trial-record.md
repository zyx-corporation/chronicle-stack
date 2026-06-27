# Downstream Query-Engine Trial Record

Use this command to persist the outcome of a real downstream handoff-bundle trial as a Chronicle `assistant_output` event.

## Record a trial

```bash
chronicle package query-engine-trial-record \
  --bundle-dir handoff-bundle \
  --reviewer "operator" \
  --consumer "downstream-demo" \
  --sufficient \
  --note "bundle was enough for dry-run inspection"
```

## Result

- records a review-oriented `assistant_output` event
- stores a structured `query_engine_trial_record` payload
- keeps Chronicle primary records authoritative

## Boundary

- records evaluation metadata only
- does not execute downstream imports
- does not host query execution
- does not make derived bundle files authoritative

Inspect recorded trials later with `docs/downstream-query-engine-trial-inspection.md`.
