# Horizon — Phase Contracts

These phases define immutable execution boundaries.

Tasks inside a phase may be refined as implementation progresses, but the phase goal, scope, exclusions, acceptance criteria, and handoff contract must not be changed during implementation.

Work discovered outside the active phase is recorded as deferred work and is not implemented.

A completed task does not mean a completed phase.

The agent must stop after satisfying the active phase handoff contract. It must never begin the next phase automatically.

---

# Phase 0 — Plasma Skeleton

## Goal

Create the smallest working KDE Plasma widget and establish the local development, installation, reload, and debugging workflow.

## Entry Conditions

* Repository structure exists.
* KDE Plasma development environment is available.
* No implementation from later phases is required.

## Scope

* Create valid plasmoid structure.
* Create metadata.
* Create minimal QML UI.
* Support compact panel representation.
* Support popup/full representation.
* Install widget locally.
* Document local install/reload/debug workflow.
* Add a small fake Codex usage display using hardcoded data.

The fake display should be sufficient to prove the intended basic UI structure:

* provider name
* plan name
* remaining percentage
* progress indicator
* reset time
* refresh control

## Explicit Exclusions

* Real Codex API access.
* Authentication handling.
* Cursor support.
* StepFun support.
* Provider abstraction layer.
* External collector.
* Caching.
* Background refresh.
* Notifications.
* Settings UI.
* Auto-detection.

## Acceptance Criteria

1. Horizon can be installed as a local Plasma widget.
2. Horizon can be added to a Plasma panel.
3. Compact representation renders correctly.
4. Clicking the widget opens its full representation.
5. The full representation displays fake Codex usage data.
6. Editing the widget and reloading Plasma produces visible changes.
7. The local development workflow is documented.
8. No real provider credentials or network calls exist.

## Handoff Contract

Before Phase 0 can be declared complete:

* All acceptance criteria must be demonstrated.
* Installation and reload instructions must be documented.
* Files changed must be recorded.
* Tests performed and their results must be recorded.
* Known limitations must be recorded.
* Deferred discoveries must be recorded.
* Any architectural decision that later work must respect must be recorded under `decisions/`.

Then STOP.

Do not begin Phase 1.

---

# Phase 1 — Real Codex Usage

## Goal

Replace fake Codex usage data with real quota information from the user's existing ChatGPT Plus / Codex authentication.

## Entry Conditions

* Phase 0 handoff contract is satisfied.
* Working Plasma widget exists.
* Fake Codex UI exists.

## Scope

* Investigate existing local Codex authentication.
* Investigate existing open-source Codex quota trackers where useful.
* Identify the source of quota and reset information.
* Document the discovered authentication and quota mechanism.
* Introduce a minimal external data collector.
* Implement Codex usage retrieval.
* Normalize Codex information into Horizon's internal data format.
* Connect real Codex data to the plasmoid.
* Handle unavailable or expired authentication.

Expected command shape:

`ai-usage status codex --json`

The exact implementation language is not fixed by this phase.

## Explicit Exclusions

* Implementing a new login flow.
* Storing copied user credentials.
* Cursor support.
* StepFun support.
* General provider plugin architecture.
* Background daemon.
* Periodic refresh.
* Notifications.
* Settings UI.
* Broad refactoring of Phase 0.

## Acceptance Criteria

1. The collector can retrieve real Codex usage information.
2. `ai-usage status codex --json` returns normalized machine-readable output.
3. Horizon does not print or persist authentication secrets.
4. Existing local authentication is reused.
5. Logged-out or unavailable authentication produces a clear error.
6. The plasmoid displays real Codex remaining usage.
7. The plasmoid displays the relevant reset time where available.
8. Provider discovery notes contain the auth source, endpoint/mechanism, required fields, and sanitized example response.
9. Phase 0 functionality still works.

## Handoff Contract

Before Phase 1 can be declared complete:

* Real Codex quota information must be visible in the Plasma widget.
* All acceptance criteria must pass.
* Tests and results must be recorded.
* Provider discovery documentation must be complete enough for another agent to understand the mechanism.
* Known upstream/API fragility must be recorded.
* Deferred work must be recorded.
* Architectural decisions affecting later providers must be recorded.

Then STOP.

Do not begin Phase 2.

---

# Phase 2 — Provider Architecture and Local State

## Goal

Turn the working Codex implementation into a small reusable provider architecture suitable for additional providers without changing observable Codex behavior.

## Entry Conditions

* Phase 1 handoff contract is satisfied.
* Real Codex usage works end-to-end.

## Scope

Define a common provider interface covering, at minimum:

* provider identity
* availability/detection
* usage retrieval
* normalization
* error state

Introduce a common normalized usage model.

Introduce local caching of the last successful provider state.

Allow the UI to represent:

* current result
* stale cached result
* provider unavailable
* authentication unavailable
* upstream error

Add manual refresh through the common collector path.

## Explicit Exclusions

* Cursor implementation.
* StepFun implementation.
* Automatic periodic refresh.
* Long-running daemon.
* Notifications.
* Settings UI.
* Provider auto-configuration beyond what is required for the architecture.
* Premature abstraction for unknown future providers.

## Acceptance Criteria

1. Codex operates through the common provider interface.
2. Provider-specific upstream data does not leak into the QML UI.
3. Normalized provider output has a documented schema.
4. Last successful state is cached locally.
5. Cached data can be displayed when fresh retrieval fails.
6. Cached data clearly indicates that it is stale.
7. Manual refresh still works.
8. Existing Codex behavior does not regress.

