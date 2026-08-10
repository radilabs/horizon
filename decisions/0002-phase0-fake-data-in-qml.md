# ADR-0002: Phase 0 fake usage lives in QML properties

## Status

Accepted

## Context

Phase 0 needs a Codex-shaped UI without collectors, networking, or provider architecture (those belong to later phases).

## Decision

- Represent fake Codex state as simple properties on the root `PlasmoidItem` in `plasmoid/contents/ui/main.qml` (`providerName`, `planName`, `remainingPercent`, `resetText`).
- Do not introduce an external collector, JSON files, or a provider abstraction in Phase 0.
- Refresh is a local UI action only (`refreshFakeData()`), not a data fetch.

## Consequences

- Phase 1 can replace these properties with real collector-backed values without requiring a Phase 0 provider framework.
- Phase 2 owns the reusable provider interface; Phase 0 intentionally avoids that abstraction.
