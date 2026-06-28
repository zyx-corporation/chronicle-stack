# Smoke Test v1.91

## Commands

- `ruff check src tests`
- `pytest -q`
- `python -m chronicle.cli add-context --title "Federation Consent Smoke" --summary "Smoke context" --json`
- `python -m chronicle.cli federation package create --purpose "Smoke review" --target-node node:partner:beta --consent-granted-by reviewer --consent-recorded-at 2026-06-28T08:00:00+00:00 --consent-scope project-review --no-third-party-sharing --third-party-sharing-reason "partner-only review" --output-dir /tmp/chronicle-federation-package-consent`
- `python -m chronicle.cli federation package inspect --package-dir /tmp/chronicle-federation-package-consent --json`
- `python -m chronicle.cli federation package verify --package-dir /tmp/chronicle-federation-package-consent --json`