## Handoff Contract

Before Phase 2 can be declared complete:

* Codex must work entirely through the common provider path.
* Cache behavior must be tested for success and failure cases.
* The normalized provider contract must be documented.
* Architecture decisions must be recorded.
* Any abstractions added must have an immediate use in the existing codebase.
* Deferred work must be recorded.

Then STOP.

Do not begin Phase 3.

---

# Phase 3 — Cursor

## Goal

Add real usage information for the user's individual Cursor account using the provider architecture established in Phase 2.

## Entry Conditions

* Phase 2 handoff contract is satisfied.
* Provider interface and normalization model are stable enough for a second provider.

## Scope

* Investigate existing Cursor local authentication/session state.
* Investigate relevant local/internal Cursor usage endpoints.
* Review existing open-source Cursor quota trackers where useful.
* Document the discovered mechanism.
* Implement Cursor provider detection.
* Implement Cursor usage retrieval.
* Normalize Cursor limits into the common model.
* Display Cursor alongside Codex in Horizon.
* Handle unavailable or expired Cursor authentication.

## Explicit Exclusions

* Implementing a Cursor login flow.
* Modifying Cursor credentials.
* StepFun support.
* Notifications.
* Settings UI.
* General redesign of provider architecture unless required to represent actual Cursor data.

## Acceptance Criteria

1. Horizon detects usable Cursor authentication where present.
2. Real Cursor usage information can be retrieved.
3. Cursor data is normalized through the common provider model.
4. Horizon does not expose or persist Cursor secrets.
5. Cursor failure does not prevent Codex from working.
6. Both Codex and Cursor appear correctly in the widget.
7. Cursor provider discovery is documented.

## Handoff Contract

Before Phase 3 can be declared complete:

* Codex and Cursor must both work independently.
* Cursor success, auth failure, and upstream failure must be tested.
* Provider documentation must describe the discovered mechanism.
* Any changes to the shared provider contract must be justified and recorded.
* Deferred work must be recorded.

Then STOP.

Do not begin Phase 4.

---

# Phase 4 — StepFun Step Plan

## Goal

Add real StepFun Step Plan credit/usage information using the existing provider architecture.

## Entry Conditions

* Phase 3 handoff contract is satisfied.
* Codex and Cursor work through the common provider model.

## Scope

* Investigate StepFun dashboard/session authentication.
* Identify relevant usage/credit endpoints.
* Review existing implementations where useful.
* Document the discovered mechanism.
* Implement StepFun provider detection.
* Implement usage/credit retrieval.
* Normalize StepFun data into the common model.
* Display StepFun alongside existing providers.
* Handle unavailable or expired StepFun authentication.

## Explicit Exclusions

* Implementing a StepFun login flow.
* General billing management.
* Purchasing or changing subscription plans.
* Notifications.
* Settings UI.
* Redesigning the entire widget around StepFun-specific concepts.

## Acceptance Criteria

1. Real StepFun account usage or credit information can be retrieved.
2. StepFun data is normalized through the common model.
3. Existing credentials are reused without exposing secrets.
4. StepFun failure does not affect Codex or Cursor.
5. All three providers can appear together in Horizon.
6. StepFun discovery and limitations are documented.

## Handoff Contract

Before Phase 4 can be declared complete:

* Codex, Cursor, and StepFun must all work independently.
* Failure of one provider must not prevent others from displaying.
* Provider documentation must be complete.
* Shared-model compromises or extensions must be documented as decisions.
* Deferred work must be recorded.

Then STOP.

Do not begin Phase 5.

---

# Phase 5 — Operational Polish

## Goal

Make Horizon pleasant enough for normal daily use without expanding its core product scope.

## Entry Conditions

* Phase 4 handoff contract is satisfied.
* Three priority providers work end-to-end.

## Scope

May include:

* Periodic background refresh.
* Configurable refresh interval.
* Provider enable/disable settings.
* Auto-detection of available providers.
* Low-quota notifications.
* Better compact-panel summary.
* Better stale/error indicators.
* Multiple limits or model-specific breakdowns where provider data supports them.
* Packaging and installation improvements.
* User-facing README.
* Basic release/versioning process.

Each feature must still be introduced as an explicit task before implementation.

## Explicit Exclusions

* Supporting arbitrary new providers simply because they exist.
* Building a general-purpose account manager.
* Managing provider subscriptions.
* OAuth/login flows unrelated to an identified requirement.
* Analytics or telemetry.
* Cloud synchronization.
* Turning Horizon into a general AI desktop application.

## Acceptance Criteria

1. Horizon works reliably during normal Plasma sessions.
2. Refresh behavior does not create overlapping provider requests.
3. Provider failures remain isolated.
4. User-visible stale/error states are understandable.
5. Configuration introduced in this phase persists correctly.
6. Notifications, if implemented, are rate-limited and useful.
7. Installation and usage documentation is sufficient for a clean installation.
8. Core three-provider functionality remains intact.

## Handoff Contract

Phase 5 is complete when:

* Implemented polish items have explicit tasks and acceptance tests.
* All selected Phase 5 tasks pass.
* Installation and operating documentation is current.
* Known limitations and unstable unofficial integrations are documented.
* Remaining ideas are clearly separated as future work rather than silently included in the product scope.
* Repository state represents a usable first release.

Then STOP.

Any additional provider or significant capability requires a new phase contract.
