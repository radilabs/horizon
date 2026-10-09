# Horizon — Phase Contracts

> **Factory alignment note:** Phases 0–5 are accepted historical contracts created before Horizon adopted the current Stage-aware Factory shell. They are preserved without retrospective restructuring. Stage 1 / Phase 6 is the first work authorized under the current Stage-aware Factory lifecycle.

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

---

# Stage 1 — Reliability & Provider Resilience

## Goal

Strengthen reliability of Horizon's existing provider integrations after the 0.1.0 baseline without adding unrelated providers or expanding Horizon into an account-management product.

## Entry Conditions

* Phase 5 is accepted.
* Horizon 0.1.0 core three-provider functionality exists.
* Current Stage-aware Factory control files are present.

## Exit Conditions

Stage 1 may be accepted only when all explicitly authorized Stage 1 phases are accepted, core Codex/Cursor/StepFun behavior remains intact, security boundaries remain documented, and no deferred provider expansion has been implemented opportunistically.

Only Phase 6 is authorized at Stage 1 creation time.

## Owner Amendment — 2026-10-08

The owners deliberately extend Stage 1 with one planned provider addition: **Phase 6.5 — Claude Usage**. This amendment supersedes the "without adding unrelated providers" clause of the Stage 1 goal **for Claude only**. Claude is a priority tool in the owners' current agent mix and is a required design input for the Phase 7 provider information contract. It is not an opportunistic expansion.

Stage 1 closes after Phase 6.5 is accepted and the Stage 1 exit conditions are checked. The previously planned Phases 7–9 move to Stage 2.

Every other provider expansion (including Groq) remains excluded from Stage 1.

---

# Phase 6 — StepFun Auth Resilience

## Goal

Determine whether Horizon can safely recover from StepFun Oasis token expiry using only credential material it already stores, and implement bounded automatic renewal if the current Oasis mechanism supports it without username/password login, browser credential import, or a general authentication framework.

If automatic renewal cannot be safely proven using existing stored credential material alone, retain manual replacement as the supported mechanism and improve expiry handling/documentation without unsupported workarounds.

## Entry Conditions

* Phase 5 handoff is accepted.
* Existing StepFun usage works with a valid manually supplied Oasis token.
* StepFun token storage remains KWallet-backed.
* Stage 1 / Phase 6 is explicitly authorized in `TASKS.md`.

## Scope

* Characterize the currently stored Oasis token structure and expiry behavior using sanitized evidence.
* Determine whether existing stored material includes a usable refresh credential.
* Investigate the current StepFun/Oasis refresh endpoint, required headers, WebID/AppID behavior, token rotation semantics, and failure behavior.
* Review existing implementations where useful, but verify behavior against the current StepFun platform.
* If safe refresh is supported using existing stored token material alone, implement one bounded automatic refresh/retry path inside the StepFun provider/auth helper.
* Validate a refreshed token before replacing the KWallet value.
* Preserve clear manual Set/Replace Token behavior as fallback.
* Improve expired/rejected-token diagnostics where needed.
* Update StepFun/security documentation with the proven mechanism and limitations.
* Verify Codex/Cursor isolation and existing cache/refresh behavior.

## Explicit Exclusions

* StepFun username/password login.
* Storing StepFun username/password.
* Browser cookie/session import.
* Reading Zen or any other browser profile automatically.
* Building a generic Oasis framework.
* Building a general-purpose authentication/account manager.
* Adding Groq or any other provider.
* Subscription or billing management.
* Unbounded token-refresh loops.
* Changes to Codex or Cursor authentication unless required to fix a demonstrated regression introduced by this phase.

## Acceptance Criteria

1. The current Oasis credential structure and expiry/refresh capability are documented from sanitized evidence.
2. Horizon conclusively determines whether automatic StepFun renewal is safely possible using existing stored credential material alone.
3. If supported, an expired/rejected StepFun credential can be renewed with at most one bounded refresh attempt, the renewed credential is validated before KWallet replacement, and live usage succeeds afterward.
4. If unsupported, Horizon does not implement an unsafe workaround; expired/rejected credentials remain a clear `auth_unavailable` state with actionable manual replacement guidance.
5. No Oasis token, refresh token, JWT payload, password, cookie, or other secret is exposed in repo, config, cache, logs, stdout/stderr, process arguments, docs, or task evidence.
6. StepFun refresh/recovery failure does not affect Codex or Cursor.
7. Existing periodic/manual refresh behavior does not create an auth-refresh loop or overlapping StepFun recovery requests.
8. StepFun provider/security documentation accurately describes the current supported recovery path and upstream fragility.

