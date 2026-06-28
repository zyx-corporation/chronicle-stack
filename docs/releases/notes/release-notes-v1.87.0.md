# Release Notes v1.87.0

## Added

- `chronicle ai-boundary preview` for preview-only external AI boundary checks, context minimization review, and opt-in persistence policy capture
- `chronicle rde draft` for AI-assisted diff memo preparation with optional linked RDE recording and hypothesis-object persistence
- runtime-record visibility for recorded AI boundary previews through the local read-only UI

## Boundary

- AI boundary preview remains local, read-only, and advisory before any external handoff
- Sayane / AI adapter integration stays contract-first; Chronicle Stack core does not add fixed provider wiring or hosted runtime behavior
