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

# Planned Stage 2 — Provider Contract & UX (planning record)

> **Execution note (2026-10-09):** Owners authorized Stage 2 / Phase 7. The executable contract is `# Stage 2 — Provider Contract & UX` and `# Phase 7 — Provider Information Contract` below. This earlier outline is a planning record, not a second contract.

> **Historical text:** This section was written as "Not Authorized" before Stage 1 closed. Stage 2 did not exist as an executable stage until Stage 1 was accepted and the owners opened Stage 2.

**Intent:** Move provider semantics into a provider-owned information contract and redesign the Plasma UI around it, across all four providers (Codex, Cursor, StepFun, Claude).

The following phase outlines record owner intent so future design and execution remain grounded in the repository. They are **planning anchors only**: they do not authorize implementation, do not create executable tasks, and may be refined before authorization. Preserve the existing Stage-aware Factory lifecycle: authorize one phase explicitly, create/refine its task file, execute, obtain independent Watcher PASS, obtain owner acceptance, then stop.

## Phase 7 — Provider Information Contract

**Intent:** Move human-facing provider semantics out of QML and into the normalized provider information package.

The provider contract should be able to supply provider identity/display name, plan information, and an ordered collection of quota/usage entries. Each quota entry owns its provider-native human-facing label, remaining percentage, reset information, and any state needed for presentation. The UI must not invent provider-specific concepts or hard-code assumptions such as a universal primary/secondary quota pair.

Codex naming should be corrected against the provider's actual exposed quota semantics. Cursor, StepFun, and Claude should retain their real provider/model/quota terminology. The contract must support an arbitrary 1..N quota entries so future providers can fit without redesigning the UI model.

**Required design input (owner decision 2026-10-08):** the contract must be designed against real Claude usage data documented by Phase 6.5. Claude is expected to expose the richest window structure of the four providers.

Detailed schema design, migration strategy, acceptance criteria, and implementation tasks are intentionally deferred until Phase 7 is explicitly authorized.

## Phase 8 — Plasma UI/UX Refresh

> **Status:** accepted 2026-10-09. Snapshot: `docs/handoffs/phase-8.md`. Compact-panel redesign and release polish stay in Phase 9.

**Intent:** Redesign Horizon's expanded representation around the provider-owned information contract from Phase 7.

The target is a polished, information-dense Plasma 6 widget that remains native to KDE/Kirigami rather than introducing a foreign visual system. Provider sections should naturally support arbitrary quota rows and make remaining quota and reset timing easy to scan.

Exact visual design, layout, interaction details, state treatment, accessibility requirements, acceptance criteria, and implementation tasks are intentionally deferred until Phase 8 is explicitly authorized.

## Phase 9 — Compact UX and Release Polish

> **Status:** accepted 2026-10-09. Snapshot: `docs/handoffs/phase-9.md`. Owners also approved Horizon **0.2.0** (`v0.2.0`) on that date.

**Intent:** Bring the compact panel representation, tooltip, refresh interaction, responsive behavior, theme/scaling behavior, documentation, and screenshots into alignment with the redesigned expanded view.

This phase is expected to form the final polish/release boundary for the redesign, but no release version is committed by this planning note.

> **Execution note (2026-10-09):** Owners authorized Phase 9 after Phase 8 was accepted and merged to `main` at `0a06644`. The executable task is `tasks/phase-9-compact-ux-release-polish.md`. The contract below is the authorized execution boundary. A release, version bump or tag still needs separate owner approval.

### Goal

Make the compact panel summary, the tooltip, the popup's size and its Refresh action honest and readable for 1..N ordered meters (ADR-0012). Then bring the screenshots, user documentation, changelog and Plasma reload/upgrade guidance up to date, and produce release-readiness evidence with a version recommendation. Horizon stays at **0.1.1** during this phase.

### Entry Conditions

* Phase 8 accepted (`docs/handoffs/phase-8.md`) and on `main` at `0a06644`.
* Stage 2 / Phase 9 explicitly authorized in `TASKS.md`.

### Scope

* **Compact summary.** Replace "lowest remaining across every row" with this rule, computed from the same meter intake the popup uses (`MeterIntake.js`, i.e. `meters`, then `breakdown`, then primary/secondary), not from `breakdownJson`. Only `ok`/`stale` providers with quota contribute:
  * **Headline:** the lowest percent **remaining** among meters that are above 0.
  * **Exhausted count:** the number of meters at exactly 0.
  * **Text:** `AI <n>%` when no meter is exhausted. `AI <n>% · <k> at 0%` when some, but not all, meters are exhausted. `AI 0%` when every contributing meter is exhausted.
  * **No quota anywhere:** keep the existing `AI` / `AI !` / `AI —` / `AI …` states.

  The compact text never hides an exhausted meter, and never reports a single exhausted meter as if all usage were gone. The rule is provider-neutral. It does not infer whether a provider's meters are alternatives or joint limits.
* **Tooltip.** One block per enabled provider, read from the same meter intake:
  * a provider line with the name, plus the plan when known, plus a cached marker and age when stale;
  * then one line per meter, giving its label and percent remaining, in payload order.

  Failure providers show their status label plus the payload's user-safe `error` text, on one line and shortened if long. Resets are not shown in the tooltip. They stay in the popup.
* **Popup height.**
  * Preferred height follows content.
  * The popup is bounded below by `Kirigami.Units.gridUnit * 12`, and above by the smaller of `gridUnit * 40` and about 80% of the available screen height.
  * The provider list keeps scrolling inside the `ScrollView` once that maximum is reached.
  * Width stays as accepted in Phase 8.
  * There are no fixed pixel sizes.
* **Refresh.**
  * Move Refresh into the popup header as a native `view-refresh` tool button with a visible tooltip.
  * Give it an accessible name and description. It is keyboard-focusable and can be activated with Enter or Space. F5 also refreshes while the popup has focus.
  * It shows a busy state while any provider is in flight, and is disabled when no provider is enabled.
  * The bottom footer row is removed, unless something non-redundant still needs it.