## Handoff Contract

Before Phase 6 can be declared complete:

* All acceptance criteria must be supported by direct evidence.
* Valid-token and expired/rejected-token paths must be tested.
* If automatic refresh is implemented, refresh success and failure paths must be tested and KWallet rotation behavior verified without exposing token material.
* Codex and Cursor must still work independently.
* Secret audit must pass.
* Durable technical findings must be promoted to `docs/`; durable architectural/security decisions must be recorded only if future work must respect them.
* Deferred work must be recorded.
* Mandatory independent Watcher verification must return PASS.
* Project owners must explicitly accept the phase after Watcher PASS.
* `docs/handoffs/phase-6.md` is created as the accepted-state snapshot.

Then STOP.

Do not begin Groq discovery, another provider, or any additional capability phase automatically.

---

# Phase 6.5 — Claude Usage

> **Status:** accepted 2026-10-09. Snapshot: `docs/handoffs/phase-6.5.md`. The contract below is the historical execution boundary.

## Goal

Show real Claude subscription usage (Pro/Max), using the user's existing Claude Code authentication, alongside Codex, Cursor, and StepFun. The phase uses the existing normalized usage schema and records enough sanitized discovery evidence for Claude to serve as a required design input to Phase 7.

## Entry Conditions

* Phase 6 is accepted.
* Codex, Cursor, and StepFun work through the common provider model.
* The user has a working Claude Code login on the development machine.
* Stage 1 / Phase 6.5 is explicitly authorized in `TASKS.md`.

## Scope

* Investigate where Claude Code stores its local credentials, and their structure and expiry behavior, using sanitized evidence only.
* Investigate the current Claude subscription usage mechanism: endpoint, required headers, response shape, exposed usage windows, their labels and reset semantics, and failure behavior for expired, missing, or rejected credentials.
* Review existing open-source Claude usage trackers where useful, but verify their behavior against the current live service.
* Document the discovered mechanism in `docs/providers/claude.md`.
* Implement Claude provider detection and usage retrieval through the explicit provider registry (ADR-0005).
* Normalize Claude usage into the current schema: `remainingPercent`/`resetAt` for the primary window, and `breakdown` (ADR-0008) with the actual window labels Claude uses.
* Display Claude alongside the existing providers using the existing UI paths.
* Handle unavailable, expired, or rejected Claude authentication as a clear `auth_unavailable` state with actionable guidance (re-authenticate in Claude Code).
* Update security documentation for the new credential source.

## Explicit Exclusions

* Refreshing Claude OAuth tokens, or writing to, rotating, or copying Claude Code's credential store. Horizon reads only (as in ADR-0004 and ADR-0007), because rotating credentials could invalidate the user's Claude Code session.
* Implementing a Claude login flow.
* Storing Claude credentials in KWallet or anywhere else.
* Anthropic API-key / Console billing or API usage tracking.
* Browser cookie or session import.
* Changes to the shared normalized schema, beyond what is strictly required to represent proven Claude data. Any such change must be justified and recorded; the schema redesign belongs to Phase 7.
* UI redesign. That belongs to Phases 8–9.
* Changes to Codex, Cursor, or StepFun behavior, unless required to fix a demonstrated regression introduced by this phase.
* Any other provider (including Groq).

## Acceptance Criteria

1. The Claude credential source, usage mechanism, and exposed usage windows are documented from sanitized evidence.
2. Horizon detects usable Claude Code authentication where it is present.
3. Real Claude usage, including every window the provider exposes with its reset time where available, is retrieved and normalized through the common provider model.
4. Claude appears correctly in the widget alongside Codex, Cursor, and StepFun.
5. Missing, expired, or rejected Claude credentials produce a clear `auth_unavailable` state, and Horizon never attempts a token refresh or modifies Claude Code's credential store.
6. No Claude token, refresh token, or other secret is exposed in repo, config, cache, logs, stdout/stderr, process arguments, docs, or task evidence.
7. Claude failure does not affect Codex, Cursor, or StepFun.
8. Periodic and manual refresh create no overlapping Claude requests.
9. Discovery documentation records the full Claude window structure (count, labels, reset semantics) in a form Phase 7 can use as a design input.

