# Phase 3 Tasks — Cursor

Phase contract: `PHASES.md` → **Phase 3 — Cursor**

Phase 2 handoff must be PASS before this file is executed.

The purpose of this phase is to prove that the provider architecture created in Phase 2 works with a second real provider.

Do not redesign the provider system unless actual Cursor behavior makes the existing contract insufficient.

---

# Execution Rules

1. Read `PROJECT.md`.
2. Read the Phase 3 contract in `PHASES.md`.
3. Read `docs/handoffs/phase-2.md`.
4. Read:

   * `docs/provider-contract.md`
   * `docs/usage-schema.md`
   * `docs/cache.md`
   * `docs/security.md`
5. Read relevant Phase 2 ADRs.
6. Inspect the current provider registry, Codex provider, cache, and QML before changing code.
7. Work on tasks in order.
8. Work on only one task at a time.
9. Preserve working Codex behavior.
10. Reuse the Phase 2 provider contract wherever possible.
11. Do not implement StepFun.
12. Do not implement notifications.
13. Do not add settings UI.
14. Do not implement periodic/background refresh.
15. Do not create a Cursor login flow.
16. Do not modify Cursor credentials.
17. Horizon must not own or persist Cursor credentials.
18. Record out-of-scope discoveries under **Deferred Work**.
19. Create ADRs only when future work must respect a real choice, constraint, rejection, or tradeoff.
20. Every task requires a deliverable, tests, and completion evidence.
21. Completing all tasks does not automatically complete Phase 3.
22. Phase completion requires the handoff validation task.
23. After successful handoff, STOP.

---

# Security Boundary

Cursor authentication remains owned by Cursor.

Horizon may:

* discover existing Cursor authentication/session state
* read it transiently where required
* use existing local/internal Cursor mechanisms
* cache normalized non-secret usage data

Horizon must not:

* create Cursor credentials
* copy Cursor credentials into Horizon-owned storage
* commit Cursor session files
* persist Cursor cookies/tokens
* print Cursor secrets to stdout
* print Cursor secrets to logs
* include Cursor secrets in docs or task evidence
* modify Cursor authentication state unless unavoidable and explicitly approved

If Horizon appears to require its own Cursor authentication store or login mechanism:

**STOP implementation and create an ADR.**

Do not quietly solve authentication by inventing a new subsystem.

---

# P3-T0 — Revalidate Credential Safety Before Cursor Discovery

## Objective

Ensure existing repository protections are sufficient before inspecting Cursor authentication.

## Instructions

Review:

* `.gitignore`
* `docs/security.md`
* current cache behavior
* repository status

Determine likely Cursor credential/session file names and locations only enough to ensure they cannot accidentally enter Git.

Add ignore rules only where needed.

Do not broadly ignore useful source/config files without reason.

## Deliverable

Updated credential safety rules if required.

## Test

Run:

```bash
git status
git diff
git diff --cached
```

Run the existing repository secret audit.

Inspect suspicious matches manually.

Confirm no Cursor credential/session artifact is currently tracked.

## Completion Evidence

Record:

* protections reviewed
* rules added, if any
* secret audit result
* tracked credential check result

Never record secret values.

## Status

* [x] Complete

---

# P3-T1 — Discover Existing Cursor Authentication

## Objective

Determine how the user's existing Cursor installation/account is authenticated and how Horizon can safely reuse that state.

## Instructions

Inspect the locally installed Cursor application and user state.

Determine:

* Cursor version
* relevant local configuration/state locations
* authentication/session storage mechanism
* whether authentication is stored in:

  * local database
  * JSON/config file
  * cookies
  * OS keyring
  * browser/session state
  * another mechanism
* whether there is an existing local command/interface that exposes account state
* what information is necessary for usage retrieval
* what must never be copied or persisted

Inspect structure and metadata without dumping secret values.

If Cursor uses a SQLite database or similar local state store, inspect schema/field names safely rather than printing credential content.

Do not modify Cursor authentication.

Do not log out/re-login unless genuinely required and approved.

## Deliverable

Create:

`docs/providers/cursor.md`

Document:

