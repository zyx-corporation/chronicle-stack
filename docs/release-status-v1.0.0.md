# Chronicle Stack v1.0.0 Release Status

Issues: #165, #167

## Status

Chronicle Stack v1.0.0 is the stable context sovereignty foundation release track.

At release-finalization time, the repository has completed:

- v0.6.0 release / hygiene
- v0.7 operational hardening and verified context workflows
- v0.8 verified package / export review workflow
- v0.9 release-candidate hardening and version finalization
- v1.0 stable release criteria and compatibility policy

## Release positioning

v1.0.0 stabilizes the local-first Chronicle Stack foundation. It does not claim to be a complete hosted system, a security enforcement layer, a correctness proof system, a GraphRAG runtime, or a downstream Sayane / CSG-RAG implementation.

## Stable surfaces

The following user-facing command surfaces are treated as the v1.0 stable compatibility set:

- `chronicle`
- `chronicle-context`
- `chronicle-export`
- `chronicle-package`
- `chronicle-graph`
- `chronicle-audit`
- `chronicle-lifecycle`

The stable claim applies to documented command names, documented options, documented status semantics, and documented JSON output expectations. It does not freeze private implementation details.

## Release evidence expected

A complete v1.0.0 release should preserve the following evidence:

- test result summary
- lint result summary
- `chronicle --version` output
- installer smoke output from the `v1.0.0` tag
- release notes
- release execution log

## Legal and governance status

The following documents remain draft completed / counsel review pending:

- `Commercial-SaaS-License.md`
- `docs/contributor-license-policy.md`

They are not final contracts, legal advice, or transaction-specific execution packages.

## Boundary notes

- Classification metadata is advisory metadata, not access control.
- Audit events are traceability metadata, not enforcement.
- Lifecycle markers are advisory metadata and do not mutate primary records by themselves.
- Package review is diagnostic and is not correctness proof.
- Graph-ready export is a derived local export surface, not a GraphRAG engine.
- Chronicle Stack v1.0.0 does not install or require a daemon, server, web runtime, model API, vector DB, or graph DB.

## Warning classification

- Documentation warning: release polish must not erase release history or evidence.
- Legal warning: draft legal/governance files remain counsel-review pending.
- Runtime warning: local installer evidence must not imply hidden hosted runtime installation.
- Semantics warning: stable release status must not overstate enforcement or proof.

## RDE review

### Preserved

- v0.9.0 release evidence remains visible.
- Local-first and inspect-first posture remains central.
- Advisory workflow limitations remain explicit.

### Transformed

- Release status shifts from release-candidate framing to stable v1.0 foundation framing.

### Supplemented

- Stable surface list.
- Release evidence expectations.
- Legal/governance draft status.

### Deviation risks

- Treating v1.0.0 as a hosted or enforcement system.
- Hiding counsel-review pending status.
- Replacing evidence with branding language.
