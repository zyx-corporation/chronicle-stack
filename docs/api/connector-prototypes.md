# Connector Prototype Simulator

Status: Draft prototype surface
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 5

Chronicle Stack includes a local connector prototype simulator so integration assumptions can be
tested without contacting external applications or promoting prototypes into production
connectors.

## CLI

```bash
chronicle daemon prototype simulate \
  --connector obsidian_capture \
  --title "Meeting note" \
  --body "Decision evidence captured from a local note." \
  --idempotency-key idem-example-obsidian \
  --source-ref "vault/meeting.md" \
  --json
```

By default, simulation is dry-run and does not change `.chronicle/chronicle.jsonl`.

To submit through local Core services:

```bash
chronicle daemon prototype simulate \
  --connector browser_capture \
  --title "Source page note" \
  --body "Captured as review evidence." \
  --idempotency-key idem-example-browser \
  --source-url "https://example.test/source" \
  --commit \
  --json
```

## Supported Prototype Kinds

| Connector | Request model | Purpose |
|---|---|---|
| `obsidian_capture` | `EventWriteRequest` | Local note capture shape |
| `git_evidence` | `EventWriteRequest` | Commit, PR, or repository evidence shape |
| `browser_capture` | `EventWriteRequest` | Source URL and disclosure-warning shape |
| `agent_assertion` | `AssertionWriteRequest` | Agent-originated claim/caveat shape |
| `business_fact` | `AssertionWriteRequest` | Structured business-system fact shape |

## Boundary

- No external application is contacted.
- No credentials are used.
- No background sync exists.
- `production_surface=false` is part of the simulator output.
- Committed simulations still use idempotency and origin metadata.
- Business facts must remain structured assertions, not arbitrary webhook log dumps.

## Carry-Forward Review

Each simulation returns:

- `carry_forward`: behavior that a future production connector should preserve.
- `do_not_carry_forward`: prototype-only behavior or prohibited production assumptions.
- `warnings`: explicit notes that this is not a production connector.