* Cursor version
* auth/session mechanism
* relevant local paths
* credential/session backend
* proposed safe reuse method
* security constraints
* unknowns

If a choice future work must respect is discovered, create an ADR.

## Test

1. Confirm Cursor is currently authenticated.
2. Confirm identified local auth/session state exists.
3. Confirm proposed Horizon access does not require copying credentials.
4. Confirm no Cursor state was modified.
5. Run secret audit again.

## Completion Evidence

Record:

* Cursor version
* auth mechanism identified
* storage/backend identified
* proposed reuse method
* ADR if required
* security check result

## Status

* [x] Complete

---

# P3-T2 — Discover Cursor Usage / Quota Mechanism

## Objective

Determine how to retrieve real usage/limit information for the authenticated individual Cursor account.

## Instructions

Investigate:

* local Cursor application behavior
* relevant local/internal endpoints
* network mechanisms where safely observable
* existing open-source Cursor quota trackers
* known implementations that reuse local Cursor authentication

Determine:

* usage endpoint/mechanism
* request method
* required auth context
* required non-secret headers
* account/plan information available
* quota fields
* reset or billing-cycle information
* model-specific limits if present
* error behavior
* whether usage is request-based, credit-based, percentage-based, or another unit

Do not force Cursor data into the existing schema prematurely.

First understand the actual upstream semantics.

Do not connect it to Plasma yet.

## Deliverable

Extend:

`docs/providers/cursor.md`

Document:

* usage mechanism
* endpoint or local mechanism
* sanitized request shape
* sanitized response example
* available limit semantics
* reset semantics
* plan information
* known unofficial/internal fragility

## Test

1. Perform a real authenticated Cursor usage query.
2. Confirm it corresponds to the currently authenticated account.
3. Confirm meaningful usage/limit information is present.
4. Repeat to verify reproducibility.
5. Confirm no credentials are persisted by Horizon.
6. Run secret audit.

If no usable mechanism exists, record the result and mark the task FAIL rather than inventing data.

## Completion Evidence

Record:

* mechanism found
* fields retrieved
* quota semantics
* reset/billing-cycle availability
* reproducibility
* security check

## Status

* [x] Complete

---

# P3-T3 — Map Cursor Data to the Existing Usage Schema

## Objective

Determine whether real Cursor data fits the Phase 2 normalized provider schema.

## Instructions

Map actual Cursor usage into:

`docs/usage-schema.md`

Use existing fields wherever they honestly represent Cursor semantics.

Do not lie to make the schema fit.

For example, only populate:

`remainingPercent`

if a meaningful percentage can actually be calculated from available Cursor limits.

If Cursor exposes a different but necessary concept, determine whether a minimal optional schema extension is required.

Any shared-schema change must:

1. be required by actual Cursor data
2. preserve Codex compatibility
3. be documented
4. be justified in an ADR if future providers/UI must respect it

Do not redesign the schema around speculative StepFun requirements.

## Deliverable

A documented Cursor → normalized schema mapping in:

`docs/providers/cursor.md`

Update `docs/usage-schema.md` only if genuinely required.

Create an ADR only if the shared contract changes materially.

## Test

Using a real sanitized Cursor response:

1. Produce a valid normalized payload.
2. Validate it against the existing schema.
3. Confirm required UI fields can be represented honestly.
4. Confirm no provider-specific raw response leaks into normalized output.
5. Confirm no secret material exists.

## Completion Evidence

Record:

* mapping result
* schema changes, if any
* fields intentionally omitted
* ADR if required

## Status

* [x] Complete

---

# P3-T4 — Implement Cursor Provider

## Objective

Implement Cursor behind the existing Phase 2 provider contract.

## Instructions

Create a Cursor provider alongside Codex.

Expected repository shape:

```text
collector/
└── providers/
    ├── codex.py
    └── cursor.py
```

Cursor provider must implement the existing responsibilities:

* `id`
* `display_name`
* `detect()`
* `fetch_usage()`
* normalization
* `ProviderError` semantics

Keep Cursor-specific:

* authentication handling
* local state parsing
* endpoint knowledge
* upstream response parsing

inside the Cursor provider or helpers owned by it.