## Handoff Contract

Before Phase 6.5 can be declared complete:

* All acceptance criteria must be supported by direct evidence.
* Claude success, missing-auth, expired/rejected-auth, and upstream-failure paths must be tested.
* Codex, Cursor, and StepFun must still work independently.
* Secret audit must pass.
* Known upstream/API fragility (unofficial mechanism) must be documented.
* Durable technical findings must be promoted to `docs/`. Decisions must be recorded only if future work must respect them.
* Deferred work must be recorded.
* Mandatory independent Watcher verification must return PASS.
* Project owners must explicitly accept the phase after Watcher PASS.
* `docs/handoffs/phase-6.5.md` is created as the accepted-state snapshot.

Then STOP.

After acceptance, check the Stage 1 exit conditions explicitly. Do not open Stage 2 or begin Phase 7 automatically.

---

# Planned Stage 2 — Provider Contract & UX (Not Authorized)

> **Stage 2 does not exist as an executable stage until Stage 1 is accepted (including Phase 6.5) and the owners explicitly open Stage 2.** Its goal, entry conditions, and exit conditions are refined at that time.

**Intent:** Move provider semantics into a provider-owned information contract and redesign the Plasma UI around it, across all four providers (Codex, Cursor, StepFun, Claude).

The following phase outlines record owner intent so future design and execution remain grounded in the repository. They are **planning anchors only**: they do not authorize implementation, do not create executable tasks, and may be refined before authorization. Preserve the existing Stage-aware Factory lifecycle: authorize one phase explicitly, create/refine its task file, execute, obtain independent Watcher PASS, obtain owner acceptance, then stop.

## Phase 7 — Provider Information Contract

**Intent:** Move human-facing provider semantics out of QML and into the normalized provider information package.

The provider contract should be able to supply provider identity/display name, plan information, and an ordered collection of quota/usage entries. Each quota entry owns its provider-native human-facing label, remaining percentage, reset information, and any state needed for presentation. The UI must not invent provider-specific concepts or hard-code assumptions such as a universal primary/secondary quota pair.

Codex naming should be corrected against the provider's actual exposed quota semantics. Cursor, StepFun, and Claude should retain their real provider/model/quota terminology. The contract must support an arbitrary 1..N quota entries so future providers can fit without redesigning the UI model.

**Required design input (owner decision 2026-10-08):** the contract must be designed against real Claude usage data documented by Phase 6.5. Claude is expected to expose the richest window structure of the four providers.

Detailed schema design, migration strategy, acceptance criteria, and implementation tasks are intentionally deferred until Phase 7 is explicitly authorized.

## Phase 8 — Plasma UI/UX Refresh

**Intent:** Redesign Horizon's expanded representation around the provider-owned information contract from Phase 7.

The target is a polished, information-dense Plasma 6 widget that remains native to KDE/Kirigami rather than introducing a foreign visual system. Provider sections should naturally support arbitrary quota rows and make remaining quota and reset timing easy to scan.

Exact visual design, layout, interaction details, state treatment, accessibility requirements, acceptance criteria, and implementation tasks are intentionally deferred until Phase 8 is explicitly authorized.

## Phase 9 — Compact UX and Release Polish

**Intent:** Bring the compact panel representation, tooltip, refresh interaction, responsive behavior, theme/scaling behavior, documentation, and screenshots into alignment with the redesigned expanded view.

This phase is expected to form the final polish/release boundary for the redesign, but no release version is committed by this planning note.

Detailed scope, acceptance criteria, release decision, and implementation tasks are intentionally deferred until Phase 9 is explicitly authorized.

No new provider is authorized by these planned phases. *(2026-10-08: this note previously read "including Claude"; that is superseded by the Stage 1 Owner Amendment, which plans Claude as Phase 6.5.)* Every other provider expansion remains separate future work.

