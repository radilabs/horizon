# Phase 2 Tasks — Provider Architecture and Local State

Phase contract: `PHASES.md` → **Phase 2 — Provider Architecture and Local State**

Phase 1 handoff must be PASS before this file is executed.

The purpose of this phase is to generalize only the architecture already proven by the working Codex implementation.

Do not design for hypothetical providers beyond what is necessary to support the next real provider.

---

# Execution Rules

1. Read `PROJECT.md`.
2. Read the Phase 2 contract in `PHASES.md`.
3. Read `docs/handoffs/phase-1.md`.
4. Read ADRs `0003` and `0004`.
5. Inspect the current collector and QML before changing architecture.
6. Work on tasks in order.
7. Work on only one task at a time.
8. Preserve observable Codex behavior unless a Phase 2 requirement explicitly changes it.
9. Do not implement Cursor or StepFun.
10. Do not implement periodic/background refresh.
11. Do not introduce a daemon.
12. Do not add settings or notifications.
13. Do not create abstractions without an immediate use.
14. Record out-of-scope discoveries under **Deferred Work**.
15. Create ADRs only for choices future work must respect.
16. Use `docs/` for factual schemas, procedures, cache behavior, interfaces, and operational knowledge.
17. Every task requires a deliverable, tests, and completion evidence.
18. Completing all tasks does not automatically complete Phase 2.
19. Phase completion requires the handoff validation task.
20. After successful handoff, STOP.

---

# Current Phase 1 Baseline

Phase 2 starts from these proven boundaries:

* Plasma invokes an external `ai-usage` collector.
* Collector is currently Python 3 stdlib.
* Existing command:

```bash
ai-usage status codex --json
```

* Codex authentication remains owned by Codex.
* Collector currently contains Codex auth, HTTP, normalization, and CLI dispatch in one file.
* QML currently hardcodes the `codex` provider command and several Codex-specific labels/error states.
* No persistent Horizon cache currently exists.

These are starting facts, not necessarily permanent implementation details.

The Phase 2 goal is to cleanly separate the pieces required for additional providers while keeping Codex working.

---

# P2-T1 — Define the Common Provider Contract

## Objective

Define the smallest provider interface required to support Codex now and another real provider later.

## Instructions

Inspect the current Codex collector implementation.

Identify the responsibilities already present:

* provider identity
* availability/auth detection
* usage retrieval
* normalization
* error reporting

Define a provider contract covering those responsibilities.

The design should allow the CLI dispatcher to select a provider without knowing its internal authentication or upstream API details.

Keep the interface simple.

A reasonable conceptual shape is:

```text
Provider
  id
  display_name
  detect()
  fetch_usage()
  normalize()
```

This is conceptual only.

Use Python structures appropriate to the current collector.

Do not create:

* dynamic plugin loading
* entry-point discovery
* dependency injection framework
* provider package registry
* abstract factories
* configuration DSL
* generic HTTP framework

If a simpler interface works, use it.

## Deliverable

Document the provider contract in:

`docs/provider-contract.md`

If the chosen provider architecture is a decision future implementations must respect, create an ADR.

## Test

Validate the proposed contract against the existing Codex implementation.

Confirm every current Codex responsibility has a clear home.

Confirm no interface method exists solely for a hypothetical provider requirement.

## Completion Evidence

Record:

* provider contract fields/methods
* Codex responsibilities mapped
* abstractions rejected as unnecessary
* ADR created or not required

## Status

* [x] Complete

---

# P2-T2 — Define the Normalized Usage Schema

## Objective

Turn the Phase 1 Codex JSON into an explicitly documented common provider output contract.

## Instructions

Define the normalized schema consumed by the Plasma UI.

Preserve existing useful Phase 1 fields where practical.

At minimum support:

* provider identifier
* display name
* plan/subscription label
* remaining percentage
* reset time
* status
* user-safe error information

