# Changelog

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
- v0.6 smoke-test checklist.

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
- `chronicle-context check` auxiliary CLI.
- Prompt-injection boundary helpers:
  - `scan_text_for_prompt_injection(...)`
  - `format_as_chronicle_data_block(...)`
- Audit log surface:
  - `.chronicle/audit.jsonl`
  - `AuditEvent`
  - `AuditLogStore`
  - `AuditService`
- Lifecycle log surface:
  - `.chronicle/lifecycle.jsonl`
  - `LifecycleEvent`
  - `LifecycleStore`
  - `LifecycleService`
- Integrity metadata preparation helpers:
  - `canonical_json_bytes(...)`
  - `sha256_digest(...)`
  - `build_integrity_metadata(...)`
  - `verify_integrity_metadata(...)`
- Doctor security-readiness checks.
- Security-aware export profiles:
  - `public-review`
  - `internal-review`
  - `local-analysis`
  - `restricted-summary`
- `chronicle-export profile` auxiliary CLI.
- Encrypted store abstraction:
  - `EncryptedStore`
  - `EncryptionEnvelope`
- Controlled integration package contract for future CSG-RAG / Sayane workflows.
- `chronicle-package context` auxiliary CLI.
- v0.5 release readiness and smoke test documentation.

### Changed
- `chronicle doctor` now reports security-readiness warnings. A newly initialized Chronicle may report `warning` even when structurally valid.
- Export manifest options now include an optional profile value when using security-aware export profiles.
- README quickstart includes v0.5 auxiliary commands.
- Project version is finalized as `0.5.0` for release/tag preparation.

### Notes
- `chronicle.jsonl` remains the primary record.
- Classification metadata, operation permissions, doctor warnings, export profiles, and packages are advisory and do not provide access control.
- Context-use checks are dry-runs and do not submit records to model services.
- Prompt-injection scanning is lightweight and incomplete by design.
- Audit and lifecycle logs are JSONL surfaces, not tamper-proof logs.
- Integrity hashes are drift-detection helpers, not proof.
- Encrypted store abstraction does not provide encryption by itself.
- Controlled integration packages are transport contracts, not GraphRAG engines, model runtimes, or permission grants.
- GraphRAG engine, vector DB, graph DB, external model API calls, real encryption backend, key management, authentication, authorization, tenant isolation, and lifecycle enforcement remain out of scope.

## v0.4.0 - 2026-06-14

### Added
- Operational readiness layer for local Chronicle projects.
- `chronicle doctor` and `chronicle doctor --json` for read-only health checks.
- Doctor checks for `.chronicle/`, `chronicle.jsonl`, metadata, JSONL parseability, derived indexes, artifact files, InjectionPlan references, graph export availability, and HTML export availability.
- Export Manifest model and service.
- Export Manifest metadata in YAML export, graph-json export, and HTML dashboard export.
- Redaction-aware export options for YAML and HTML:
  - `--redact-sensitive`
  - `--exclude-sensitive`
- Static HTML dashboard section navigation and stable local anchors.
- Static HTML dashboard local row filtering.
- `chronicle-graph` auxiliary console command for read-only graph export inspection.
- `chronicle-graph summary`, `chronicle-graph nodes`, and `chronicle-graph edges` commands.

### Changed
- v0.4 focuses on operational reliability rather than new memory semantics.
- Ruff configuration aligned with the current codebase style.
- HTML dashboard remains a single-file, static, read-only derived view while becoming easier to inspect.
- Export outputs now carry stronger provenance metadata where supported.

### Notes
- `chronicle.jsonl` remains the primary record.
- All indexes, exports, dashboards, graph-json outputs, and graph inspection outputs remain derived views.
- `chronicle doctor` is read-only and does not repair or mutate records.
- Export Manifest is provenance metadata, not cryptographic proof.
- Redaction-aware export is explicit opt-in and is not access control.
- Dashboard filtering is local display filtering, not a live dashboard server.
- `chronicle-graph` inspects graph-json-derived structure; it is not a GraphRAG engine.
- GraphRAG query engine, embeddings, vector database integration, graph database integration, live dashboard, editing UI, authentication, cloud sync, and automatic LLM injection remain out of scope.

## v0.3.0 - 2026-06-13

### Added
- Interface stability and serialization contracts (`docs/interface-contracts.md`).
- Contract tests for JSONL primary records, EventType payload shapes, model compatibility, CLI JSON output, rebuild, and export behavior.
- Explicit Injection Plan persistence via `chronicle injection plan --record`.
- `injection_plan_recorded` Chronicle Event type.
- Graph-ready export boundary and deterministic `graph-json` export.
- Graph candidate models for nodes, edges, and graph export snapshots.
- Static read-only HTML dashboard export via `chronicle export --format html`.
- `chronicle --version` CLI option.
- CLI UX tests for version, help, and invalid-input behavior.

### Changed
- Project metadata updated for v0.3 development (`0.3.0.dev0`).
- CLI help text updated for the Chronicle Stack v0.3 feature set.
- Documentation expanded for GraphRAG boundary, interface contracts, commercial support scope, and contributor license policy.
- Injection Plans remain non-persistent by default; persistence is now available only by explicit `--record`.
- Export surface now includes `yaml`, `markdown`, `graph-json`, and `html`.

### Notes
- `chronicle.jsonl` remains the primary record.
- `graph-json` and HTML dashboard exports are derived views.
- GraphRAG query engine, embeddings, vector database integration, graph database integration, live dashboard, authentication, editing UI, and redaction are out of scope for v0.3.
- Visibility hints are not access control or redaction.
- Boundary Rules are advisory.
- Injection Plans do not inject anything into LLMs.

## v0.2.0 - 2026-06-13

### Added
- Formal Context Scope Model (`ContextScope`) for Context records.
- Backward-compatible loading from v0.1 `scope_hint`.
- `VisibilityHint` for Context and Artifact records.
- CLI support for setting Context / Artifact visibility (`--visibility`).
- Structured SourceProvenance metadata for Events, Contexts, and Artifacts.
- CLI support for source metadata on record, add-context, and artifact create.
- Context Boundary Rule model and CLI (boundary add/list/check).
- Boundary rule index rebuild support.
- Rule-based Context Injection Plan generation.
- `chronicle injection plan` CLI command.

### Changed
- License changed to AGPL-3.0-or-later for v0.2.0 and later, with commercial licensing available separately from ZYX Corp株式会社.
- Earlier releases that were published under different license terms are not retroactively changed by this transition.

## v0.1.0 - 2026-06-13

### Added
- Chronicle Event JSONL primary store (`chronicle.jsonl`)
- Artifact create / update / history with version snapshots
- Decision records (accepted, rejected, deferred, etc.)
- RDE Diff Records with six fixed audit fields
- RDE Markdown reports (`.chronicle/reports/rde/`)
- RDE-to-ArtifactVersion derived linkage (via `index rebuild`)
- YAML and Markdown export (`chronicle export`)
- CLI integration tests (`test_cli.py`)
- GitHub Actions CI (ruff + pytest)

### Fixed
- Persist `ArtifactVersion.source_event_id` in `chronicle.jsonl`
- Persist `Decision.event_id` in `chronicle.jsonl`
- Prevent accidental empty artifact updates (`ARTIFACT_CONTENT_MISSING` error)

### Notes