Do not put Cursor-specific logic in the generic CLI dispatcher.

Do not modify Codex provider unless Cursor proves a shared contract defect.

## Deliverable

`collector/providers/cursor.py`

or an equivalently simple implementation.

## Test

Run provider-specific tests directly or through CLI plumbing as appropriate.

Verify:

* authenticated Cursor state is detected
* real usage is retrieved
* normalized payload is valid
* missing auth gives appropriate `ProviderError`
* upstream failure gives appropriate error
* no secrets appear

## Completion Evidence

Record:

* implementation files
* live result
* auth failure result
* upstream failure result
* security result

## Status

* [x] Complete

---

# P3-T5 — Register Cursor in the Collector

## Objective

Expose Cursor through the existing generic `ai-usage` CLI.

## Instructions

Add Cursor to the explicit provider registry.

Expected commands:

```bash
ai-usage status codex --json
ai-usage status cursor --json
```

Do not create dynamic plugin discovery.

Do not special-case Cursor throughout the CLI unless a provider-specific option is unavoidable.

If provider-specific arguments are required, keep the generic CLI as clean as practical.

## Deliverable

Cursor registered in the Phase 2 provider registry.

## Test

### Cursor

```bash
ai-usage status cursor --json
```

Verify:

* exit `0` on success
* valid normalized JSON
* real Cursor usage data

### Codex regression

```bash
ai-usage status codex --json
```

Verify unchanged behavior.

### Unknown provider

Confirm existing unknown-provider behavior still works.

## Completion Evidence

Record:

* registry change
* Cursor CLI result
* Codex CLI result
* unknown-provider result

## Status

* [x] Complete

---

# P3-T6 — Validate Cursor Cache and Stale Fallback

## Objective

Ensure Cursor automatically benefits from the Phase 2 cache architecture without introducing provider-specific cache behavior.

## Instructions

Use the existing XDG last-successful cache mechanism.

Expected Cursor cache shape/location should follow existing provider rules, e.g.:

```text
~/.cache/horizon/usage-cursor.json
```

Do not add Cursor-specific credential material to cache.

Do not create separate cache architecture.

## Deliverable

Cursor participates in the existing last-success/stale flow.

## Test

### Fresh result

Run:

```bash
ai-usage status cursor --json
```

Verify cache is written.

### Cache contents

Inspect the cache.

Confirm only normalized non-secret data exists.

### Stale fallback

1. obtain valid cache
2. safely cause live Cursor retrieval to fail
3. run collector
4. verify `status=stale`
5. verify cached values are preserved
6. verify `fetchedAt` is preserved

### No-cache failure

Test failure without usable cache.

Verify normal error result.

## Completion Evidence

Record:

* cache path
* fresh write result
* stale result
* no-cache result
* cache security result

## Status

* [x] Complete

---

# P3-T7 — Introduce Minimal Multi-Provider Collector Execution in QML

## Objective

Allow Horizon to retrieve both Codex and Cursor independently.

## Instructions

The current UI requests one configured provider.

Phase 3 requires both Codex and Cursor to appear together.

Update the QML execution model only as much as required to run both provider commands independently.

Expected commands:

```text
ai-usage status codex --json
ai-usage status cursor --json
```

Each provider must have independent state.

A Cursor failure must not overwrite or invalidate Codex state.

A Codex failure must not prevent Cursor from rendering.

Do not introduce:

* settings-driven provider selection
* dynamic provider discovery
* arbitrary provider configuration
* background refresh scheduler

A simple explicit Phase 3 list of:

```text
codex
cursor
```

is acceptable.

## Deliverable

QML can retrieve and hold independent normalized state for Codex and Cursor.

## Test

1. Both providers succeed.
2. Codex succeeds / Cursor fails.
3. Cursor succeeds / Codex fails.
4. Both fail.
5. Stale Cursor + fresh Codex.
6. Stale Codex + fresh Cursor.

Confirm states do not overwrite one another.

## Completion Evidence

Record:

* execution approach
* isolation tests
* stale/fresh combinations tested

## Status

* [x] Complete

---

# P3-T8 — Display Cursor Alongside Codex

## Objective

Display both providers in the Horizon popup.