* **Readability.** Refine provider separation, spacing, header hierarchy and progress bars using Plasma/Kirigami components and theme values only. An exhausted meter may use the theme's negative color as a supplement to its existing text, never as a replacement. There are no other invented thresholds.
* **QML cleanup.** Model fields that become unused after compact and tooltip move to meter intake (`breakdownJson`, `secondaryRemainingPercent`) may be removed from QML. This change is QML-only.
* **Documentation.**
  * Real-desktop README screenshots: popup, compact plus tooltip, and settings showing all four providers.
  * README and `docs/release.md` text matching the new compact rule.
  * A `CHANGELOG.md` "Unreleased" entry.
  * Plasma reload guidance after install/upgrade, in the README, and optionally as a printed hint in `scripts/install.sh` (which `scripts/upgrade.sh` runs).
* **Release readiness.** Run the `docs/release.md` validation checklist against this branch, run the secret audit, and record a version recommendation with its rationale for the owners.
* **Tests.** Deterministic `qmltestrunner6` tests for the compact rule and the tooltip text, including mixed states. The existing Python and QML tests still pass.

### Explicit Exclusions

* Collector, provider normalize, cache, cache schema, authentication, or ADR-0012 changes. `git diff 0a06644 -- collector` stays empty.
* New providers (including Groq), billing, spend, balances, accounts, login flows, backend refactoring.
* Provider-specific compact logic, for example treating Cursor pools as alternatives or Claude windows as joint limits.
* New configuration keys or settings UI, notifications, compact icon/graphic redesign, alternative compact modes.
* A general-purpose UI framework or component library.
* Changing `VERSION`, `plasmoid/metadata.json` `KPlugin.Version`, or the README version line. Creating git tags or GitHub releases. Publishing anything.
* Rewriting accepted Phase 0–8 contracts, task files or handoffs.

### Acceptance Criteria

1. **Compact, mixed states.** On a real panel and in tests:
   * one meter at 0% with others high (Cursor Other Models 0, Cursor Models 75, Codex/StepFun/Claude high) shows `AI 75% · 1 at 0%`, not `AI 0%`;
   * all healthy shows `AI <lowest>%`;
   * every meter at 0 shows `AI 0%`;
   * auth or error with no quota anywhere shows `AI !` / `AI —`;
   * no providers enabled shows `AI`;
   * loading shows `AI …`;
   * stale cached meters count with their cached values.
2. **Compact fits.** The compact text is readable without clipping on a horizontal panel. On a vertical panel, eliding or wrapping is acceptable as long as the tooltip carries the full text.
3. **Tooltip.**
   * Lists every enabled provider, with each meter's label and percent remaining in order.
   * Stale providers are marked with their age. Failure providers show their status and user-safe error text.
   * No Primary/Secondary label, no invented plan, and no reset a meter lacks.
4. **Popup height.**
   * On a landscape screen, four providers fit without excess empty space.
   * On a portrait screen, or one constrained to a portrait-like height, the popup stays on screen and the provider list scrolls.
   * Nothing is clipped.
   * Checked on a freshly added widget, because Plasma may keep a user-resized popup size.
5. **Refresh.** Visible in the header. Reachable and activatable by keyboard, F5 works, it has an accessible name, it shows a busy state while refreshing, and it is disabled with no providers. It never starts overlapping per-provider requests.
6. **No popup regression.** The Phase 8 behavior still holds:
   * meters → breakdown → primary/secondary intake;
   * a reset only on meters that have their own `resetAt`;
   * percent remaining;
   * text-identifiable states with no bars on failure;
   * `tests/test_meter_intake.qml` passes.
7. **Native look.** Kirigami/Plasma theme values only. Readable in Breeze Light and Breeze Dark, both for the popup and the compact panel plus tooltip.
8. **Documentation.**
   * The README screenshots are captured on the real Plasma desktop, committed under `docs/assets/`, and contain no secrets, tokens, emails or account ids.
   * The README, `docs/release.md` and `CHANGELOG.md` describe the actual behavior.
   * Reload/upgrade guidance is accurate and verified once on this machine.
9. **Release readiness.** The `docs/release.md` checklist is run and its result recorded. A version recommendation with rationale is recorded for the owners. No version files changed, and no tag or release was created.
10. **Boundaries.** The collector diff from `0a06644` is empty, all tests pass, and the secret audit passes. Out-of-scope discoveries are recorded as Deferred Work.
11. Independent Watcher verification returns PASS. Owners explicitly accept after reviewing the evidence.

### Handoff Contract

* Record direct evidence for every criterion in the task file. Runtime screenshots and Watcher reports go under the gitignored `reports/`. README images go under `docs/assets/`.
* Independent Watcher PASS, then explicit owner acceptance.
* Only after acceptance, write `docs/handoffs/phase-9.md`.
* Any release (version bump, tag, GitHub release) is a separate, explicitly approved owner action, not part of this phase.
* STOP. Do not start new work or a new stage automatically.

No new provider is authorized by these planned phases. *(2026-10-08: this note previously read "including Claude"; that is superseded by the Stage 1 Owner Amendment, which plans Claude as Phase 6.5.)* Every other provider expansion remains separate future work.



---

# Stage 2 — Provider Contract & UX

## Goal

Make Horizon's provider information coherent and extensible for real observed subscription usage, then improve the KDE Plasma presentation without changing the established authentication and collection boundaries.

## Entry Conditions

* Stage 1 exit conditions checked and Stage 1 closed.
* Phase 6 and Phase 6.5 accepted; four existing providers available as evidence.
* Owners explicitly authorize Stage 2 / Phase 7.

## Planned Phases

* Phase 7 — Provider Information Contract (accepted 2026-10-09; snapshot `docs/handoffs/phase-7.md`).
* Phase 8 — Plasma UI/UX Refresh (accepted 2026-10-09; snapshot `docs/handoffs/phase-8.md`).
* Phase 9 — Compact UX and Release Polish (accepted 2026-10-09; snapshot `docs/handoffs/phase-9.md`).

> **Status:** closed 2026-10-09. Phases 7, 8, and 9 are accepted. Horizon **0.2.0**. No later phase is authorized.

## Exit Conditions

All authorized Stage 2 phases are accepted; existing four providers and security boundaries remain intact; UX is evaluated on real KDE Plasma; documentation and operational behavior reflect the accepted product. No later phase is opened automatically.

