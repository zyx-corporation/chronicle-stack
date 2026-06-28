# Changelog

## Unreleased

- No unreleased changes recorded.

## v1.14.0 - 2026-06-24

### Added
- `v1.14.0` release-track documents:
  - `docs/releases/status/release-status-v1.14.0.md`
  - `docs/releases/readiness/release-readiness-v1.14.md`
  - `docs/releases/notes/release-notes-v1.14.0.md`
  - `docs/releases/smoke/smoke-test-v1.14.md`
  - `docs/releases/remaining/v1.14-release-remaining-issues.md`
- Dedicated `v1.14.0` release-lane framing for local reviewer-boundary derived fallback copy.
- Explicit drilldown variants for row-detail versus overview-dominant reviewer-boundary summaries.
- Deterministic fallback message and fact-line copy derived from structured reviewer-boundary contracts.
- `ui-smoke` coverage for explicit reviewer-boundary drilldown variants and derived fallback-copy fields.

### Changed
- Project version finalized as `1.14.0`.
- `v1.14.0` release-lane documents now treat `v1.13.0` as the historical published baseline rather than the active repository-side lane.
- Reviewer-boundary drilldown rendering now consumes variant-aware template params before fallback literals.

### Notes
- `v1.14.0` is a local reviewer-boundary derived-fallback-copy release over the published `v1.13.0` baseline.
- Repository-side release preparation is complete once editable reinstall, version verification, lint, tests, and local `ui-smoke` pass for this checkout.
- The release remains local-first, read-only, presentation-only for i18n wording, and derived from existing UI payload contracts.
- `v1.14.0` still does not imply hosted auth, default-on mutation, multi-user-safe authority, localized machine-readable payload values, correctness proof, or security certification.

## v1.13.0 - 2026-06-24

### Added
- `v1.13.0` release-track documents:
  - `docs/releases/status/release-status-v1.13.0.md`
  - `docs/releases/readiness/release-readiness-v1.13.md`
  - `docs/releases/notes/release-notes-v1.13.0.md`
  - `docs/releases/smoke/smoke-test-v1.13.md`
  - `docs/releases/remaining/v1.13-release-remaining-issues.md`
- Dedicated `v1.13.0` release-lane framing for local reviewer-boundary structured presentation contracts.
- Shared drilldown message-template keys and message params across overview, list, and detail reviewer-boundary summaries.
- `ui-smoke` coverage for explicit reviewer-boundary drilldown message-template fields.

### Changed
- Project version finalized as `1.13.0`.
- `v1.13.0` release-lane documents now treat `v1.12.0` as the historical published baseline rather than the active repository-side lane.
- Reviewer-boundary drilldown rendering now prefers shared template-based presentation copy before fallback literals.

### Notes
- `v1.13.0` is a local reviewer-boundary structured-presentation-contract release over the published `v1.12.0` baseline.
- Repository-side release preparation is complete once editable reinstall, version verification, lint, tests, and local `ui-smoke` pass for this checkout.
- The release remains local-first, read-only, presentation-only for i18n wording, and derived from existing UI payload contracts.
- `v1.13.0` still does not imply hosted auth, default-on mutation, multi-user-safe authority, localized machine-readable payload values, correctness proof, or security certification.

## v1.12.0 - 2026-06-24

### Added
- `v1.12.0` release-track documents:
  - `docs/releases/status/release-status-v1.12.0.md`
  - `docs/releases/readiness/release-readiness-v1.12.md`
  - `docs/releases/notes/release-notes-v1.12.0.md`
  - `docs/releases/smoke/smoke-test-v1.12.md`
  - `docs/releases/remaining/v1.12-release-remaining-issues.md`
- Dedicated `v1.12.0` release-lane framing for local reviewer-boundary presentation/read-model drilldown.
- Read-only reviewer-boundary drilldown summaries across overview, runtime, review, and summary payloads.
- HTML-shell visibility for reviewer-boundary drilldown summaries across overview, list, and detail surfaces.
- Dominant reviewer-boundary state navigation from overview into matching list slices.
- Structured reviewer-boundary drilldown message and fact-line template fields for presentation-layer i18n.
- `ui-smoke` contract coverage for reviewer-boundary drilldown summaries and their structured presentation fields.

### Changed
- Project version finalized as `1.12.0`.
- `v1.12.0` release-lane documents now treat `v1.11.0` as the historical published baseline rather than the active repository-side lane.
- Reviewer-boundary overview, list, and detail rendering now formats localized dataset and status copy from structured read-only summary fields.

