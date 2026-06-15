# Chronicle Stack v1.0.0 Smoke Test Profile

Issues: #165, #168

## Purpose

This smoke profile defines the minimum release-operator validation expected before publishing Chronicle Stack v1.0.0.

It turns the v0.9.0 installer smoke evidence into a repeatable stable-release validation profile.

## Pre-tag verification

Run from a clean checkout on the release branch or final release commit:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version before tag publication:

```text
chronicle 1.0.0
```

## CLI help smoke

```bash
chronicle --help
chronicle-context --help
chronicle-export --help
chronicle-package --help
chronicle-graph --help
chronicle-audit --help
chronicle-lifecycle --help
```

All commands should return help output without uncaught exceptions.

## Local installer smoke from tag

After the `v1.0.0` tag is pushed, run from a temporary directory:

```bash
rm -rf /tmp/chronicle-stack-v10-install-smoke
mkdir -p /tmp/chronicle-stack-v10-install-smoke
cd /tmp/chronicle-stack-v10-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v1.0.0/scripts/install-local.sh -o install-local.sh
less install-local.sh
bash install-local.sh

/tmp/chronicle-stack-v10-install-smoke/bin/chronicle --version
/tmp/chronicle-stack-v10-install-smoke/bin/chronicle --help
```

Expected version output:

```text
chronicle 1.0.0
```

## Installed command expectation

The installer should make the following commands available in its command directory:

- `chronicle`
- `chronicle-context`
- `chronicle-export`
- `chronicle-package`
- `chronicle-graph`
- `chronicle-audit`
- `chronicle-lifecycle`

## Required installer notes

The smoke evidence should preserve the following notes or equivalent wording:

- The installer does not install a daemon, service, web server, or HTTP runtime.
- The installer does not call external model APIs, GraphRAG engines, vector DBs, or graph DBs.
- Operators should inspect the script before piping it to `bash` in production-like environments.

## Failure classification

Release-blocking failures:

- `chronicle --version` does not report `1.0.0` after version finalization.
- Any stable CLI entry point fails to start or show help.
- Installer smoke cannot install from the `v1.0.0` tag.
- Installed `chronicle --version` does not report `1.0.0`.
- Smoke output implies installation of a daemon, server, model API, GraphRAG engine, vector DB, or graph DB.

Non-blocking but review-required findings:

- Cosmetic help text drift.
- Documentation wording mismatch that does not affect installability.
- Shell environment differences that require a documented operator note.

## Warning classification

- Runtime warning: installer smoke must not imply hidden daemon or hosted runtime installation.
- Evidence warning: smoke success is installability evidence, not full correctness proof.
- Operator warning: inspect-first installation remains preferred over blind pipe-to-bash.

## RDE review

### Preserved

- v0.9 local install boundary.
- Inspect-first installation posture.
- No-daemon / no-external-runtime warning.

### Transformed

- One-off v0.9 smoke evidence becomes a repeatable v1.0 release validation profile.

### Supplemented

- Stable CLI help smoke.
- Failure classification.
- Tag-based installer evidence expectations.

### Deviation risks

- Treating smoke success as complete correctness proof.
- Letting installer convenience blur local-first boundaries.