---

# Phase 7 — Provider Information Contract

> **Status:** accepted 2026-10-09. Snapshot: `docs/handoffs/phase-7.md`. The contract below is the historical execution boundary.

## Goal

Define and validate the smallest provider-neutral usage information contract that faithfully represents the existing Codex, Cursor, StepFun and Claude subscription data, so Phase 8 can redesign the UI without embedding provider-specific assumptions.

## Entry Conditions

* Stage 1 closed, Phase 6.5 accepted.
* Stage 2 / Phase 7 explicitly authorized in `TASKS.md`.
* Current collector schema, UI consumers, and sanitized provider discovery docs are available.

## Scope

* Inventory the actual normalized outputs, distinct usage windows, labels, reset semantics, availability/auth/stale states and supported metadata for all four existing providers.
* Use Claude's multiple independently resetting windows as a mandatory test case; inspect StepFun/Cursor/Codex variations too.
* Define a minimal, documented provider-neutral contract for one or more displayable usage meters; specify semantics for percentage remaining versus consumed, unknown values, timestamps, and status.
* Distinguish proven present-day data from future candidates (balances, spending, rate limits and multiple accounts). Do not add speculative fields merely to cover hypothetical providers.
* Decide a compatibility/migration approach for existing collector JSON, persisted cache and current QML; implement only changes needed to establish and verify the Phase 7 contract, keeping existing visible behavior stable.
* Add deterministic fixture/contract tests that exercise each existing provider's normalized result and failure/stale cases.
* Document durable information-model decisions and the Phase 8 UI-facing contract.

## Explicit Exclusions

* Plasma popup redesign, layout/style changes or compact UI redesign (Phases 8–9).
* New providers, including Groq, OpenRouter, Anthropic API billing and SendGrid.
* Credential refresh, login or authentication changes for any provider.
* General plugin architecture, multi-account management, billing or purchase flows.
* A speculative universal financial/usage model unsupported by current evidence.
* Unrelated feature work, notification changes or upgrades to unrelated dependencies.

## Acceptance Criteria

1. Sanitized examples and a clear field/semantic inventory cover all four current providers, including Claude's session and weekly windows and their independent reset timestamps.
2. The documented contract can express current multi-meter outputs, plan/provider identity, missing/unknown data, per-meter reset, success, auth-unavailable, upstream-error and stale states without provider-specific QML assumptions.
3. Meter direction and scale (used versus remaining) are unambiguous; no fabricated usage values, resets or plan/account identities.
4. The compatibility story for current CLI output, cache and QML is explicit and verified; no regression in any of the four providers or the current widget.
5. Deterministic contract/fixture tests pass, including multi-window and error/stale scenarios.
6. No credential material appears in committed artifacts, logs or test fixtures.
7. Out-of-scope opportunities are recorded as deferred work rather than implemented.
8. Independent Watcher verification returns PASS; owners explicitly accept after reviewing evidence.

## Handoff Contract

* Record direct test evidence and the schema/compatibility decisions in the active task and durable documentation.
* Verify all four provider paths remain independent, with no secret exposure and no incidental UI changes.
* Independent Watcher PASS, followed by explicit owner acceptance.
* Only after acceptance, write `docs/handoffs/phase-7.md` as the accepted-state snapshot and produce the checkpoint.
* STOP. Do not start Phase 8.

---

# Stage 3 — Maintenance & Hardening

## Goal

Correct verified defects, quality gaps and documentation drift in the accepted Horizon **0.2.0** baseline without adding providers or features, and without changing the authentication boundaries or the ADR-0012 meters contract.

## Entry Conditions

* Stage 2 closed (2026-10-09). Phase 9 accepted. Horizon **0.2.0** (`v0.2.0`) released.
* An external Watcher audit of the 0.2.0 baseline exists: `reports/post-v0.2.0-external-watcher-1.md` (findings W-01..W-14).
* Owners explicitly authorize Stage 3 / Phase 10 (authorized 2026-11-27).

## Planned Phases

* Phase 10 — Post-0.2.0 Remediation (accepted 2026-11-27; snapshot `docs/handoffs/phase-10.md`).
* Phase 11 — Cursor Credential Compatibility (accepted 2026-11-27; snapshot `docs/handoffs/phase-11.md`).

> **Status:** closed 2026-11-27. Phase 10 and Phase 11 are accepted. Horizon **0.2.1**. No later phase is authorized.

No other Stage 3 phase is planned or authorized.

## Exit Conditions

All authorized Stage 3 phases are accepted. The four existing providers (Codex, Cursor, StepFun, Claude) remain. ADR-0013 supersedes only ADR-0007's single-source restriction and its only-remediation rule. The read-only, no-write, no-login, and no-refresh boundaries, and the ADR-0012 meters contract, remain in force. No provider or feature expansion is implemented. No later phase is opened automatically.

---

# Phase 10 — Post-0.2.0 Remediation

> **Status:** accepted 2026-11-27. Snapshot: `docs/handoffs/phase-10.md`. Released as Horizon **0.2.1** (`v0.2.1`).

## Goal

Resolve external Watcher findings W-01..W-14 (`reports/post-v0.2.0-external-watcher-1.md`) against the 0.2.0 baseline with the smallest correction each finding needs, with direct test or inspection evidence for each.

## Entry Conditions

* Stage 3 / Phase 10 explicitly authorized in `TASKS.md`.
* Baseline `eadcfb3` (`v0.2.0` at `cbc2c93` plus the audit report commit). Python and QML tests pass at baseline.

## Scope

Only findings W-01..W-14, each with the smallest fix that matches the report:

* **W-01 — StepFun credit breakdown.** The single `Credits` meter is derived only from valid `credit_buckets`. When buckets are absent or invalid, the existing `Subscription Credits` / `Top-up Credits` branch becomes reachable and is used. Separate rates are never added together or collapsed into one `Credits` row. Docs match the code.
* **W-02 — StepFun refresh duplicate request.** The usage body that validated a refreshed (or already-rotated) token is returned and reused by `fetch_usage()`. `QueryStepPlanRateLimit` is not posted a second time for that recovery. A successful usage response is still required before any KWallet write.
* **W-03 — Refresh key handling.** Remove the redundant `Keys.onSpacePressed` from the popup Refresh button, make Return/Enter acceptance explicit, and test that Space, Return and Enter each activate Refresh exactly once and not at all when disabled.
* **W-04 — StepFun auth status.** `stepfun_auth_helper.py` and `ai-usage auth stepfun set|status` distinguish auth rejection (`auth_unavailable` → `auth_failed`) from network/upstream/collector failure (a distinct non-destructive status). The settings page shows an accurate message for the new status. Remove the unused `token` parameter of `verify_token()`.
* **W-05 — Settings helper path and launch failure.** Resolve the helper under the XDG data location the installer uses, show a clear error state when the helper produces no stdout or exits non-zero, and remove the stale fallback comment.
* **W-06 — Provider numeric and I/O edge cases.** Treat `bool` and non-finite numbers as invalid in the cited Claude/Codex/Cursor parsers (same outcome as existing invalid values). Catch `OSError` in Codex `_load_auth()` and `json.JSONDecodeError` in Codex `_refresh_tokens()` as `ProviderError`.
* **W-07 — Shell quoting.** Shell-quote the collector path in `main.qml` `collectorCommand()`.
* **W-08 — Frozen relative times.** Reset and cache-age text in the popup is recomputed from stored timestamps on popup open or a lightweight periodic tick, not frozen between refreshes.
* **W-09 — Installer pipefail.** Remove the `grep -q` under `pipefail` pattern from `install.sh` and `uninstall.sh` `kpackagetool6 --list` checks.
* **W-10 — Cache secret-key check.** The cache writer rejects the existing forbidden secret keys recursively (nested dicts and lists) and case-insensitively. The set of stored public fields does not change.
* **W-11 — qmllint.** Fix the cited warnings only: the unused import and unqualified `stepfunBusy` in `configGeneral.qml`; `pragma ComponentBehavior: Bound`, `required property` on `Repeater` delegates, and qualified `plasmoid.configuration` access in `main.qml`.
* **W-12 — Test hygiene.** Restore any pre-existing `XDG_CACHE_HOME` in `test_cache_refuses_secret_fields`. Add targeted tests alongside W-01..W-06.
* **W-13 — Codex doc.** `docs/providers/codex.md` matches the installed wrapper script and the full duration-label mapping.
* **W-14 — Doc drift.** Fix `docs/providers/cursor.md` plan source, `docs/cache.md` persisted fields, and `docs/release.md` release-notes command. Document the existing in-process `threading.Lock` in `docs/providers/stepfun.md`.

## Explicit Exclusions

* New providers (including Groq), billing, spend, balances, accounts, login flows, or new features of any kind.
* Changes to authentication boundaries or credential-store behavior beyond W-02/W-04 as written: no new token refresh paths, no Codex/Cursor/Claude credential changes, no storing of an unvalidated refreshed token, no weakening of `auth_unavailable`.
* Changes to the ADR-0012 meters contract, the normalized payload schema, or the set of cached public fields.
* A cross-process lock for StepFun refresh. Editing ADR-0010, ADR-0012, or any other accepted decision record.
* QML redesign, layout or visual changes, new settings, new configuration keys. qmllint warnings beyond those cited in W-11.
* Changing `VERSION`, `plasmoid/metadata.json` `KPlugin.Version`, or the README version line. Tags, GitHub releases, publishing.
* Rewriting accepted Phase 0–9 contracts, task files or handoffs.

## Acceptance Criteria

1. Each of W-01..W-14 is resolved as specified in Scope, with the per-finding acceptance check in the task file supported by direct evidence (test, diff, command output or runtime observation), or recorded with evidence as a false positive where the task file allows it.
2. StepFun: credit payloads without valid buckets produce `Subscription Credits` / `Top-up Credits` meters, never a merged `Credits` row from separate rates. Refresh recovery issues exactly one `QueryStepPlanRateLimit` per token it validates, and KWallet is written only after a successful usage response.
3. StepFun auth status: an offline or upstream failure is never reported as a rejected token. A rejected token still reports `auth_failed` / `auth_unavailable`.
4. No regression: all pre-existing Python and QML tests pass, plus new tests. The four providers still work independently on this machine (`ai-usage status <id> --json` for each).
5. ADR-0012 contract unchanged: meter labels other than W-01's restored credit labels, meter order, remaining-percent semantics and cached field set are unchanged.
6. `qmllint6` shows none of the W-11 cited warnings, and its total warning count does not increase over the baseline.
7. The widget and settings page load and work on the real Plasma desktop after `scripts/install.sh` (popup, Refresh keys, StepFun settings status).
8. Secret audit passes. No token or secret appears in the diff, tests, logs or task evidence.
9. `VERSION` and version strings are unchanged. No tag or release.
10. Out-of-scope discoveries are recorded as Deferred Work.
11. Independent Watcher verification returns PASS. Owners explicitly accept after reviewing the evidence.

## Handoff Contract

* Record direct evidence for every W-ID and every criterion in the task file. Watcher reports go under the gitignored `reports/` as `stage-3-phase-10-watcher-<attempt>.md`.
* Promote durable facts to `docs/` only where W-01, W-13 and W-14 require it. No new decision record unless future work must respect a new choice.
* Independent Watcher PASS, then explicit owner acceptance.
* Only after acceptance, write `docs/handoffs/phase-10.md` and produce the checkpoint.
* Any release (version bump, tag, GitHub release) is a separate, explicitly approved owner action.
* STOP. Do not start new work or a new phase automatically.

---

# Phase 11 — Cursor Credential Compatibility

> **Status:** accepted 2026-11-27. Snapshot: `docs/handoffs/phase-11.md`. Horizon remains **0.2.1**. No release in this checkpoint.

## Goal

Restore Cursor `GetCurrentPeriodUsage` for a signed-in user on Cursor desktop 3.28.x. The desktop IDE now stores an opaque, non-JWT `cursorAuth/accessToken` that the API rejects with HTTP 401. Add the Cursor CLI's own `~/.config/cursor/auth.json` as a second read-only, Cursor-owned credential source, as decided in ADR-0013. Credentials stay Cursor-owned, read-only and in memory only.

