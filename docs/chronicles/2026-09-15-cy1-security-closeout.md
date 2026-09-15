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

## PR separation follow-up

At the user's request, the five CY-1 commits are replayed onto main in
`codex/security-cy1-closeout`. The seven earlier documentation commits remain on
`codex/cy1-security-closeout`; ADR-0108 is retained there for the requested post-merge step.
Event Origin documents were uncommitted and remain untouched in the original workspace.
The daemon/API implementation and all tests are unchanged from the validated CY-1 tree.

The fifth cherry-pick conflicted in docs/README.md, docs/adr/README.md and docs/cli-reference.md
because main lacks the excluded documentation restructuring. Resolution preserves main's CLI
reference and ADR index, adds only CY-1 entries/instructions, and supplies a minimal API/security
index instead of importing the excluded documentation map. These were documentation dependency
conflicts, not runtime changes. References in earlier history to pending ADR-0098–0103 are retained
as provenance, not treated as newly adopted policy on main. The separate PR records the new
commit identities and fresh tests/lint/local CI; previous CI evidence applies only to its original
commit. Main merge awaits approval of the replacement PR, as explicitly required by the user.

## Approved security integration and residual-risk ADR placement

The operator explicitly approved PR #391. It merged into main as
`1b58ca9aaa65da3a9be3296666649498541aec22` after fresh validation of the isolated
head `19bff0cb4327a9b1d438764f2d9b0e817d81d780`: 582 native tests, Ruff, canonical
local act (582 tests and UI smoke), and GitHub CI run `34927747242` all passed.
PR #390 was closed without merging, and its original branch was retained.

The seven excluded documentation commits are preserved on `codex/docs-pending-review` at
`ad2b9e2c`; none entered main through #391. Original uncommitted Event Origin/Yard edits
remain in the original workspace. Source, tests and workflow in the separated security
head matched the original security tree exactly, including the daemon/API baseline and hotfix.

Following the requested order, ADR-0108 is now placed alongside existing ADRs at
`docs/adr/0108-daemon-token-residual-risk.md` in a separate documentation change based on
the merged main. Its text is recovered from `f7a46ada`, with the related PR link updated to
#391 while retaining #390 as the original draft. The index is updated. No automatic stale-token
cleanup, token reuse, code changes or deferred documentation adoption accompany this placement.

## 追加記録 — daemon token残留リスクADR

利用者の「これを追加ADRとしてください」という依頼を受け、添付の
`adr-daemon-token-residual-risk.md`をADR-0108として登録し、ADR一覧へ追加した。
異常終了時のファイル残留と今後の回収設計を保存したうえで、ADR-0107および実装に合わせ、
既存ファイル拒否・手動復旧が既定であること、同一UIDへの保護を保証しないこと、
停止済みdaemonの認証権限とtoken値の残留は別であることを明確化した。
将来の対応案は検討事項として記録し、今回の依頼による実装変更・自動回収・main統合は行わない。