Example:

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": "ChatGPT Plus",
  "remainingPercent": 94,
  "resetAt": "2026-08-17T12:00:00+02:00",
  "status": "ok"
}
```

Define valid status semantics for at least:

* `ok`
* provider unavailable
* authentication unavailable
* upstream error
* collector/internal error

Do not force every future provider to have fields that Codex does not prove necessary.

Optional fields are acceptable where actual provider behavior requires them.

The schema must contain no credentials or provider-specific raw API data.

## Deliverable

Create:

`docs/usage-schema.md`

Include:

* field definitions
* required vs optional fields
* status meanings
* sanitized success example
* sanitized failure example

## Test

1. Validate current Codex success output against the schema.
2. Validate current auth failure output.
3. Validate current upstream/collector failure output.
4. Confirm the existing QML can represent the required data.
5. Confirm no secret-bearing field exists.

## Completion Evidence

Record:

* schema version/shape
* Codex examples validated
* fields removed or changed from Phase 1
* compatibility result

## Status

* [x] Complete

---

# P2-T3 — Refactor Codex Into Provider Implementation

## Objective

Move Codex-specific behavior behind the common provider contract without changing Codex behavior.

## Instructions

Refactor the existing collector.

Separate:

* generic CLI dispatch
* provider selection
* Codex authentication
* Codex upstream usage retrieval
* Codex normalization

A reasonable repository shape may be:

```text
collector/
├── ai-usage
└── providers/
    ├── __init__.py
    └── codex.py