## Entry Conditions

* Phase 10 accepted (2026-11-27). Horizon **0.2.1** (`v0.2.1` at `3891626`).
* ADR-0013 (`decisions/0013-cursor-dual-source-read-only-credentials.md`) accepted by the owner.
* Stage 3 / Phase 11 explicitly authorized in `TASKS.md` (2026-11-27).
* Baseline `3891626`: `python3 -m unittest discover -s tests` passes (48 tests); the QML test suites pass.

## Scope

Only `collector/providers/cursor.py`, any small `collector/ai-usage` wiring it needs, and new or updated Python tests. Docs follow afterwards through the Writer step below.

1. **IDE source (unchanged path).** Read `cursorAuth/accessToken` from `state.vscdb` with SQLite `mode=ro`. `--auth-file` and `CURSOR_STATE_VSCDB` remain the IDE override.
2. **JWT shape gate.** Use the IDE value only when it is a non-empty string of exactly three non-empty `.`-separated segments. Do not decode, split, decrypt or exchange a non-JWT value, and do not send it.
3. **CLI source.** Add read-only support for `~/.config/cursor/auth.json`, using only its top-level `accessToken` string. Never use, send or keep `refreshToken`. Add a test-only path override, `CURSOR_CLI_AUTH_FILE`, that never becomes a credential store.
4. **Order.** A usable IDE JWT is tried first. Only on HTTP 401/403 from that attempt, or when the IDE source has no sendable value, try the CLI token.
5. **No fallback on upstream failure.** A network error, a non-auth HTTP status, a non-200 response, invalid JSON or an unexpected shape from any attempt stops with `upstream_error`.
6. **Plan info.** Reuse the bearer that got HTTP 200 for `GetPlanInfo`. Existing `stripeMembershipType` fallback unchanged. A `GetPlanInfo` failure never triggers a credential fallback.
7. **detect().** Raise `auth_unavailable` only when neither source file is present.
8. **Failure message.** When no source succeeds: `auth_unavailable` with a per-source outcome from the ADR-0013 fixed set (`not found`, `unreadable`, `no token`, `unsupported format`, `rejected (HTTP 401)`, `rejected (HTTP 403)`). No token text, lengths, prefixes, claims, emails or user ids.
9. **Preserve.** Endpoints, request headers, request body, the `autoPercentUsed`/`apiPercentUsed` meter mapping, the normalized payload, the cached field set, and `auth_unavailable` / `upstream_error` / `stale` semantics.
10. **Tests.** Regression tests for both sources, missing or invalid credentials, fallback precedence, authentication rejection, upstream failures, and the security checks: fixture files unchanged after a fetch, no token substring in output or cache, `refreshToken` never sent.
11. **Writer step (after implementation, before Watcher).** Update the current Cursor docs against ADR-0013: `docs/providers/cursor.md`, `docs/provider-contract.md`, and `docs/security.md`.

## Explicit Exclusions

* Token refresh, rotation, write-back, login, OAuth, device flows, running `agent` or Cursor, or token exchange of any kind.
* Decoding or inspecting any token, including a local JWT `exp` check (Deferred Work).
* New providers (including Groq) and any general authentication framework or shared credential layer.
* Changes to the ADR-0012 ordered meter contract, `docs/usage-schema.md`, the normalized schema, or the cached field set.
* Changes to Codex, StepFun or Claude providers or their authentication boundaries (ADR-0004, 0009, 0010, 0011).
* Editing ADR-0007 or any other accepted decision record, or accepted historical task files and handoffs (including `docs/handoffs/phase-3.md` and `docs/handoffs/phase-10.md`).
* `VERSION`, `plasmoid/metadata.json` `KPlugin.Version`, the README version line, CHANGELOG release entries, tags, GitHub releases, or pushing to `main` during implementation.
* Plasmoid QML, layout or visual changes.
* Creating `docs/handoffs/phase-11.md` before owner acceptance.

## Acceptance Criteria

1. **Dual source with a fake API.** With `CURSOR_API_BASE` pointed at a local fake server and fixture files only (no real credentials), automated tests show:
   - (a) an IDE JWT accepted gives `ok`, sends no CLI request, and uses the IDE bearer for `GetPlanInfo`;
   - (b) an IDE JWT rejected with 401, and separately with 403, followed by a valid CLI token gives `ok` using the CLI bearer, which `GetPlanInfo` reuses;
   - (c) a non-JWT IDE value is never sent and the CLI token is used;
   - (d) a missing IDE database with a valid CLI file gives `ok`;
   - (e) neither file present gives `auth_unavailable` from `detect()`;
   - (f) both sources rejected, absent, unreadable or without a token give `auth_unavailable` with the correct fixed outcome for each source.
2. **No fallback on upstream failure.** A network error, an HTTP 500, a 200 with invalid JSON, or a 200 missing both percent fields from the IDE attempt gives `upstream_error` with zero CLI requests. A warm cache in those cases gives `stale`.
3. **Read-only.** Both fixture files are byte-identical with unchanged mtime after every fetch path.
4. **Secret audit.**
   - No fixture token substring appears in stdout, stderr, `--json` output, error messages or the cache file.
   - No request carries a `refreshToken` value.
   - No real token appears in the diff, tests, logs or evidence.
   - No new file stores Cursor credentials.
5. **Contract preserved.** Endpoints, headers, meter labels and order, remaining-percent semantics and cached field set are unchanged (diff review plus existing `CursorContractTests`). The status vocabulary is unchanged.
6. **No regression.** All pre-existing Python and QML tests pass, plus the new tests. The four providers still work independently on this machine (`ai-usage status <id> --json` for codex, cursor, stepfun, claude), and Cursor returns `ok` live for the signed-in owner.
7. **Scope fence.**
   - `git diff 3891626` touches only `collector/providers/cursor.py`, optional minimal `collector/ai-usage` wiring, `tests/`, the three Writer docs, `decisions/0013-…`, and the Factory files (`PHASES.md`, `TASKS.md`, `tasks/`).
   - `decisions/0007-…`, `VERSION`, `plasmoid/` and `docs/handoffs/` are unmodified.
