# Stage 2 Performance Baseline

Status: Measured
Date: 2026-07-13
Environment: local macOS development checkout, Python 3.11 virtual environment

## Baseline

The Stage 2 release gate uses deterministic local checks; no external runtime is contacted.

| Check | Result |
|---|---:|
| Ruff (`src/`, `tests/`) | passed |
| Full pytest suite | 508 passed in 26.89 s |
| Transport boundary tests | 7 passed in 1.42 s |
| Local UI smoke | passed; no server, browser, or external runtime |

These numbers are regression indicators, not cross-machine service-level objectives. Re-measure after dependency, Python, storage, or runtime transport changes.
