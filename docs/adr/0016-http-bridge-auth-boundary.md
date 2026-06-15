# ADR-0016: HTTP Bridge Auth Dependency Boundary

Status: Accepted  
Date: 2026-06-15  
Scope: Chronicle Stack future HTTP bridge / Sayane integration guidance  
Related: ADR-0010, ADR-0011, ADR-0013, #87

## Context

Chronicle Stack currently has no in-repository FastAPI bridge, HTTP runtime server, or bearer-token route dependency surface.

The current Chronicle Stack implementation is primarily local-first and file/CLI oriented:

```text
primary JSONL records
index rebuilds
exports
package persistence
package inspection
lifecycle/audit derived surfaces
Observation E2E documentation
```

A separate Sayane Local Bridge design decision clarified a FastAPI route-auth dependency boundary:

```text
HTTP authentication that exists only to authorize a route should be registered as route metadata.
```

In that context, using dummy endpoint parameters for authentication caused dependency-shape drift risks:

```python
def endpoint(_: Annotated[None, Depends(require_bearer)]) -> dict:
    ...
```

or:

```python
def endpoint(_: Annotated[None, Depends(require_bearer)] = None) -> dict:
    ...
```

The accepted bridge-side pattern was route-level dependency metadata:

```python
@router.get("/example", dependencies=[Depends(require_bearer)])
def get_example() -> dict:
    return {"ok": True}
```

Chronicle Stack does not need a direct implementation change from that decision today. However, Chronicle Stack may later integrate with Sayane, CSG-RAG, local bridge services, package-consumption servers, or controlled HTTP runtime adapters.

If such HTTP bridge surfaces are added, the auth dependency boundary should be documented before implementation begins so that authentication, endpoint business input, package payloads, and derived-output policy do not become entangled.

## Decision

Chronicle Stack adopts the following design guidance for future HTTP bridge or Sayane integration surfaces:

```text
No direct Chronicle Stack implementation change is required now.
```

For future HTTP bridge routes, authentication dependencies that exist only to authorize a route should be represented as route metadata, not as endpoint business parameters.

Preferred pattern:

```python
@router.get("/path", dependencies=[Depends(require_bearer)])
def endpoint(...):
    ...
```

Rejected future pattern:

```python
def endpoint(_: Annotated[None, Depends(require_bearer)]) -> dict:
    ...
```

Also rejected:

```python
def endpoint(_: Annotated[None, Depends(require_bearer)] = None) -> dict:
    ...
```

If Chronicle Stack later exposes a FastAPI or similar HTTP bridge, the bridge should keep these roles separate:

```text
auth dependency        = route authorization metadata
endpoint parameters    = request data consumed by endpoint business logic
primary JSONL          = source-of-truth record surface
derived exports        = derived projections, not enforcement
packages               = transport contracts, not permission grants
lifecycle markers      = advisory derived-output signals unless explicitly enforced later
```

## Rationale

Chronicle Stack already treats security-aware metadata, lifecycle markers, export filtering, audit records, and packages as distinct surfaces with explicit boundaries.

HTTP route authentication should follow the same discipline.

Authentication is not part of the endpoint payload shape. Treating auth-only dependencies as dummy endpoint parameters creates several risks:

1. The web framework may interpret the dependency marker as a missing request parameter and return request-shape errors such as `422` instead of authentication errors.
2. Adding a default to make the endpoint callable may hide the dependency execution path in some refactor shapes.
3. Endpoint signatures become polluted by values that the endpoint does not actually consume.
4. Observation E2E may confuse auth-boundary drift with payload-shape drift.

Route-level dependency metadata better expresses the intended meaning:

```text
execute this authorization dependency before endpoint logic
```

This preserves a clean distinction between authorization boundary and business request schema.

## Consequences

### Positive

- Future Sayane / Chronicle Stack bridge integration has a clear auth dependency convention.
- HTTP route auth remains separate from package, export, lifecycle, and primary JSONL semantics.
- Endpoint signatures stay focused on request data that endpoint logic actually consumes.
- Observation E2E scenarios can distinguish authentication failures from request payload-shape failures.
- The project avoids prematurely introducing HTTP runtime code only to encode a design rule.

### Negative / Cost

- Future HTTP route modules must consistently attach route-level dependencies to protected routes.
- Authentication may be less visible in endpoint function signatures, though more visible in route metadata.
- This ADR is guidance until Chronicle Stack actually has an HTTP bridge surface.
- Framework-specific behavior still requires focused validation in the future implementation environment.

## Required Future Pattern

If Chronicle Stack introduces protected HTTP route modules, they should follow this pattern:

```python
from fastapi import APIRouter, Depends


def register_example_routes(app, require_bearer):
    router = APIRouter()

    @router.get("/example", dependencies=[Depends(require_bearer)])
    def get_example() -> dict:
        return {"ok": True}

    app.include_router(router)
```

If the endpoint requires request body, path, query, or header values for business logic, those values remain normal function parameters.

The auth dependency remains route metadata.

## Observation E2E Guidance

If an HTTP bridge is later added, Observation E2E should include auth-boundary scenarios such as:

```text
missing auth       -> authentication failure, not success
invalid auth       -> authentication failure, not success
valid auth         -> protected endpoint reachable
payload mismatch   -> request-shape failure, not auth-boundary failure
```

The exact status code and error detail must be specified by the bridge implementation ADR or contract tests at that time.

Observation E2E pass must not be treated as proof of security, token secrecy, or access-control sufficiency.

## Non-goals

This ADR does not:

- add a Chronicle Stack HTTP bridge
- add FastAPI as a Chronicle Stack dependency
- alter CLI behavior
- alter package persistence behavior
- alter export behavior
- alter lifecycle marker semantics
- alter bearer token validation semantics in Sayane
- define Sayane bridge internals
- introduce physical deletion or access-control enforcement
- introduce external model, vector DB, graph DB, embedding, or runtime calls

## RDE Review

### Preserved

- Chronicle Stack remains local-first and file/CLI oriented unless a future ADR changes that.
- Primary JSONL remains the source-of-truth record surface.
- Derived exports remain derived projections.
- Packages remain transport contracts, not permission grants.
- Lifecycle markers remain advisory derived-output signals unless later explicitly enforced.
- Observation E2E remains non-certifying.

### Transformed

- A Sayane Local Bridge implementation lesson is generalized into Chronicle Stack future integration guidance.
- Auth dependency placement is framed as a responsibility-boundary issue, not merely a FastAPI syntax preference.

### Added

- A future HTTP bridge auth dependency convention.
- A rejected-pattern list for auth-only dummy endpoint parameters.
- Observation E2E guidance for future auth-boundary scenarios.

### Unresolved

- Whether Chronicle Stack will introduce an HTTP bridge.
- Whether Chronicle Stack will consume Sayane bridge routes directly or through package files only.
- Exact HTTP status codes and error details for any future Chronicle-controlled bridge.
- Where auth contract tests should live if an HTTP bridge is introduced.

### Deviation Risks

- Applying this ADR to non-HTTP surfaces such as CLI commands or local file operations.
- Treating route-level dependencies as complete access-control design rather than route authorization plumbing.
- Treating Observation E2E auth success as security certification.
- Allowing future HTTP bridge implementation convenience to blur primary JSONL, package transport, derived export, and authorization boundaries.
