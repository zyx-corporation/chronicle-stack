# Stage 2 Operator Runbook

Status: Ready
Date: 2026-07-13

## Safe default

Stage 2 does not run a model, network backend, capability, proposal apply, or external command automatically. Keep the runtime disabled unless an operator is actively testing it.

```bash
chronicle runtime config disable
chronicle runtime status --json
chronicle doctor --json
```

## Preflight

From an initialized Chronicle root:

```bash
chronicle doctor --json
chronicle runtime status --json
chronicle runtime capability list --json
chronicle ui-smoke --json
```

Pass when doctor has no errors, runtime reports explicit invocation, capability IDs are unique, and UI smoke reports success. Warnings for missing classifications or optional exports require operator interpretation but do not enable execution.

## Explicit runtime execution

Only configure HTTP execution for a reviewed endpoint. Store the environment-variable name, never the credential value, in Chronicle configuration.

```bash
chronicle runtime config set-http \
  --base-url https://runtime.example.test/v1 \
  --model test-model \
  --api-key-env CHRONICLE_RUNTIME_API_KEY \
  --allow-network
chronicle doctor --json
```

Stop if doctor reports a non-TLS external endpoint, review is disabled, or an unexpected capability/configuration appears. Runtime output remains review-required and recording remains explicit.

## Proposal workflow

```bash
chronicle plan artifact-update-preview \
  --artifact ARTIFACT_ID \
  --summary "Reason for change" \
  --content "Replacement content" \
  --record --json
chronicle plan list --json
chronicle review queue --json
```

Preview does not update the artifact. Conversion creates a proposal; approval and apply remain separate. Rebuild the plan if the target version becomes stale. Never bypass the proposal path for capability-generated changes.

## Local UI

Read-only is the default. Mutation requires loopback binding plus explicit mutation, authentication, and authorization settings. Use `chronicle ui-smoke --json` before an operator session and retain the report with release evidence.

## External input

Stage 2 provides a model/service contract and mock adapter only. It does not expose a public webhook or platform integration. Accepted envelopes become review-required `user_input`; command promotion remains `not_executed` until a separate reviewed command path is used.

## Recovery

Follow [Local Backup and Restore](../releases/operations/local-backup-and-restore.md). After restore:

```bash
chronicle index rebuild
chronicle doctor --json
chronicle ui-smoke --json
```

Indexes and registries are derived. `.chronicle/chronicle.jsonl` remains the primary record.
