# Changelog

## v1.3.0 - 2026-06-17

### Added
- Automated read-only UI smoke command:
  - `chronicle ui-smoke`
  - `chronicle ui-smoke --json`
  - `chronicle ui-smoke --root <root>`
- `chronicle.ui_smoke` service and report models.
- Collection payload smoke checks for the local UI data surface.
- Detail payload smoke checks for available records.
- Missing-detail smoke behavior.
- Text and JSON smoke report output.
- Tests for service success, CLI text output, CLI JSON output, missing-root failure, and help text.

### Changed
- Project version finalized as `1.3.0`.
- README now documents `chronicle ui-smoke` and the v1.3 release target.
- v1.2 manual UI detail smoke is now supported by repeatable local automation.

### Notes
- v1.3.0 is an automated UI smoke / release-verification release over v1.2.0.
- `chronicle ui-smoke` does not start a server, bind sockets, or open a browser.
- `chronicle ui-smoke` does not write records, call external model APIs, embed GraphRAG, use vector DB, or use graph DB.
- Smoke pass is diagnostic and is not security certification, access-control enforcement, or correctness proof.
- Commercial SaaS license and contributor policy drafts remain draft completed / counsel review pending.
- Tag creation, GitHub Release publication, and installer smoke from tag remain explicit release-operator steps.

## v1.2.0 - 2026-06-16

### Added
- Read-only detail endpoints for `chronicle ui`:
  - `/api/events/<id>`
  - `/api/contexts/<id>`
  - `/api/artifacts/<id>`
  - `/api/decisions/<id>`
  - `/api/rde/<id>`
  - `/api/boundary/<id>`
  - `/api/audit/<id>`
  - `/api/lifecycle/<id>`
- Artifact detail payloads now include version metadata.
- Lightweight browser-shell drill-down affordance for table rows.
- Tests for service-level and HTTP-level detail endpoint success and not-found behavior.
- v1.2 UI detail endpoint release track.

### Changed
- Project version finalized as `1.2.0`.
- README now documents v1.2 detail endpoint status and release target.
- `chronicle ui` moves from collection-oriented review to record-inspection review.

### Notes
- v1.2.0 is a UI drill-down / inspectability release over the v1.1.0 GUI/readability release.
- Detail endpoints are read-only derived views over local Chronicle files.
- Detail views do not write records, enforce access control, or prove correctness.
- `chronicle ui` remains explicitly launched, foreground-only, and loopback-bound by default.
- v1.2.0 does not add daemon/autostart behavior, hosted service, model API, GraphRAG runtime, vector DB, or graph DB.
- Commercial SaaS license and contributor policy drafts remain draft completed / counsel review pending.
- Tag creation, GitHub Release publication, and installer smoke from tag remain explicit release-operator steps.

## v1.1.0 - 2026-06-16

### Added
- Static read-first Review Console for GUI-oriented inspection.
- Explicit foreground local web UI command:
  - `chronicle ui`
- Python stdlib local UI server with no new web framework dependency.
- Default loopback UI binding:
  - host: `127.0.0.1`
  - port: `8765`
- Lightweight browser shell for local read-only review.
- Read-only local UI endpoints:
  - `/api/overview`
  - `/api/events`
  - `/api/contexts`
  - `/api/artifacts`
  - `/api/decisions`
  - `/api/rde`
  - `/api/boundary`
  - `/api/audit`
  - `/api/lifecycle`
  - `/api/package-review`
  - `/api/graph-summary`
- `/review-console` route for the static Review Console view.
- v1.1 Review Console plan.
- v1.1 Local Web UI design document.
- UI server tests covering startup metadata, shell rendering, read-only endpoints, and HTTP smoke.

### Changed
- Project version finalized as `1.1.0`.
- README now documents `chronicle ui` usage and read-only endpoint surface.
- HTML dashboard language now presents the surface as a Review Console.
- GUI/readability is now an explicit v1.1 release theme.

### Notes
- v1.1.0 is a GUI/readability release over the v1.0.0 local-first foundation.
- `chronicle ui` is explicitly launched and foreground-only.
- `chronicle ui` does not install or start a daemon, autostart service, hosted UI, or cloud sync.
- `chronicle ui` does not call external model APIs.
- `chronicle ui` does not embed GraphRAG, vector DB, or graph DB runtime.
- UI visibility is not access control, enforcement, or correctness proof.
- Static HTML Review Console remains available as a portable read-only derived export.
- Commercial SaaS license and contributor policy drafts remain draft completed / counsel review pending.
- Tag creation, GitHub Release publication, and installer smoke from tag remain explicit release-operator steps.

