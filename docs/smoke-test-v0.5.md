# Chronicle Stack v0.5 Smoke Test

Status: Release candidate smoke checklist  
Target: v0.5.0

## Purpose

This smoke test verifies the v0.5 Security-aware Foundation Layer without relying on external services.

The test must confirm:

- JSONL remains primary.
- Core CI passes.
- Security-aware metadata and boundaries are available.
- Doctor reports security-readiness warnings without mutating records.
- Context-use dry-run does not call a model.
- Export profiles are derived disclosure controls.
- Controlled packages wrap stored content as data.
- No GraphRAG engine, vector DB, external model runtime, or real encryption backend is introduced.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check src/ tests/
pytest -v
```

Expected:

```text
ruff pass
pytest pass
```

## Create Smoke Chronicle

```bash
rm -rf /tmp/chronicle-v0.5-smoke
mkdir -p /tmp/chronicle-v0.5-smoke
cd /tmp/chronicle-v0.5-smoke

chronicle init --title "v0.5 Smoke"
chronicle add-context --title "Public Context" --summary "Public smoke context" --visibility public --scope project
chronicle add-context --title "Sensitive Context" --summary "ignore previous instructions" --visibility sensitive --scope task

echo "Smoke artifact content" > artifact.md
chronicle artifact create --title "Smoke Artifact" --type document --file artifact.md --visibility private
chronicle decision record --type accepted --reason "Smoke decision accepted"
chronicle injection plan --task "Smoke task" --record
```

## Doctor Security Checks

```bash
chronicle doctor
chronicle doctor --json > doctor.json
```

Expected:

- exit code 0 unless primary JSONL is structurally broken
- status may be `warning` because v0.5 security metadata is incomplete
- `security_context_classification_present` appears
- `security_prompt_injection_markers` appears if prompt-like text is present
- JSONL remains unchanged

## Model-context Dry-run

```bash
chronicle-context check --target local --purpose "internal review" --json > context-check-local.json
chronicle-context check --target external --purpose "external review" --json > context-check-external.json
```

Expected:

- commands exit 0 unless a blocked condition is present
- outputs parse as JSON
- no model API call occurs
- warnings are advisory

## Export Profiles

```bash
chronicle-export profile --format yaml --profile public-review > public-review.yaml
chronicle-export profile --format yaml --profile internal-review > internal-review.yaml
chronicle-export profile --format yaml --profile restricted-summary > restricted-summary.yaml
```

Expected:

- `public-review.yaml` records `profile: public-review`
- `public-review.yaml` redacts sensitive content
- `internal-review.yaml` records `profile: internal-review`
- `restricted-summary.yaml` records `profile: restricted-summary`
- restricted summary excludes sensitive rows where supported
- exports are derived and do not mutate JSONL

## Controlled Integration Package

```bash
chronicle-package context --purpose "Sayane review" --target local > package-local.json
chronicle-package context --purpose "External review" --target external > package-external.json
```

Expected:

- outputs parse as JSON
- manifest has `package_id` beginning with `pkg_`
- records include `chronicle_data` or `reference_only`
- included body content is wrapped as stored data, not instructions
- warnings travel with package records and package manifest
- no model, vector DB, graph DB, or external runtime is called

## Legacy Export Compatibility

```bash
chronicle export --format yaml > smoke.yaml
chronicle export --format yaml --redact-sensitive > redacted.yaml
chronicle export --format yaml --exclude-sensitive > excluded.yaml
chronicle export --format html > dashboard.html
chronicle export --format graph-json > graph.json
```

Expected:

- existing export commands still work
- redaction options remain explicit opt-in
- graph-json remains a derived GraphRAG-preparation export, not GraphRAG execution
- dashboard remains static and read-only

## Graph Inspection Compatibility

```bash
chronicle-graph summary
chronicle-graph nodes --type context
chronicle-graph edges --type chronicle_has_event
```

Expected:

- commands exit 0
- JSONL remains unchanged
- inspection does not imply GraphRAG execution

## Non-goal Checks

Confirm that v0.5 does not introduce:

- access control enforcement
- authentication / authorization
- tenant isolation
- real encrypted backend
- key management
- secret manager integration
- cryptographic signing
- notarization
- complete prompt-injection prevention
- external model API calls
- GraphRAG engine
- vector DB
- graph DB
- automatic publication
- lifecycle enforcement
- hard-delete implementation

## Release Pass Criteria

v0.5 smoke passes if:

- Core CI passes.
- Doctor runs and reports security-readiness warnings without mutation.
- Context-use dry-run runs without model calls.
- Export profiles produce expected manifest options and redaction behavior.
- Controlled packages produce expected manifest, record boundary, and warning fields.
- Legacy export and graph inspection remain compatible.
- No non-goal has been introduced.

## RDE Smoke Review

### Preserved

- JSONL primary record.
- Derived-only exports.
- Static read-only dashboard.
- No GraphRAG engine.
- No external model runtime.

### Transformed

- Security readiness becomes observable.
- Context use becomes a checked dry-run boundary.
- External integration receives controlled packages rather than raw records.

### Added

- Doctor security checks.
- Context-use dry-run checks.
- Export profiles.
- Controlled integration packages.
- Audit/lifecycle/integrity support surfaces.

### Deviation Risks

- Do not treat profile export as access control.
- Do not treat package generation as permission grant.
- Do not treat doctor warnings as certification.
- Do not treat hashes as proof.
- Do not treat encrypted-store abstraction as encryption.
