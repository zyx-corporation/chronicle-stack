# Agent Runtime Integration Contract

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 7

This contract describes how Kazane-compatible or other agent runtimes may use Chronicle API
without owning the Chronicle.

Executable models live in `src/chronicle/api/agent_runtime.py`.

## CLI

```bash
chronicle daemon agent contract --json
```

## Capability Scopes

| Scope | Meaning |
|---|---|
| `read_context` | Read boundary-aware context |
| `read_boundaries` | Read advisory boundary rules |
| `write_events` | Write structured Chronicle events |
| `write_assertions` | Write reviewable claims, caveats, unknowns, and evidence |
| `write_diffs` | Write RDE diffs through Chronicle services |
| `request_review` | Request human review or disposition |

## Origin Kinds

| Origin kind | Meaning |
|---|---|
| `human_judgment` | Human-authored judgment; requires `human_supervisor_id` |
| `ai_proposal` | AI-generated proposed content |
| `agent_action` | Agent-executed action |
| `business_system_fact` | Structured fact from a business system |
| `derived_interpretation` | Interpretation derived from existing records |

## Boundary Rules

- Agent runtime is an execution layer, not Chronicle authority.
- Agent writes go through Chronicle API contracts.
- AI proposal and derived interpretation remain reviewable and are not primary facts by default.
- Unbounded memory dumps are disallowed.
- Replay/audit metadata is required for agent-originated writes.

## Prototype Client Plan

The first prototype client should:

1. Read the default contract.
2. Generate API origin metadata from `AgentRuntimeMetadata`.
3. Use dry-run API writes by default.
4. Commit only with idempotency keys, origin metadata, and review status.
5. Record what should and should not be promoted through T-RDE before production use.