## v1.0.0 - 2026-06-15

### Added
- Stable context sovereignty foundation release track.
- v1.0 release criteria and compatibility policy documentation.
- v1.0 README release-status and docs polish.
- v1.0 installer smoke profile.
- v1.0 CLI compatibility audit.
- v1.0 Sayane / CSG-RAG integration boundary note.
- v1.0 release execution plan and release notes.

### Changed
- Project version finalized as `1.0.0`.
- README release status now reflects the v0.9.0 published baseline and v1.0.0 stable target.
- Release documentation now treats compatibility, installer smoke, and boundary warnings as stable-release requirements.

### Notes
- v1.0.0 is a local-first stable foundation release.
- v1.0.0 does not introduce a server, daemon, web runtime, model API, GraphRAG engine, vector DB, or graph DB.
- Classification metadata remains advisory metadata, not access control.
- Audit events remain traceability metadata, not enforcement.
- Lifecycle markers remain advisory metadata and do not mutate primary records by themselves.
- Package review remains diagnostic and is not correctness proof.
- Commercial SaaS license and contributor policy drafts remain draft completed / counsel review pending.
- Tag creation, GitHub Release publication, and installer smoke from tag remain explicit release-operator steps.

## v0.9.0 - 2026-06-15

### Added
- Release Candidate Hardening and Version Finalization track.
- v0.9 release-readiness document.
- v0.9 smoke-test profile.
- v0.9 release deployment procedure.

### Changed
- Project version finalized as `0.9.0`.
- README document list now includes v0.7, v0.8, and v0.9 technical docs.
- v0.9 release checklist connects v0.7 operational workflows and v0.8 package review workflow into one release candidate path.

### Notes
- v0.9 is a local-first technical release candidate.
- v0.9 does not introduce a server, daemon, model runtime, GraphRAG engine, vector DB, or graph DB.
- v0.9 does not finalize #26 commercial license template or #27 CLA / DCO final policy.
- Tag and GitHub Release creation remain explicit release execution steps.

## v0.8.0 - 2026-06-15

### Added
- Verified Package / Export Review Workflow.
- Package review models:
  - `PackageReviewStatus`
  - `PackageReviewFinding`
  - `PackageReviewReport`
- Package review service for converting controlled-package warnings into an explicit review report.
- `chronicle package review` CLI command.
- JSON package review output.
- Review support for both generated context packages and persisted packages.
- v0.8 package review workflow documentation.
- v0.8 package review smoke profile.
- v0.8 package review tests covering pass, warning, blocked, and persisted-package review paths.

### Changed
- Controlled package warnings can now be inspected before persistence or handoff through a local review checkpoint.
- Package review reports classify findings as `pass`, `warning`, or `blocked`.
- Sensitive external package review conditions can return a blocked status without calling any external runtime.

### Notes
- Package review is diagnostic and local-first.
- Package review does not call models, GraphRAG engines, vector databases, graph databases, servers, or daemons.
- `pass` is not formal correctness proof.
- `warning` is not automatic approval.
- `blocked` requires review before handoff.
- #26 commercial license template and #27 CLA / DCO final policy remain intentionally out of scope until explicitly directed.

## v0.7.0 - 2026-06-15

### Added
- Operational Hardening and Verified Context Workflows.
- Context classification workflow:
  - `chronicle context classification missing`
  - `chronicle context classification set --context ...`
  - `chronicle context classification show --context ...`
- Audit event workflow:
  - `chronicle audit record`
  - `chronicle audit list`
  - `chronicle audit show --id ...`
- Lifecycle marker workflow:
  - `chronicle lifecycle record`
  - `chronicle lifecycle list`
  - `chronicle lifecycle show --id ...`
- `chronicle-audit` and `chronicle-lifecycle` entry points.
- Doctor remediation guidance for classification / audit / lifecycle warnings.
- v0.7 operational hardening plan.
- v0.7 smoke test profile.
- v0.7 operational workflow tests.