8. **Docs.** The Writer docs match ADR-0013 and the implemented behavior.
9. **Deferred Work.** Out-of-scope discoveries are recorded in the task file.
10. **Watcher, then stop.** Independent Watcher verification returns PASS. Work then stops for explicit owner acceptance.

## Handoff Contract

* Record direct evidence for every task and criterion in `tasks/phase-11-cursor-credential-compatibility.md`. Watcher reports go under the gitignored `reports/` as `stage-3-phase-11-watcher-<attempt>.md`.
* Independent Watcher PASS, then explicit owner acceptance.
* Only after acceptance, write `docs/handoffs/phase-11.md` and produce the checkpoint.
* Any release (version bump, tag, GitHub release) is a separate, explicitly approved owner action.
* STOP. Do not start new work or a new phase automatically.

---

# Stage 4 — Provider Expansion

## Goal

Add AI coding subscriptions the owner uses as small, provider-specific adapters on the existing explicit `PROVIDERS` registry and the ADR-0012 ordered-meters contract. Each new provider gets its own read-only usage path and an authentication boundary that is already permitted. There is no shared authentication rewrite, no new credential framework, and no change to the four existing providers' behavior beyond what a phase contract names.

## Entry Conditions

* Stage 3 closed (2026-11-27). Phase 11 accepted. Horizon **0.2.1** (`v0.2.1`). `main` at `220563f`.
* Discovery record for the first provider exists: `docs/research/xiaomi-mimo-coding-plan.md` (verdict CONDITIONAL GO).
* Owners explicitly authorize Stage 4 / Phase 12 and record their decisions (authorized 2026-11-27).

## Planned Phases

* Phase 12 — Xiaomi MiMo Token Plan (accepted 2026-11-27; snapshot `docs/handoffs/phase-12.md`).

> **Status:** closed 2026-11-27. Phase 12 is accepted. Horizon remains **0.2.1**. No later phase is authorized.

No other Stage 4 phase is planned or authorized.

## Exit Conditions

Every authorized Stage 4 phase is accepted by the owners. Existing providers (Codex, Cursor, StepFun, Claude) keep their accepted behavior. ADR-0012, ADR-0009 and the read-only, no-login, no-cookie and no-refresh boundaries stay in force. No later phase is opened automatically.

---

# Phase 12 — Xiaomi MiMo Token Plan

> **Status:** accepted 2026-11-27. Snapshot: `docs/handoffs/phase-12.md`. Horizon remains **0.2.1**. No release in this checkpoint. Task file: `tasks/phase-12-xiaomi-mimo-token-plan.md`. Discovery record: `docs/research/xiaomi-mimo-coding-plan.md`.

## Goal

Add provider `mimo` (display name `Xiaomi MiMo`). It shows the remaining Xiaomi MiMo Token Plan credits as one ADR-0012 meter. The data comes from Xiaomi's official `GET /v1/platform/token_plan` endpoint, read with a user-supplied `tp-` key held only in KWallet. Requests go only to the explicitly configured region. MiMo is fetched only on a manual refresh.

## Entry Conditions

* Stage 4 / Phase 12 explicitly authorized in `TASKS.md` (2026-11-27).
* Baseline `220563f`: `python3 -m unittest discover -s tests` passes (61 tests, recorded by the Architect on 2026-11-27). The Coder re-records this and the QML suite counts before the first change.
* ADR-0009 permits this credential: no provider-owned local `tp-` key source is in scope. Decision 7 is excluded here, and the env variable is user-owned, not provider-owned. ADR-0009 item 2 allows a user-supplied secret in the OS credential store, and item 7 lets future providers reuse `secret_store` when similarly justified. **No new ADR is written.** ADR-0009 text is not edited.

## Owner Decisions (2026-11-27, binding for this phase)

1. **Plan labels.** Map the documented tiers and billing periods in `plan_code` to readable names. `lite` → `Lite`, `standard` → `Standard`, `pro` → `Pro`, `max` → `Max`. The suffix `:year` → ` · Annual` (so `lite:year` → `Lite · Annual`), and `:month` → ` · Monthly`. A bare known tier with no suffix maps to the tier name alone. No period is invented. An unknown tier, or a known tier with an unknown suffix, is **preserved**: the raw `plan_code` is trimmed, limited to printable characters and at most 64 characters, then shown as is. It is not dropped and not replaced. A missing or empty `plan_code` gives `plan: null`.
2. **Credentials: KWallet only, StepFun pattern.** `secret_store` entry `mimo/token-plan-key` (folder `Horizon`). Management through `ai-usage auth mimo set|status|clear` and a settings helper that reads the clipboard. Horizon never parses `~/.bashrc` or any shell profile. It never reads `XIAOMI_API_KEY`, `MIMO_API_KEY` or any other environment variable for the key. It writes no plaintext file and has no CLI flag that carries the key.
3. **Region.** Explicit configuration with values `sgp`, `cn` and `ams`, default `sgp`. Regions are never probed. HTTP 401 is `auth_unavailable` for the configured region, and no other host is tried.
4. **Period.** `resetAt` is Xiaomi's `period.end_at`, parsed as UTC and stored as ISO-8601 with `+00:00`. No monthly reset is invented for annual plans.
5. **Polling: manual refresh only.** Xiaomi's Token Plan subscription terms say the quota "is only available for use in programming tools". They prohibit "API calls for request behaviors in obvious non-coding scenarios … such as automated scripts and custom application backends" (`mimo.mi.com/static/docs/tokenplan/Token%20Plan/subscription.md`). That text does not clearly permit unattended polling, so **periodic or automatic MiMo fetching is out of this phase**. In `plasmoid/contents/ui/main.qml`, `refreshUsage()` is reached from these places:
   * the interval `refreshTimer`;
   * `Component.onCompleted`;
   * `onExpandedChanged` (popup open);
   * `onConfigChanged()` (configuration changes);
   * the Refresh button (`onClicked`, which also covers Space, and the Return and Enter key handlers);
   * the F5 `Shortcut`.

   The interval timer, startup, popup-open and config-change paths **must not** spawn the MiMo collector. Only the Refresh button (click, Space, Return, Enter), the F5 shortcut, and `ai-usage status mimo` run by hand may fetch. A MiMo result already in the model, or the existing stale cache fallback on a manual refresh, may still be shown. No new polling framework is added.
