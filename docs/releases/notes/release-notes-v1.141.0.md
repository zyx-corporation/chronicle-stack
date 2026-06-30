# Release Notes v1.141.0

- added dedicated `Federation Workspace` route renderers for `Federation Inbox` and `Federation Outbox` so message route, preview-only state, audit state, and related Chronicle links can be reviewed without falling back to generic tables
- exposed shared `federation_summary` aggregates on inbox and outbox route payloads to support the new workspace summary rail
- updated operator-facing docs so Federation Workspace route validation is part of manual local UI checks
