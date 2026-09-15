# 2026-09-15 — CY-1 remaining security work

## Manifest and adoption boundary

Execute the supplied CY-1 remaining-work instruction: preserve the daemon hotfix, close browser
request/credential exposure, cover all HTTP methods and replace daemon argv/stdout token delivery.
This entry uses CY-1/CY-2 as named in that instruction; it does not redefine the differently named
Yard roadmap milestones. Event Origin implementation and shared Core authorization remain outside
this task. The security hotfix exception in ADR-0100 applies; functional branches and reviewable
commits preserve the work before PR integration, without direct main edits.

## Existing state and preserved work

The starting branch was `codex/hotfix-daemon-request-boundary` at `ad2b9e2c`. Its uncommitted work
included the entire daemon/API implementation, its dependencies, UI session hardening, and unrelated
Yard/Event Origin documentation. The daemon had no tracked implementation to patch independently.
The required API baseline and hotfix were therefore preserved together in `3b12e6a`; the existing
UI implementation was preserved separately in `2b78cf0`. Their earlier TDD claims are inherited
history, not a red phase observed during this task. The initial working tree passed 559 tests and
Ruff. Unrelated document edits remain unstaged in the original workspace and are excluded from this
security integration branch's committed tree.

## Design and implementation

- Task 0: daemon baseline/hotfix committed on `codex/hotfix-daemon-request-boundary`.
- Task 1: existing one-time UI bootstrap and cookie/mutation separation reviewed and committed on
  `codex/cy1-ui-session-boundary`. Added service-spy tests for unauthorized capture, all review
  actions, GraphRAG query and rebuild; no service calls or JSONL byte changes occur.
- Task 3: `codex/cy1-http-method-boundary` adds a shared parsed-request gate before dispatch.
  Every method, including unknown names, passes Host/Origin validation. Unsupported methods return
  405 with `Allow: GET, POST`; HEAD omits the body. CORS remains disabled (ADR-0104/0106).
- Task 2: `codex/cy1-daemon-token-file` adds exclusive 0600 generated credential files and removes
  `--session-token` plus metadata credentials. ADR-0107 records the breaking draft startup migration,
  generated entropy, candidate screening, file lifecycle and abrupt-shutdown limitations.
- Integration: `codex/cy1-security-closeout` carries the functional commits and operator/index docs.
  Integration uses a PR, with main merge subject to the operator's requested confirmation.

## Verification evidence

- New all-method boundary regressions: observed 3 failures and 1 pass before implementation;
  then 62 focused UI/daemon/boundary tests passed.
- New credential regressions: observed 17 failures before implementation; the expanded suite of
  19 credential tests then passed, including a real subprocess authenticated read and SIGTERM
  cleanup, file modes, symlinks, collisions, weak tokens, secrecy and replacement preservation.
- The final full-suite and canonical local `act` results are recorded in the integration PR with
  the tested commit, command, platform, image and result. Native pytest evidence is 582 tests.
- Local development logs are task artifacts under `/tmp/chronicle-cy1-*`; they are not primary
  Chronicle records or enduring CI attestations.

## Failure Note

A new subprocess regression initially tried `python -m chronicle`, but this repository exposes
`chronicle.cli:main` and has no package `__main__.py`. The full run consequently had 1 failure and
581 passes. The test now invokes the installed entrypoint function in a separate interpreter.
Future lifecycle tests must use the actual project entrypoint rather than infer a module launcher.

## T-RDE

### Preserved

Append-only JSONL authority, Core-mediated writes, explicit foreground operation, default read-only
UI, workspace enablement, reviewer checks, non-browser daemon and no external connector execution.

### Transformed

Public UI HTML is a locked shell; authenticated session responses issue mutation credentials.
Method-specific validation becomes a shared pre-dispatch HTTP boundary. Daemon credential delivery
moves from arguments/startup output to an exclusively created private file.

### Supplemented

Negative socket tests, service non-invocation assertions, token lifecycle tests, explicit 405/Allow
contract, metadata versioning, migration guidance and functional commit boundaries.

### Unresolved

Same-UID process isolation, UI browser-opener fragment exposure, abrupt-termination stale files,
CY-2 transport-neutral authorization/resource scopes, and final human approval of main integration.
A green test run does not certify security or complete the broader Yard roadmap.

### Deviation risks

Mistaking character-distribution entropy for proof of random generation; treating a loopback cookie
or a file mode as multi-user authorization; including unrelated pre-existing semantic changes in a
security PR; silently reintroducing credential-disclosing compatibility paths.

### Next update policy

Reassess on every new HTTP route, credential consumer, browser delivery change, multi-user or remote
transport. Record final integration and remaining capability work in the PR/next task. Do not
rewrite existing chronicles or migrate authoritative event records as part of this security work.