6. **One provider and one meter.** Provider id `mimo` in the existing `PROVIDERS` registry. Exactly one meter, label `Credits`. `remainingPercent = max(0, min(100, int(round(remaining_credits / total_credits * 100))))`, the same round-then-clamp style as StepFun's `_clamp_pct_from_left_rate`. `total_credits <= 0`, or a missing or invalid `quota`, gives an error payload with no meter and no 0% bar.
7. **No MiMo-Code credentials.** Never read `~/.local/share/mimocode/auth.json`, `~/.config/mimocode/` or any MiMo-Code credential or config file.

## Scope

1. **Provider module** `collector/providers/mimo.py`, class `MiMoProvider`, with `id = "mimo"` and `display_name = "Xiaomi MiMo"`:
   * `detect()` raises `auth_unavailable` when no KWallet key is stored.
   * `fetch_usage()` issues exactly one `GET https://token-plan-{region}.xiaomimimo.com/v1/platform/token_plan`. It sends the KWallet key as `Authorization: Bearer <key>` and builds the payload through `providers.contract.project_ok`.
   * A test-only base-URL override, `MIMO_API_BASE`, is allowed for offline fake-server tests, following the `CURSOR_API_BASE` precedent. It replaces the whole origin and never adds a region fallback.
2. **Registry and CLI wiring** in `collector/ai-usage`:
   * Add `"mimo": MiMoProvider` to `PROVIDERS`.
   * Add a non-secret `--region {sgp,cn,ams}` option, default `sgp`, to `status` and `auth`. It is used only by `mimo`, is validated by argparse choices, and is passed to `MiMoProvider(region=…)`.
   * Extend `cmd_auth` so `ai-usage auth mimo set|status|clear` follows the StepFun semantics:
     * `set` uses a non-echo TTY prompt, or one stdin line when not a TTY.
     * `set` and `status` print `working`, `auth_failed`, `unavailable` or `missing`. `clear` prints `cleared`.
     * The verify step is one usage GET to the configured region.
   * The StepFun branch is unchanged.
3. **Key shape check (no decoding).** Accept the key only when it is a non-empty string that starts with `tp-`, has no whitespace, and is 8–256 characters long. Reject anything else without echoing it.
4. **Status mapping.**
   * Missing key → `auth_unavailable`.
   * HTTP 401 → `auth_unavailable`, with a message that names the configured region and says to check the key and region.
   * Network failure (`URLError`, timeout), any non-200 status other than 401, invalid JSON, or an unexpected shape → `upstream_error`. This includes HTTP 403.
   * `total_credits <= 0`, or a missing `quota` or `total_credits` → `upstream_error`, with no meter.
   * No new status code is added. The existing `stale` fallback applies unchanged.
5. **Normalization.**
   * One meter: label `Credits`, the percent from decision 6, and `resetAt` from decision 4.
   * A missing or unparseable `period.end_at` omits `resetAt` and keeps the meter.
   * `plan` follows decision 1.
   * `remaining_credits` is clamped to `0..total_credits` before dividing. When `remaining_credits` is absent, use `max(0, total − used)` per Xiaomi's formula. When both are absent, return `upstream_error`.
6. **Install.** `scripts/install.sh` lists collector files explicitly, so add `providers/mimo.py` and `mimo_auth_helper.py` there. Make no other installer change.
7. **Cache.** `~/.cache/horizon/usage-mimo.json` through the existing `write_success`, with normalized fields only. The existing forbidden-key check applies.
8. **Settings helper.** `collector/mimo_auth_helper.py <status|clipboard|stdin|clear> <region>` mirrors `stepfun_auth_helper.py`:
   * The key comes from the clipboard or stdin, never from argv.
   * It clears the clipboard after a save, and prints only the fixed status words.
   * `stepfun_auth_helper.py` is not modified.
9. **Plasmoid.**
   * `plasmoid/contents/config/main.xml`: add `enableMimo` (Bool, default **false**) and `mimoRegion` (String, default `sgp`).
   * `configGeneral.qml`: add a MiMo enable checkbox, a region selector (`sgp`, `cn`, `ams`), and a MiMo credential section with Save key (clipboard), Check status and Clear, using the StepFun section's pattern. Do not change the StepFun section.
   * `main.qml`:
     * Add `mimo` to `allProviderIds`, `enabledProviderIds()` and `providerEnabled()`.
     * Pass `--region <mimoRegion>` only for `mimo` in the collector command.
     * Split the refresh entry points so that automatic callers skip `mimo` and manual callers (Refresh button, Return/Enter, F5) include it.
     * Before any MiMo fetch in the session, show the idle MiMo row with a manual-refresh hint.
     * The config-change handlers (including `mimoRegion` and `enableMimo`) never fetch MiMo.
   * A pure helper in `MeterIntake.js` (for example `refreshIds(enabledIds, manual)`) holds the manual-only rule so QML tests can check it.
   * The help text in the empty-providers message includes MiMo.
10. **Tests.** Offline only, with fabricated fixtures and a fake HTTP server. The tests never read the real environment key: `XIAOMI_API_KEY` and `MIMO_API_KEY` are removed from the test process environment, or proven unused. `secret_store` is stubbed. Coverage is listed in the task file.
11. **Writer step (after implementation, before Watcher).**
    * `docs/providers/mimo.md` (new).
    * `docs/provider-contract.md`: registry block, provider list, `--region` note.
    * `docs/security.md`: the KWallet entry, the never-commit list, the no-env/no-bashrc/no-MiMo-Code rule, and the manual-refresh rule with its Xiaomi citation.
    * The README `Supported providers` row.
    * `docs/research/xiaomi-mimo-coding-plan.md` stays a research record, except for the single authorization status line.

## Explicit Exclusions

