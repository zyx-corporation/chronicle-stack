# Chronicle Stack Release Tag Policy

Status: v1.6 release operations policy  
Scope: release tag immutability and corrective retag evidence

## Purpose

This document defines Chronicle Stack's release tag policy.

The default rule is simple:

```text
Published release tags are immutable.
```

A release tag should identify one stable release commit. Release tags should not be moved as part of normal operations.

## Background

Chronicle Stack v1.4 hardened the local installer against stale local tags after exceptional retag events.

Chronicle Stack v1.5 added a release operator guide that documents manual release execution evidence.

This policy complements both documents:

- [Release Operator Guide](release-operator-guide.md)
- [curl-based Local Deployment](local-deployment-curl.md)

## Default rule

After publication, release tags such as `v1.5.0` are treated as immutable.

Normal release execution should follow this order:

1. Merge repository-side release preparation.
2. Confirm latest `main` is ready.
3. Create annotated release tag once.
4. Publish GitHub Release once.
5. Run installer and smoke evidence from that tag.
6. Close the release execution issue only after evidence is recorded.

## Exceptional corrective retag

A corrective retag is allowed only when all of the following are true:

- the tag points to the wrong commit
- release evidence shows the mismatch
- the correction is recorded in the release execution issue
- the corrected tag is verified against latest `main`
- fresh installer smoke is rerun from the corrected tag
- the GitHub Release notes are checked or edited if needed

Corrective retagging is not a routine release mechanism.

## Required evidence after corrective retag

Record these items in the release execution issue:

```text
## Retag reason
## Old tag evidence
## Corrected tag evidence
## Tag/main equivalence evidence
## Clean installer smoke after correction
## Existing-checkout reinstall smoke after correction
## UI smoke continuity after correction
## Boundary note
```

Minimum evidence:

```bash
git rev-parse main
git rev-parse 'vX.Y.Z^{}'
```

or connector comparison:

```text
compare base=vX.Y.Z head=main
status: identical
ahead_by: 0
behind_by: 0
```

For annotated tags, compare the dereferenced tag commit:

```bash
git rev-parse 'vX.Y.Z^{}'
```

Do not rely on raw `git rev-parse vX.Y.Z` for commit comparison because it may return the tag object SHA.

## Installer behavior

The installer has moved-tag hardening for exceptional correction cases.

By default, requested local tag refs are refreshed from origin before checkout.

Operators can disable forced tag refresh:

```bash
CHRONICLE_STACK_ALLOW_MOVED_TAG=0 bash install-local.sh
```

This opt-out preserves ordinary non-forced tag fetch semantics. It does not make retagging routine.

## GitHub Release already exists

If GitHub reports:

```text
Release.tag_name already exists
```

Interpretation:

- a GitHub Release already exists for that tag
- this may be accepted as release-existence evidence
- tag/main equivalence and release notes should still be checked

If release notes need correction:

```bash
gh release edit vX.Y.Z \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack vX.Y.Z" \
  --notes-file docs/release-notes-vX.Y.Z.md
```

## Boundary

This policy does not add:

- automated tag protection
- release automation
- GitHub Actions release publishing
- package publishing
- daemon or service installation
- hosted UI
- external model API
- GraphRAG runtime
- vector DB
- graph DB
- legal contract finalization

Smoke evidence remains diagnostic. It is not correctness proof, security certification, access-control enforcement, or legal compliance certification.

## Warning classification

- Release warning: release tags are immutable by default.
- Corrective warning: retagging is exceptional and requires evidence.
- Runtime warning: this policy does not imply hosted runtime or background services.
- Semantics warning: smoke remains diagnostic, not certification or proof.
- Legal warning: this is an operations policy, not legal contract finalization.

## RDE review

### Preserved

- Evidence-based release execution.
- Local-first installer smoke.
- Annotated tag verification discipline.
- No-daemon/no-service/no-external-runtime boundaries.

### Transformed

- Repeated retag caution becomes explicit release policy.

### Supplemented

- Immutable-by-default rule.
- Corrective retag criteria.
- Required retag evidence sections.
- Annotated tag dereference guidance.

### Unresolved

- Platform-enforced tag protection.
- Future release automation.
- Package publishing.
- Legal/governance finalization.

### Deviation risks

- Normalizing retagging.
- Treating smoke as certification.
- Confusing operational policy with legal terms.
- Over-automating releases before evidence workflow is stable.
