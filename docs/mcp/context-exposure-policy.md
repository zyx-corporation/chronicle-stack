# MCP Context Exposure Policy

This document defines the default exposure boundary for the Sayane MCP Server.

Sayane treats context as something accepted, scoped, and handed over by the user, not as an unrestricted memory dump. The MCP Server therefore exposes only review-safe context by default.

## Goals

- Preserve the Candidate review boundary introduced by Context Acceptance.
- Prevent pending or rejected Candidate content from being presented as accepted context.
- Make failure modes safe by default.
- Keep MCP useful for AI editors without turning it into an unbounded context export channel.

## Exposure classes

| Class | Default MCP exposure | Notes |
| --- | --- | --- |
| Global Profile | Allowed | Expose through an explicit profile resource/tool only. |
| Project Context | Allowed when selected | Expose only for the active or explicitly requested project. |
| Approved Candidate | Allowed with scope | Expose only after approval and with section/scope metadata. |
| Pending Candidate | Blocked | Must not be exposed as normal context. Review-only tooling may list metadata, not content, when explicitly requested. |
| Rejected Candidate | Blocked | Must not be exposed as normal context. Rejection lineage may be summarized only as audit metadata. |
| Raw Capture / Conversation Log | Blocked by default | May be used as lineage/source metadata, not as general MCP context. |
| Evaluation / RDE Result | Metadata only | Useful as warning or audit metadata. It is not a final judgment. |

## Default rules

1. The MCP Server must not expose pending Candidate content as reusable AI-editor context.
2. The MCP Server must not expose rejected Candidate content as reusable AI-editor context.
3. Approved Candidate content must carry scope metadata such as section, source, and acceptance lineage when available.
4. If a project is not selected, project context exposure must fail closed or return an empty result with a clear diagnostic.
5. If profile storage is not initialized, profile context exposure must fail closed.
6. If a client requests an unknown resource, the server must return a narrow error, not a broad fallback context.
7. Safety metadata may be exposed separately from content so that clients can show review state without silently using unaccepted content.

## Recommended MCP surface

The stable surface should prefer explicit resources/tools over implicit bulk dumps.

Suggested resources:

- `sayane://profile/current`
- `sayane://project/current`
- `sayane://candidate/approved`
- `sayane://lineage/recent`

Suggested tools:

- `sayane_get_profile_context`
- `sayane_get_project_context`
- `sayane_list_approved_candidates`
- `sayane_get_lineage_summary`

Review-only tools, if added, must be named clearly and must not be used as normal context providers:

- `sayane_list_pending_candidate_metadata`
- `sayane_get_candidate_review_status`

## Safe failure modes

The MCP Server should prefer an empty or diagnostic response over an overly broad response.

Examples:

- No active project: return `project_context_unavailable`.
- Storage not initialized: return `profile_storage_uninitialized`.
- Pending Candidate requested through normal context endpoint: return `candidate_not_approved`.
- Unknown scope: return `scope_not_found`.

## Smoke-test requirements

A smoke test should verify:

1. Profile context can be read when initialized.
2. Project context can be read only when a project is selected or explicitly specified.
3. Approved Candidate content can be exposed with scope metadata.
4. Pending Candidate content is not exposed through normal context endpoints.
5. Rejected Candidate content is not exposed through normal context endpoints.
6. Unknown resources fail closed.

## RDE audit note

This policy preserves the distinction between capture, review, acceptance, and reuse. The key risk is implementation convenience turning unaccepted Candidate content into effective long-term context. MCP integration must therefore be treated as a context boundary, not merely as an editor integration feature.
