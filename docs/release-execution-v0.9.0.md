# Chronicle Stack v0.9.0 Release Execution

Status: release execution checklist  
Target tag: `v0.9.0`

## Preconditions

```bash
git checkout main
git pull --ff-only
git status --short
chronicle --version
ruff check src/ tests/
pytest -v
```

Expected:

```text
git status is clean
chronicle 0.9.0
283 passed
```

## Create tag

```bash
git tag -a v0.9.0 -m "Chronicle Stack v0.9.0"
git push origin v0.9.0
```

## Create GitHub Release

```bash
gh release create v0.9.0 \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack v0.9.0" \
  --notes-file docs/release-notes-v0.9.0.md
```

## Installer smoke

```bash
rm -rf /tmp/chronicle-stack-v09-install-smoke
mkdir -p /tmp/chronicle-stack-v09-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v0.9.0/scripts/install-local.sh \
  -o /tmp/chronicle-install-local.sh

INSTALL_DIR=/tmp/chronicle-stack-v09-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v09-install-smoke/bin \
CHRONICLE_STACK_REF=v0.9.0 \
bash /tmp/chronicle-install-local.sh

/tmp/chronicle-stack-v09-install-smoke/bin/chronicle --version
```

Expected:

```text
chronicle 0.9.0
```

## Post-release smoke

Run:

```text
docs/smoke-test-v0.9.md
```

## Completion criteria

- `v0.9.0` tag exists.
- GitHub Release exists.
- Installer smoke reports `chronicle 0.9.0`.
- v0.9 smoke profile passes.
- Release issue is closed as completed.