* The console or dashboard endpoints (`platform.xiaomimimo.com/api/v1/tokenPlan/*`, `/api/v1/balance`), browser cookies, Xiaomi Account SSO, login, OAuth, device flows, and token minting.
* Any Xiaomi host other than `token-plan-{configured region}.xiaomimimo.com`. Region probing, region fallback, and retrying another host after a 401.
* Inference calls, any request that consumes credits, and the Finance balance, daily consumption or bill endpoints. Absolute credit counts, spend or cash in the payload.
* Reading the key from environment variables, `~/.bashrc` or any shell profile, a plaintext file, MiMo-Code's `auth.json` or config, or a CLI flag.
* Automatic, periodic, startup, popup-open or config-change MiMo fetches. A new polling or scheduling framework. A per-provider interval setting.
* Team-edition seats, multiple keys, multiple accounts or regions at once, and per-model breakdowns.
* A new ADR, edits to ADR-0009, ADR-0012 or any other accepted decision, and any change to `docs/usage-schema.md`, the meter schema, the status vocabulary, or the cached field set.
* Changes to Codex, Cursor, StepFun or Claude behavior. The only exception is the shared refresh path in `main.qml`, which now skips MiMo on automatic triggers. Changes to `stepfun_auth_helper.py`.
* A general authentication framework, shared credential layer, or refactor of `cmd_auth` beyond adding the `mimo` branch.
* `VERSION`, `plasmoid/metadata.json` `KPlugin.Version`, the README version line, CHANGELOG release entries, tags, GitHub releases, and pushing to `main` during implementation.
* Creating `docs/handoffs/phase-12.md` before owner acceptance. Editing accepted task files or handoffs.

## Acceptance Criteria

1. **Payload.** With a fake `MIMO_API_BASE` server and a stubbed KWallet key, `ai-usage status mimo --json --no-cache --region sgp` returns `status=ok` with exactly one meter:
   * label `Credits`;
   * `remainingPercent` equal to the decision-6 formula;
   * `resetAt` equal to `period.end_at` as ISO-8601 with `+00:00`.

   The compatibility fields equal the projections from `project_ok`.
2. **Plan labels.** `lite` → `Lite`, `lite:year` → `Lite · Annual`, `pro:month` → `Pro · Monthly`. An unknown code (for example `ultra:quarter` or `lite:weird`) is preserved as its sanitized raw string. A missing or empty code gives `null`. A label is never invented.
3. **Period.** Fixtures for a monthly plan (about 1 month) and an annual plan (about 1 year) each produce `resetAt` equal to their own `end_at`, with no monthly reset synthesized for the annual plan. A malformed `end_at` omits `resetAt`.
4. **Credentials.**
   * A missing KWallet key gives `auth_unavailable` from `detect()` and from `status`, with zero HTTP requests.
   * Setting `XIAOMI_API_KEY` or `MIMO_API_KEY` in the environment has no effect.
   * No code path opens `~/.bashrc`, a shell profile, or any `mimocode` path. This is checked by a test and by `git grep`.
5. **Region.**
   * The request goes to the configured region host only (`sgp` by default, and `cn` and `ams` when configured).
   * A 401 gives `auth_unavailable` after exactly **one** request, with no request to any other region.
   * An invalid region value is rejected by argparse.
6. **Failure states.** A network error, HTTP 403 or 500, invalid JSON, a JSON array, `total_credits` of 0 or negative, and a missing `quota` each give `upstream_error`. A cold cache produces no `meters` key. A warm cache gives `stale` through the existing path.
7. **Manual-only refresh.** QML or `MeterIntake.js` tests show:
   * the automatic path (timer, startup, popup open, config change) never includes `mimo`;
   * the manual path (Refresh button click, Space, Return, Enter, F5) includes `mimo` when it is enabled;
   * the other four providers are refreshed exactly as before on every path.
8. **Secret audit.**
   * The fixture key never appears in stdout, stderr, `--json`, error messages, the cache file, logs, docs, or the argv of any process Horizon spawns (helper, collector, QML command).
   * The `docs/security.md` secret-check procedure finds no real key.
   * Fixtures use obviously fake values such as `tp-fake-fixture-key`.
9. **Settings.** The settings page shows the MiMo enable checkbox, the region selector and the credential section. Save key, Check status and Clear map to the fixed status words. Live verification uses the configured region only.
10. **No regression.**
    * All pre-existing Python and QML tests pass, plus the new ones.
    * Codex, Cursor, StepFun and Claude still return their accepted results through `ai-usage status <id> --json`.
    * The StepFun auth CLI and helper behave as before.
11. **Live check (only if a key is configured in KWallet).** One manual `ai-usage status mimo --json --region <configured>` run is recorded in sanitized form only: the status, meter label, percent bucket, whether `resetAt` is present, and the plan label. No key, email or user id is recorded.
12. **Scope fence.**
    * `git diff 220563f --stat` touches only:
      * `collector/providers/mimo.py`, `collector/mimo_auth_helper.py`, `collector/ai-usage`;
      * `plasmoid/contents/config/main.xml`, `plasmoid/contents/ui/configGeneral.qml`, `plasmoid/contents/ui/main.qml`, `plasmoid/contents/ui/MeterIntake.js`;
      * `scripts/install.sh`, which must install `providers/mimo.py` and `mimo_auth_helper.py` because it lists collector files explicitly; `scripts/uninstall.sh` and `scripts/upgrade.sh` do not list collector files and stay unchanged;
      * `tests/`;
      * the Writer docs, the research note status line, and the Factory files (`PHASES.md`, `TASKS.md`, `tasks/`).
    * `VERSION`, `plasmoid/metadata.json`, `decisions/`, `docs/handoffs/`, `docs/usage-schema.md`, the other provider modules and `collector/stepfun_auth_helper.py` show no diff.
13. **Deferred Work.** Out-of-scope discoveries are recorded in the task file.
14. **Watcher, then stop.** Independent Watcher verification returns PASS, then work stops for explicit owner acceptance.

## Handoff Contract

* Record direct evidence for every task and criterion in `tasks/phase-12-xiaomi-mimo-token-plan.md`. Watcher reports go under the gitignored `reports/` as `stage-4-phase-12-watcher-<attempt>.md`.
* Independent Watcher PASS, then explicit owner acceptance.
* Only after acceptance, write `docs/handoffs/phase-12.md` and produce the checkpoint.
* Any release (version bump, tag, GitHub release) is a separate, explicitly approved owner action.
* STOP. Do not start new work or a new phase automatically.