## Instructions

Render provider information from normalized payloads.

Each provider section/card must independently support:

* display name
* plan if available
* remaining quota where available
* progress indicator where meaningful
* reset information where available
* stale state
* error/unavailable state

Do not hard-code Cursor upstream semantics into generic UI code.

Keep the design simple.

This phase requires coexistence, not visual polish.

Do not add settings or provider ordering controls.

## Deliverable

Horizon popup visibly displays both:

* Codex
* Cursor

## Test

### Both successful

Confirm both appear correctly.

### Cursor unavailable

Confirm:

* Codex remains visible and functional
* Cursor shows its own error state

### Codex unavailable

Confirm Cursor remains visible and functional.

### Stale state

Confirm stale indication is isolated to the affected provider.

## Completion Evidence

Record:

* both-success result
* Cursor-failure isolation result
* Codex-failure isolation result
* stale-state result

## Status

* [x] Complete

---

# P3-T9 — Manual Refresh for Both Providers

## Objective

Ensure manual refresh updates both providers without coupling their success/failure states.

## Instructions

The existing Refresh control may:

* refresh all displayed providers

or

* use another equally simple Phase 3 interaction

Do not build settings around refresh behavior.

Do not add periodic refresh.

Ensure one provider failing does not prevent results from another provider being applied.

Avoid overlapping duplicate requests where practical using the existing simple loading protections.

## Deliverable

Working manual multi-provider refresh.

## Test

Test:

1. both providers succeed
2. Cursor fails, Codex succeeds
3. Codex fails, Cursor succeeds
4. stale fallback for one provider
5. repeated Refresh interaction

Confirm usable provider results still render.

## Completion Evidence

Record:

* refresh behavior
* partial failure behavior
* repeated-click behavior

## Status

* [x] Complete

---

# P3-T10 — Cursor Failure and Recovery Validation

## Objective

Prove Cursor failure does not damage the rest of Horizon.

## Instructions

Test at minimum:

* Cursor authentication unavailable
* Cursor upstream failure
* malformed Cursor response
* stale fallback
* recovery after failure

Do not destroy real Cursor authentication to test failure.

Use safe overrides, fixture-like local methods, or controlled failure mechanisms.

## Deliverable

Verified independent Cursor failure handling.

## Test

For every failure scenario verify:

* collector produces safe normalized error/stale data
* no secrets appear
* QML remains functional
* Codex remains functional
* Cursor recovers after normal conditions return

## Completion Evidence

Record:

* scenarios tested
* Cursor behavior
* Codex behavior during Cursor failure
* recovery result
* secret check

## Status

* [x] Complete

---

# P3-T11 — Codex Regression Validation

## Objective

Confirm introducing a second provider did not regress the proven Codex path.

## Instructions

Repeat key Codex tests from Phase 2.

Verify:

* live usage
* cache
* stale fallback
* manual refresh
* auth handling
* UI rendering
* security boundary

Do not "fix" unrelated Codex behavior unless Phase 3 caused the regression.

## Deliverable

Codex regression evidence.

## Test

At minimum:

```bash
ai-usage status codex --json
```

plus:

* controlled failure
* stale fallback
* widget display
* multi-provider refresh

## Completion Evidence

Record:

* live result
* failure result
* stale result
* UI result
* regression PASS/FAIL

## Status

* [x] Complete

---

# P3-T12 — Documentation and Secret Audit

## Objective

Ensure Cursor integration is reproducible and no credentials leaked during discovery or implementation.

## Instructions

Review:

* `docs/providers/cursor.md`
* `docs/provider-contract.md`
* `docs/usage-schema.md`
* `docs/cache.md`
* `docs/security.md`
* Phase 3 ADRs
* task evidence
* source changes
* cache contents

Documentation must explain:

* Cursor auth/session mechanism
* usage retrieval mechanism
* normalized mapping
* cache behavior
* failure behavior
* security constraints
* upstream fragility

Run the established repository secret audit.

Also inspect for Cursor-specific session/cookie/token artifacts.

Do not include matched values in evidence.

## Deliverable

Complete Cursor provider documentation and clean repository state.

## Test