```

Use a different simple structure if more appropriate.

Preserve:

```bash
ai-usage status codex --json
```

Preserve the existing authentication security model.

Do not alter Codex credential ownership.

Do not introduce Horizon credential storage.

Do not add another real provider.

## Deliverable

Codex operating through the common provider architecture.

## Test

Run the same Phase 1 success/failure tests.

At minimum:

```bash
ai-usage status codex --json
```

Verify:

* exit code `0`
* valid normalized JSON
* live quota matches expected real usage
* reset information remains correct

Test missing auth using the existing safe method.

Verify:

* non-zero exit
* normalized failure
* no credential leak

Compare pre/post-refactor observable JSON behavior.

## Completion Evidence

Record:

* files moved/created
* command compatibility
* live Codex result
* failure result
* regressions found/fixed

## Status

* [x] Complete

---

# P2-T4 — Make CLI Provider Dispatch Generic

## Objective

Ensure the collector CLI can dispatch through the common provider interface rather than containing Codex-specific execution logic.

## Instructions

Update CLI handling so:

```bash
ai-usage status codex --json
```

selects the Codex provider through generic dispatch.

The dispatcher may use a small explicit registry/map.

Example concept:

```text
providers = {
    "codex": CodexProvider
}
```

That is sufficient.

Do not implement runtime plugin discovery.

Do not add Cursor placeholders pretending to be implementations.

Unknown providers should fail clearly.

## Deliverable

Generic provider dispatch behind the existing CLI.

## Test

### Existing provider

```bash
ai-usage status codex --json
```

Must still work.

### Unknown provider

Test an unsupported provider safely.

Verify:

* non-zero exit
* understandable error
* no traceback during normal invalid input
* no secrets

## Completion Evidence

Record:

* dispatch mechanism
* Codex test result
* unsupported-provider result

## Status

* [x] Complete

---

# P2-T5 — Remove Codex-Specific Knowledge From QML

## Objective

Make the Plasma UI consume normalized provider data without depending on Codex internals.

## Instructions

Inspect `main.qml`.

Remove unnecessary Codex-specific assumptions.

Currently these include concepts such as:

```text
status codex --json
Codex unavailable
Loading Codex usage…
```

The UI may still display "Codex" because that value comes from provider data.

The QML should care about:

* provider identity/display name
* normalized status
* normalized quota
* normalized reset information
* generic collector execution

It must not know:

* Codex endpoints
* Codex auth
* Codex file locations
* raw upstream response structure

For Phase 2, it is acceptable for the UI to request the single currently configured provider if that is the simplest path.

Do not create a multi-provider UI yet unless required by the Phase 2 contract.

## Deliverable

Provider-agnostic QML rendering for the current Codex provider.

## Test

1. Open Horizon.
2. Confirm real Codex data still renders.
3. Confirm provider name comes from normalized output.
4. Trigger a controlled provider/auth failure.
5. Confirm generic error UI works.
6. Confirm no Codex-specific upstream logic remains in QML.
7. Confirm manual refresh works.

## Completion Evidence

Record:

* Codex-specific UI assumptions removed
* real-data test
* error-state test
* refresh test

## Status

* [x] Complete

---

# P2-T6 — Define Cache Location and Format

## Objective

Define a safe local cache for the last successful normalized provider state.

## Instructions

Choose a standard user cache location.

Prefer an XDG cache location such as:

```text
~/.cache/horizon/
```

or the equivalent resolved through the environment.

Do not store cache inside the repository.

Do not store it alongside provider credentials.

The cache must contain only normalized non-secret provider data.

Define a cache envelope including at least:

* provider
* fetch timestamp
* normalized usage payload

Example:

```json
{
  "fetchedAt": "2026-08-10T20:30:00+02:00",
  "provider": "codex",
  "data": {
    "provider": "codex",
    "displayName": "Codex",
    "plan": "ChatGPT Plus",
    "remainingPercent": 94,
    "resetAt": "...",
    "status": "ok"
  }
}
```

Cache writes should be safe against partial writes where practical.

If the cache architecture creates a persistent convention future providers must respect, record an ADR.

## Deliverable

Document:

`docs/cache.md`

Include:

* cache location
* format
* write rules
* read rules
* security constraints
* invalid/corrupt cache handling

## Test

Validate that the proposed cache contains no auth/token material.

Validate expected XDG/cache path on the current machine.

## Completion Evidence

Record:

* chosen location
* format
* security review
* ADR if created

## Status

* [x] Complete

---

# P2-T7 — Implement Last-Successful-State Cache

## Objective

Persist the last successful normalized provider response.

## Instructions

After a successful provider retrieval:

1. normalize the response
2. return it normally
3. write the successful normalized state to cache

Do not cache failed provider responses as successful data.

The cache must:

* contain only normalized data
* never contain access tokens
* never contain refresh tokens
* never contain authorization headers
* never contain raw upstream responses
* tolerate missing cache directories
* tolerate corrupt existing cache safely

Use atomic replacement or another simple safe write method.

## Deliverable

Working local last-successful-state cache.

## Test

### Successful retrieval

Run:

```bash
ai-usage status codex --json
```

Verify:

* command succeeds
* cache file appears
* cache values match normalized output
* fetch timestamp exists

### Security

Inspect cache manually.

Confirm no credential material exists.

### Repeated write

Run multiple successful refreshes.

Verify cache updates cleanly.

### Corrupt cache

Temporarily create malformed cache data.

Verify the collector does not crash catastrophically.

Restore/refresh afterward.

## Completion Evidence

Record:

* cache path
* successful write result
* repeated-write result
* corrupt-cache behavior
* security check result

## Status

* [x] Complete

---

# P2-T8 — Implement Stale Cache Fallback

## Objective

Allow Horizon to show the last successful provider state when fresh retrieval fails.

## Instructions

When live provider retrieval fails:

* attempt to load the last successful cached state
* preserve information that the current retrieval failed
* clearly mark the returned/displayed result as stale

Do not silently convert stale data into `status=ok`.

The normalized response must expose enough information for the UI to distinguish:

* fresh success
* stale cached success after retrieval failure
* complete failure with no usable cache

A minimal extension might include fields such as:

```json
{
  "status": "stale",
  "stale": true,
  "fetchedAt": "...",
  "error": "Current refresh failed"
}
```

Use the smallest schema change that works.

Document the chosen semantics.

## Deliverable

Collector returns usable stale cache state on live failure.

## Test

1. Obtain a successful live result and cache it.
2. Trigger a controlled live retrieval failure.
3. Run the collector.
4. Confirm cached values are returned.
5. Confirm result is explicitly marked stale.
6. Confirm original fetch time is preserved.
7. Remove/disable cache.
8. Trigger failure again.
9. Confirm normal unavailable/error result occurs.

## Completion Evidence

Record:

* fresh result
* stale fallback result
* stale marker
* cache timestamp preservation
* no-cache failure behavior

## Status

* [x] Complete

---

# P2-T9 — Display Stale State in Plasma

## Objective

Make cached data visibly different from fresh data.

## Instructions

Update the Plasma UI to understand the normalized stale state.

When stale data is shown:

* quota information may remain visible
* provider/plan may remain visible
* stale state must be clearly indicated
* last successful update time should be shown where practical
* current refresh failure should not be hidden

Keep the UI simple.

Examples:

```text
Codex
ChatGPT Plus
94%
Cached — updated 18 min ago
Refresh failed
```

Do not add notification behavior.

Do not add background polling.

## Deliverable

Visible stale-cache state in Horizon.

## Test

### Fresh state

Retrieve normally.

Verify no stale indicator.

### Stale state

Create successful cache, then trigger live failure.

Open/refresh Horizon.

Verify:

* cached quota remains visible
* stale indication is obvious
* fresh and stale states cannot reasonably be confused

### No cache

Remove cache and trigger failure.

Verify normal unavailable/error state.

## Completion Evidence

Record:

* fresh UI behavior
* stale UI behavior
* no-cache failure behavior
* screenshot optional

## Status

* [x] Complete

---

# P2-T10 — Validate Manual Refresh Through Common Path

## Objective

Ensure the existing Refresh control uses the common provider + cache path.

## Instructions

Manual Refresh must perform a live retrieval attempt.

Its behavior should be:

### Success

* fetch live data
* normalize
* update cache
* show fresh data

### Failure with cache

* show cached data
* mark stale
* expose refresh failure

### Failure without cache

* show unavailable/error

Do not schedule automatic refresh.

## Deliverable

Manual Refresh operating entirely through the common collector path.

## Test

Test all three scenarios:

1. live success
2. failure with valid cache
3. failure without cache

Verify repeated clicks do not start overlapping QML collector executions if existing protection already prevents that.

Do not add a general concurrency system beyond what is needed.

## Completion Evidence

Record:

* success refresh
* stale fallback refresh
* no-cache failure
* overlapping-request behavior

## Status

* [x] Complete

---

# P2-T11 — Regression and Security Validation

## Objective

Verify the refactor did not break Phase 1 behavior or credential safety.

## Instructions

Repeat the meaningful Phase 1 tests against the new architecture.

At minimum validate:

* real Codex usage
* reset time
* auth reuse
* missing-auth handling
* collector JSON
* manual Plasma refresh
* popup behavior
* secret boundary

Review cache contents.

Review repository changes.

## Deliverable

Phase 2 regression evidence.

## Test

Run:

```bash
ai-usage status codex --json
```

Validate live output.

Test controlled auth/upstream failure.

Inspect:

```bash
git status
git diff
git diff --cached
```

Run the established secret audit from `docs/security.md`.

Inspect Horizon cache and confirm it contains only normalized non-secret data.

Open the real panel widget and confirm existing Codex behavior still works.

## Completion Evidence

Record:

* Codex regression result
* auth failure result
* refresh result
* cache security result
* repo secret audit result
* Plasma runtime result

## Status

* [x] Complete

---

# P2-T12 — Documentation Review

## Objective

Ensure Phase 2 architecture is understandable before another provider is implemented.

## Instructions

Review and update relevant documentation.

At minimum ensure these are current:

* `docs/provider-contract.md`
* `docs/usage-schema.md`
* `docs/cache.md`
* `docs/providers/codex.md`
* `docs/security.md`
* `docs/development.md`

Documentation must distinguish:

* provider interface
* normalized schema
* provider-specific implementation
* credential ownership
* cache ownership
* UI boundary

Do not document Cursor implementation.

Phase 3 may use these contracts later.

## Deliverable

Current Phase 2 architecture documentation.

## Test

From repository documentation alone, verify another agent can answer:

1. How is a provider selected?
2. What must a provider return?
3. Where does provider-specific HTTP/auth live?
4. What does QML consume?
5. Where is cache stored?
6. What is cached?
7. What happens when live retrieval fails?
8. Where do credentials remain?

If these cannot be answered clearly, documentation is incomplete.

## Completion Evidence

Record:

* docs reviewed
* corrections made
* unanswered architecture questions, if any

## Status

* [x] Complete

---

# P2-T13 — Phase 2 Handoff Validation

## Objective

Determine whether Phase 2 satisfies its immutable contract.

This task adds no new functionality.

## Instructions

Read the Phase 2 contract in `PHASES.md`.

Validate every acceptance criterion individually.

Create:

`docs/handoffs/phase-2.md`

The report must include:

## Deliverables

Meaningful files and artifacts.

## Provider Architecture

Describe:

* common provider contract
* current registered providers
* collector dispatch mechanism
* QML boundary

## Normalized Schema

Reference the documented common schema.

## Cache Behavior

Record:

* cache path
* successful cache behavior
* stale fallback behavior
* corrupt/missing cache behavior

## Tests Performed

List actual tests.

## Acceptance Results

Record PASS/FAIL for every Phase 2 acceptance criterion.

## Regression Results

Confirm existing Codex behavior remains intact.

## Security Validation

Confirm:

* provider credentials remain outside Horizon
* cache contains no credentials
* no new secret-bearing state exists
* repository audit passes

## Decisions

Reference ADRs created during Phase 2.

## Deferred Work

Reference out-of-scope discoveries.

## Test

Compare the running implementation against every Phase 2 acceptance criterion.

If any criterion fails:

* Phase 2 remains active
* record the failure
* create/refine a Phase 2 task
* do not weaken the phase contract

## Completion Evidence

`PHASE 2 HANDOFF: PASS`

Report: `docs/handoffs/phase-2.md`

## Status

* [x] Complete

---

# Deferred Work

Record work discovered outside Phase 2.

Do not implement it.

Format:

```text
- [date] Short description
  - Discovered while: P2-Tx
  - Suggested phase: Phase X / Future
  - Reason deferred: outside Phase 2 contract
```

Likely examples:

* Cursor provider → Phase 3
* StepFun provider → Phase 4
* periodic refresh → Phase 5
* notifications → Phase 5
* settings/provider enable-disable → Phase 5
* installer/package improvements → Phase 5 unless immediately required

- [2026-08-10] Cursor provider implementation
  - Discovered while: P2-T1
  - Suggested phase: Phase 3
  - Reason deferred: outside Phase 2 contract

- [2026-08-10] Multi-provider UI / enable-disable
  - Discovered while: P2-T5
  - Suggested phase: Phase 5
  - Reason deferred: outside Phase 2 contract

- [2026-08-10] Periodic refresh / notifications
  - Discovered while: P2-T10
  - Suggested phase: Phase 5
  - Reason deferred: outside Phase 2 contract

---

# STOP CONDITION

When `P2-T13` passes:

**STOP.**

Do not:

* start Cursor
* create Phase 3 implementation tasks
* add StepFun
* add periodic refresh
* add notifications
* build runtime plugin discovery
* build a provider marketplace
* turn the collector into a daemon
* redesign Horizon around hypothetical future providers

Phase 3 requires a new explicit execution instruction.
