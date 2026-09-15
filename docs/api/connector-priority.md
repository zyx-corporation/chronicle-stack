# API Connector Priority Draft

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 0 / Phase 5

Connector prototypes should lower uncertainty without becoming production surfaces.

| Priority | Connector | Why first | Production gate |
|---|---|---|---|
| 1 | Obsidian capture script or plugin | Tests personal/local knowledge capture with low network risk | Must write structured events with origin metadata |
| 2 | Git hook / PR evidence recorder | Captures decisions and evidence near code changes | Must avoid secrets and avoid implicit commit blocking |
| 3 | Browser extension capture | Exercises boundary-aware context capture from web work | Must include source URL and injection warning handling |
| 4 | AI番頭 / Kotone local client | Tests agent-facing context and assertion writes | Must distinguish human judgment from AI proposal |
| 5 | Business app bridge simulator | Exercises structured external facts | Must reject arbitrary webhook log dumping |

## Prototype Rules

- Prototype branches are not production surfaces.
- No connector may require hosted Chronicle Cloud.
- No connector may write without idempotency and origin metadata.
- Connector output is reviewed through T-RDE before being promoted to stable behavior.

## Current Prototype Surface

The local simulator is documented in `connector-prototypes.md` and exposed through:

```bash
chronicle daemon prototype simulate --connector <kind> ...
```

This simulator is not an external connector. It only generates or submits local API contract
requests so the project can inspect what should and should not be carried into production
connectors.