1. Follow documented Cursor collector procedure.
2. Retrieve real Cursor usage.
3. Run repository secret scans.
4. Inspect `git status`.
5. Inspect `git diff`.
6. Inspect staged changes.
7. Inspect Cursor cache.
8. Confirm no credential/session files are tracked.
9. Confirm docs contain only sanitized examples.

## Completion Evidence

Record:

* docs validated
* secret audit PASS/FAIL
* suspicious matches reviewed
* credential artifact check
* fixes made

## Status

* [x] Complete

---

# P3-T13 — Phase 3 Handoff Validation

## Objective

Determine whether Phase 3 satisfies its immutable contract.

This task adds no new functionality.

## Instructions

Read the Phase 3 contract in `PHASES.md` again.

Validate every acceptance criterion individually.

Create:

`docs/handoffs/phase-3.md`

The report must include:

## Deliverables

List meaningful files and artifacts.

## Cursor Discovery

Describe:

* auth/session source
* usage mechanism
* limitations
* credential ownership

## Provider Integration

Describe:

* registry entry
* normalized schema mapping
* cache integration

## Multi-Provider UI

Confirm:

* Codex appears
* Cursor appears
* states are independent

## Tests Performed

List actual runtime tests.

## Acceptance Results

Record PASS/FAIL for every Phase 3 acceptance criterion:

1. Horizon detects usable Cursor authentication where present.
2. Real Cursor usage information can be retrieved.
3. Cursor data is normalized through the common provider model.
4. Horizon does not expose or persist Cursor secrets.
5. Cursor failure does not prevent Codex from working.
6. Both Codex and Cursor appear correctly in the widget.
7. Cursor provider discovery is documented.

## Required Handoff Tests

Explicitly document tests for:

* Cursor success
* Cursor auth failure
* Cursor upstream failure
* Codex during Cursor failure

These are required by the Phase 3 handoff contract.

## Security Validation

Confirm:

* Cursor credentials remain owned by Cursor
* Horizon stores no Cursor credentials
* cache contains normalized data only
* no Cursor secret/session artifact is committed
* repository secret audit passes

## Decisions

Reference any ADR created in Phase 3.

If the shared provider contract changed, explain why and reference the required decision record.

## Deferred Work

Reference all out-of-scope discoveries.

## Test

Compare implementation and evidence against every Phase 3 acceptance criterion.

If any criterion fails:

* Phase 3 remains active
* record the failure
* create/refine a Phase 3 task
* do not weaken or modify the contract

## Completion Evidence

Record exactly one:

`PHASE 3 HANDOFF: PASS`

or

`PHASE 3 HANDOFF: FAIL`

## Status

* [x] Complete

---

# Deferred Work

Record work discovered outside Phase 3.

Do not implement it.

```text
- [2026-08-10] StepFun provider
  - Discovered while: Phase 3 exclusions
  - Suggested phase: Phase 4
  - Reason deferred: outside Phase 3 contract

- [2026-08-10] Provider enable/disable settings / ordering UI
  - Discovered while: P3-T7
  - Suggested phase: Phase 5
  - Reason deferred: no settings UI in Phase 3

- [2026-08-10] Periodic/background refresh and notifications
  - Discovered while: P3-T9
  - Suggested phase: Phase 5
  - Reason deferred: explicit Phase 3 exclusions

- [2026-08-10] In-memory Cursor token refresh without writing state.vscdb
  - Discovered while: P3-T1
  - Suggested phase: Future
  - Reason deferred: not required while access token valid; must not mutate Cursor credentials

- [2026-08-10] Model-specific Cursor sub-limit breakdown in UI
  - Discovered while: P3-T2
  - Suggested phase: Phase 5 / Future
  - Reason deferred: remainingPercent sufficient for Phase 3
```

---

# STOP CONDITION

When `P3-T13` passes:

**STOP.**

Do not:

* start StepFun
* create Phase 4 implementation tasks
* add provider settings
* add dynamic provider discovery
* add periodic refresh
* add notifications
* redesign the provider architecture without a proven need
* introduce Horizon-owned Cursor authentication

Phase 4 requires a new explicit execution instruction.
