# Stage 2 / Phase 7 — Provider Information Contract

**Status:** AUTHORIZED — not started  
**Authority:** `PHASES.md` Stage 2 / Phase 7, `TASKS.md`  
**Previous accepted snapshot:** `docs/handoffs/phase-6.5.md`

## Goal

Establish and verify the minimal provider-neutral information contract for the four existing providers. Preserve operational behavior; prepare a sound contract for Phase 8 UI redesign.

## Execution Tasks

- [ ] Inspect current usage schema, cache behavior, QML bindings and four collectors; record sanitized evidence and semantics for existing meters and states.
- [ ] Draft the smallest necessary provider/meter schema and explicit old-to-new compatibility strategy. Use Claude's multiple windows as mandatory evidence. Record only durable decisions.
- [ ] Implement any **necessary** contract/normalization/adapter changes without changing existing visible UI or authentication flows.
- [ ] Add deterministic fixtures/tests for each provider, multiple windows, unavailable/auth/error/stale outputs and compatibility with existing consumers.
- [ ] Run relevant automated tests, provider isolation checks and secret audit; record direct evidence.
- [ ] Independent Watcher evaluation against Phase 7 acceptance criteria; fix in-scope findings and rerun if needed.
- [ ] Present verification and any deferred work for owner review. **STOP pending owner acceptance.**

## Boundaries

No provider additions, authentication changes, UI redesign, invented account hierarchy, generalized plugin framework, or work from Phases 8–9. Future balance/spend/rate-limit designs are exploratory notes only unless directly supported by current provider data.

## Evidence and Handoff

Record changed files, test commands and results, contract examples (sanitized), compatibility evidence, risks, Watcher report location and owner decision here as execution proceeds. This task is **not accepted** merely because implementation or Watcher review finishes.

After explicit owner acceptance only: create `docs/handoffs/phase-7.md`, checkpoint, then STOP.