### Notes
- `v1.12.0` is a local reviewer-boundary presentation-drilldown release over the published `v1.11.0` baseline.
- Repository-side release preparation is complete once editable reinstall, version verification, lint, tests, and local `ui-smoke` pass for this checkout.
- The release remains local-first, read-only, presentation-only for i18n wording, and derived from existing UI payload contracts.
- `v1.12.0` still does not imply hosted auth, default-on mutation, multi-user-safe authority, localized machine-readable payload values, correctness proof, or security certification.

## v1.11.0 - 2026-06-24

### Added
- `v1.11.0` release-track documents:
  - `docs/releases/status/release-status-v1.11.0.md`
  - `docs/releases/readiness/release-readiness-v1.11.md`
  - `docs/releases/notes/release-notes-v1.11.0.md`
  - `docs/releases/smoke/smoke-test-v1.11.md`
  - `docs/releases/remaining/v1.11-release-remaining-issues.md`
- Dedicated `v1.11.0` release-lane framing for local reviewer-boundary smoke-contract hardening.
- Reviewer-boundary smoke checks for overview summaries, list-row statuses, detail summaries, and HTML continuity markers.
- Reviewer-boundary count-consistency smoke checks between overview aggregates and runtime, review, and summary list-row statuses.

### Changed
- Project version finalized as `1.11.0`.
- `v1.11.0` release-lane documents now treat `v1.10.0` as the historical published baseline rather than the active repository-side lane.

### Notes
- `v1.11.0` is a local reviewer-boundary smoke-contract release over the published `v1.10.0` baseline.
- Repository-side release preparation is complete once editable reinstall, version verification, lint, tests, and local `ui-smoke` pass for this checkout.
- The release remains local-first, read-only, preview-only for GUI mutation, and derived from existing UI payload contracts.
- `v1.11.0` still does not imply hosted auth, default-on mutation, multi-user-safe authority, new reviewer-boundary persistence, correctness proof, or security certification.

## v1.10.0 - 2026-06-23

### Added
- `v1.10.0` release-track documents:
  - `docs/releases/status/release-status-v1.10.0.md`
  - `docs/releases/readiness/release-readiness-v1.10.md`
  - `docs/releases/notes/release-notes-v1.10.0.md`
  - `docs/releases/smoke/smoke-test-v1.10.md`
  - `docs/releases/remaining/v1.10-release-remaining-issues.md`
- Dedicated `v1.10.0` release-lane framing for local reviewer-boundary observability and i18n-ready presentation alignment.
- Reviewer-boundary overview aggregation across runtime records, review queue rows, and summary jobs.
- Reviewer-boundary slice/filter navigation from overview counts into read-only list surfaces.
- Translation-key routing for reviewer-boundary badges, metrics, and fact labels.

### Changed
- Project version finalized as `1.10.0`.
- `v1.10.0` release-lane documents now treat `v1.9.0` records as historical published baseline rather than the active release lane.

### Notes
- `v1.10.0` is a local reviewer-boundary observability release over the published `v1.9.0` baseline.
- Repository-side release preparation is complete once version verification, lint, tests, and UI smoke pass for this checkout.
- The release remains local-first, explicit-enable, read-only-by-default, and fail-closed.
- `v1.10.0` still does not imply hosted auth, default-on mutation, multi-user-safe authority, hidden runtime execution, GraphRAG runtime, vector DB, graph DB, correctness proof, or security certification.

## v1.9.0 - 2026-06-23

### Added
- `v1.9.0` release-track documents:
  - `docs/releases/status/release-status-v1.9.0.md`
  - `docs/releases/readiness/release-readiness-v1.9.md`
  - `docs/releases/notes/release-notes-v1.9.0.md`
  - `docs/releases/smoke/smoke-test-v1.9.md`
  - `docs/releases/remaining/v1.9-release-remaining-issues.md`
- Dedicated `v1.9.0` release-lane framing for local reviewer/session enforcement-boundary hardening.
- Explicit `reviewer_enforcement_summary` visibility for route-enforced versus descriptive-only reviewer/session conditions.
- Explicit `reviewer_validation_gate_summary` visibility for validation, authorization, target-state, and durable-write failure families.

### Changed
- Project version finalized as `1.9.0`.
- `v1.9.0` release-lane documents now treat `v1.8` records as historical context rather than the active release lane.

