# Release Notes v1.90.0

## Added

- `chronicle federation package create --signature-mode local_dev` for reviewable local-dev signed manifests
- federation package signature metadata for signing time, expiry, and revocation reason
- federation package verification outcomes for `unsigned`, `signed`, `mismatch`, `expired`, and `revoked`
- CLI and service coverage for signed-manifest verification behavior

## Boundary

- signed manifests remain local review surfaces and do not claim remote trust certification or identity proof
- verification stays package-local and does not add import, transport, or unattended sync behavior
