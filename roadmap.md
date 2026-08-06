# Chronicle Stack Roadmap Map

Status: Active
Scope: Repository entrypoint for roadmap navigation

This file is the root map for roadmap documents. It does not replace the canonical roadmap
documents under `docs/roadmaps/` and `docs/stage-2/`.

## Canonical Roadmap Documents

- [Overall Roadmap](docs/roadmaps/overall-roadmap.md): integrated long-range roadmap across
  existing roadmap documents.
- [Roadmaps Index](docs/roadmaps/README.md): index of roadmap documents under `docs/roadmaps/`.
- [Chronicle Daemon and API Roadmap](docs/roadmaps/chronicle-daemon-api-roadmap.md):
  planned local resident service, Chronicle-native API, agent-runtime integration, and
  Chronicle Cloud expansion path, while keeping Chronicle Stack out of cloud AI memory
  positioning.
- [Chronicle Yard Product Family Milestones](docs/roadmaps/chronicle-yard-product-family-milestones.md):
  milestone lane for Chronicle Yard as the umbrella over Chronicle Stack and related products
  such as CSG-RAG and chronicle-external-query.
- [Stage 2 Roadmap](docs/stage-2/roadmap.md): current Stage 2 implementation sequence.
- [Stage 2 Milestones](docs/stage-2/milestones.md): milestone-level execution map.
- [Release Operations](docs/releases/operations/README.md): release operation procedures and
  runbooks.

## Current Reading Order

1. Start with [README.md](README.md) for the repository map.
2. Read [Overall Roadmap](docs/roadmaps/overall-roadmap.md) for the integrated direction.
3. Read [Chronicle Daemon and API Roadmap](docs/roadmaps/chronicle-daemon-api-roadmap.md)
   before planning resident services, tool-facing APIs, Kazane/agent runtime integration, or
   Chronicle Cloud.
4. Read [Chronicle Yard Product Family Milestones](docs/roadmaps/chronicle-yard-product-family-milestones.md)
   before coordinating Chronicle Stack with CSG-RAG, chronicle-external-query, Chronicle Cloud,
   Chronicle API, or other Yard-family products.
5. Read [Stage 2 Roadmap](docs/stage-2/roadmap.md) for the active implementation lane.
6. Check [ADR Index](docs/adr/README.md) before changing architecture, storage, runtime,
   security, review, federation, or documentation governance.
7. Check [Chronicles](docs/chronicles/README.md) for task-specific maintenance history.

## Boundary

Roadmaps describe order, dependencies, non-goals, and re-evaluation points. They are not stable
interface contracts and should not be used to override specifications, ADRs, or tests.