### Notes
- `v1.9.0` is a local reviewer/session enforcement-boundary release over `v1.8.0`.
- Repository-side release preparation is complete, but external publication remains a separate release-operator step.
- The release remains local-first, explicit-enable, and fail-closed.
- `v1.9.0` still does not imply hosted auth, default-on mutation, multi-user-safe authority, hidden runtime execution, GraphRAG runtime, vector DB, graph DB, correctness proof, or security certification.

## v1.8.0 - 2026-06-23

### Added
- `v1.8.0` release-track documents:
  - `docs/releases/status/release-status-v1.8.0.md`
  - `docs/releases/readiness/release-readiness-v1.8.md`
  - `docs/releases/notes/release-notes-v1.8.0.md`
  - `docs/releases/smoke/smoke-test-v1.8.md`
  - `docs/releases/remaining/v1.8-release-remaining-issues.md`
- Dedicated `v1.8.0` release-lane framing for local GUI review-route contract hardening.
- Explicit read-only local UI review-route visibility for:
  - per-action route-family semantics
  - CLI-equivalent route semantics
  - HTTP status-code semantics for the current fail-closed local boundary

### Changed
- Project version finalized as `1.8.0`.
- `v1.8.0` release-lane documents now treat `v1.7` records as historical context rather than the active release lane.

### Notes
- `v1.8.0` is a local GUI review-route contract-hardening release over `v1.7.0`.
- Repository-side release preparation is complete, but external publication remains a separate release-operator step.
- The release remains local-first, explicit-enable, and fail-closed.
- `v1.8.0` still does not imply hosted UI, default-on mutation, multi-user auth, hidden runtime execution, GraphRAG runtime, vector DB, graph DB, correctness proof, or security certification.

## v1.7.0 - 2026-06-23

### Added
- Local placeholder AI index CLI surface:
  - `chronicle ai-index status`
  - `chronicle ai-index vector add`
  - `chronicle ai-index vector search`
  - `chronicle ai-index graph add-node`
  - `chronicle ai-index graph add-edge`
  - `chronicle ai-index graph neighbors`
- Local file-backed placeholder AI index storage:
  - `.chronicle/ai_indexes/vector_index.json`
  - `.chronicle/ai_indexes/graph_index.json`
- Read-only local UI visibility for placeholder AI index surfaces:
  - `/api/ai-index-status`
  - `/api/ai-index-vector`
  - `/api/ai-index-graph-nodes`
  - `/api/ai-index-graph-edges`
- Placeholder AI index detail JSON for vector entries and graph nodes.
- CLI contract, README, and placeholder AI index documentation updates.

### Changed
- `chronicle init` now creates the `.chronicle/ai_indexes/` directory for local placeholder index surfaces.
- UI smoke now validates read-only placeholder AI index endpoints in addition to the existing local UI data surface.

### Notes
- Placeholder AI indexes are derived local surfaces, not primary records.
- Placeholder vector search uses local token-overlap and substring scoring only.
- No LLM, embedding provider, vector DB, graph DB, GraphRAG runtime, or external service is invoked.
- Read-only UI visibility does not imply GUI mutation, approval automation, or correctness proof.

## v1.4.0 - 2026-06-17

### Added
- Local installer hardening for moved/recreated release tags.
- Forced refresh of requested local release tags from origin by default.
- `CHRONICLE_STACK_ALLOW_MOVED_TAG=0` opt-out for non-forced tag fetch semantics.
- Installer checkout commit logging.
- Local deployment documentation for moved/recreated tag handling and clean smoke guidance.

### Changed
- Project version finalized as `1.4.0`.
- `scripts/install-local.sh` now explicitly resolves requested branch/tag refs before checkout.
- Local installer uses `pip install --force-reinstall` to reduce stale package installs.
- README release status now points to v1.4.0 preparation.

### Notes
- v1.4.0 is a local installer hardening release over v1.3.0.
- Moving release tags remains exceptional and should be evidence-recorded.
- Installer success is diagnostic and is not correctness proof or security certification.
- The installer still does not install a daemon, service, hosted UI, model API, GraphRAG runtime, vector DB, or graph DB.
- Commercial SaaS license and contributor policy drafts remain draft completed / counsel review pending.
- Tag creation, GitHub Release publication, and installer smoke from tag remain explicit release-operator steps.

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