### Changed
- Doctor security checks now evaluate the latest Context snapshot per `context_id`.
- Missing classification warnings point to the classification workflow.
- Missing audit/lifecycle log warnings point to local CLI workflows.
- Context classification records a new Context snapshot with advisory classification metadata and integrity metadata.

### Notes
- Classification metadata remains advisory and is not access control.
- Audit events improve traceability and are not enforcement.
- Lifecycle markers are advisory metadata and do not mutate primary records by themselves.
- v0.7 does not introduce a server, daemon, model runtime, GraphRAG engine, vector DB, or graph DB.

## v0.6.0 - 2026-06-15

### Added
- Observation E2E surface-gate boundary documentation.
- ADR-0011 through ADR-0017 for v0.6 architecture decisions:
  - ADR-0011: Observation E2E as Separate Surface Gate
  - ADR-0012: Audit Insertion Points for Derived Operations
  - ADR-0013: Lifecycle-aware Export Filtering
  - ADR-0014: Package Persistence Model
  - ADR-0015: Python Code Splitting and Complexity Management Criteria
  - ADR-0016: HTTP Bridge Auth Dependency Boundary
  - ADR-0017: Auxiliary CLI Integration Boundary
- Package persistence under `.chronicle/packages`.
- Persisted package inspection commands:
  - `chronicle package list`
  - `chronicle package show --package ...`
  - `chronicle package records --package ...`
- Lifecycle-aware export filtering across major derived export surfaces:
  - Markdown
  - YAML
  - HTML
  - graph-json
- Shared lifecycle export helper logic for derived-output filtering.
- Primary CLI aliases for previously auxiliary surfaces:
  - `chronicle package ...`
  - `chronicle context ...`
  - `chronicle graph ...`
  - `chronicle export profile ...`
- Primary alias tests for package, context, graph, and export profile workflows.
- Future HTTP bridge auth dependency guidance for Chronicle / Sayane integration planning.
- v0.6 release-readiness document.

### Changed
- User-facing documentation now prefers primary CLI aliases while preserving auxiliary commands as compatibility surfaces.
- `chronicle export` now supports the `profile` subcommand while preserving existing `chronicle export --format ...` behavior.
- Lifecycle markers now influence derived exports without mutating primary records.
- Package persistence makes controlled integration packages inspectable after generation.
- README and CLI reference document primary CLI aliases and auxiliary compatibility.

### Notes
- `chronicle.jsonl` remains the primary record.
- Observation E2E remains a separate non-certifying workflow observation surface and is not promoted to the Core CI phase gate.
- Core CI pass is not semantic correctness certification or security certification.
- Lifecycle-aware export is derived-output filtering, not physical deletion, access-control enforcement, or deletion-law compliance by itself.
- Hard-delete markers are lifecycle markers and do not physically erase primary records in v0.6.
- Package persistence is a transport artifact, not a permission grant, publication event, external submission, or access-control decision.
- Primary CLI aliases do not deprecate `chronicle-context`, `chronicle-export`, `chronicle-package`, or `chronicle-graph`.
- Future HTTP bridge auth guidance does not add an HTTP server, authentication, or authorization implementation to Chronicle Stack.
- Observation E2E runner implementation, release tag creation, external model API calls, GraphRAG engine, vector DB, graph DB, Sayane runtime execution, HTTP bridge implementation, real encrypted backend, key management, and lifecycle enforcement remain out of scope.

## v0.5.0 - 2026-06-14

### Added
- Security-aware foundation layer for Chronicle context assets.
- ADR series for v0.5 security architecture:
  - ADR-0001: Treat Chronicle Records as Context Assets
  - ADR-0002: CI as T-RDE Execution and Phase Gate
  - ADR-0003: Encrypted Store Abstraction Boundary
  - ADR-0004: Prompt Injection Sanitizer Boundary
  - ADR-0005: Audit Log for Derived Operations
  - ADR-0006: Lifecycle Model for Redact / Seal / Tombstone
  - ADR-0007: Integrity Metadata Preparation
  - ADR-0008: Doctor Security Checks
  - ADR-0009: Security-aware Export Profiles
  - ADR-0010: Controlled CSG-RAG / Sayane Integration Packages
- `ClassificationMetadata` for Chronicle context assets.
- Classification layers 0-4 and sensitivity labels.
- Operation permission vocabulary for view / create / edit / append / summarize / reinterpret / redact / seal / export / inject / publish.
- Model-context dry-run models and `ContextUseService`.
