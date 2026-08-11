# Phase 5 Tasks — Operational Polish

Phase contract: `PHASES.md` → **Phase 5 — Operational Polish**

Phase 4 handoff must be PASS before execution.

## Goal

Make Horizon pleasant and reliable enough for normal daily Plasma use without expanding the core product scope.

This phase is about operating the existing three-provider product well.

It is not a new architecture phase.

---

# Selected Phase 5 Scope

Implement only:

1. Provider enable/disable configuration
2. Periodic refresh with configurable interval
3. Refresh concurrency protection
4. Better compact-panel summary
5. Better stale/error/auth indicators
6. StepFun credential management through settings using existing KWallet storage
7. Installation/upgrade/uninstall improvements
8. User-facing README and provider setup documentation
9. Basic v0.1.0 release/versioning process

Low-quota notifications are optional and may be added only after the above is complete and stable.

---

# Explicit Non-Goals

Do not implement:

* new providers
* generic provider plugins
* general account management
* StepFun username/password login
* browser cookie import
* generic Oasis authentication framework
* OAuth frameworks
* subscription management
* usage history/graphs
* analytics
* telemetry
* cloud synchronization
* arbitrary dashboard customization
* long-running daemon
* unrelated architecture refactors

The existing Codex, Cursor, and StepFun integrations remain the product boundary for Phase 5.

---

# P5-T0 — Baseline and Phase 4 Regression

## Objective

Establish a known-good Phase 5 starting point.

## Instructions

Read:

* `PROJECT.md`
* Phase 5 in `PHASES.md`
* `docs/handoffs/phase-4.md`
* provider contract/schema/cache/security docs
* current provider ADRs
* current QML/configuration structure
* current installation/development docs

Verify:

```bash
ai-usage status codex --json
ai-usage status cursor --json
ai-usage status stepfun --json
```

Verify existing plasmoid displays all three.

No implementation before baseline is recorded.

## Status

* [x] Complete

---

# P5-T1 — Provider Enable / Disable

## Objective

Allow users to choose which existing providers Horizon queries and displays.

## Providers

Exactly:

* Codex
* Cursor
* StepFun

No dynamic provider/plugin system.

## Behavior

Settings should expose:

```text
Providers

[x] Codex
[x] Cursor
[x] StepFun
```

Configuration must persist through normal Plasma configuration.

Disabled providers:

* are not queried
* do not participate in refresh
* do not display stale/errors
* do not appear in compact summary
* remain configured; disabling does not delete credentials

At least one enabled provider is preferred, but Horizon should behave sensibly if all are disabled.

## Initial Defaults

For existing installations, preserve current behavior: all existing priority providers remain enabled.

Do not silently disable a provider because authentication temporarily fails.

Auto-detection may be considered only for first-run defaults if simple and reliable.

Do not build ongoing provider auto-management.

## Test

* disable each provider independently
* disable two providers
* disable all providers
* re-enable provider
* restart Plasma/widget and verify persistence
* verify disabled provider generates no collector request
* verify failures remain isolated

## Status

* [x] Complete

---

# P5-T2 — Periodic Refresh

## Objective

Keep quota information reasonably current during normal Plasma sessions.

## Behavior

Add periodic refresh.

Suggested intervals:

```text
5 minutes
10 minutes
15 minutes
30 minutes
60 minutes
```

Default:

```text
15 minutes
```

Persist through Plasma configuration.

Manual Refresh remains available.

Only enabled providers refresh.

No long-running daemon.

The plasmoid itself owns scheduling.

## Important

Do not hammer unofficial upstream APIs.

Do not refresh every minute.

Do not refresh disabled providers.

## Test

* default interval
* each configured interval
* configuration persistence
* manual refresh still works
* provider isolation
* disabled provider not refreshed

## Status

* [x] Complete

---

# P5-T3 — Prevent Overlapping Refreshes

## Objective

Guarantee the Phase 5 acceptance criterion that refresh behavior cannot create overlapping provider requests.

## Behavior

If a provider request is already running:

* do not start another request for that provider
* manual refresh must not create duplicates
* timer refresh must not overlap manual refresh
* opening popup must not create duplicate refresh work

Providers remain independent.

Example:

```text
Codex running
Cursor idle
StepFun idle
```

Cursor/StepFun may refresh normally; Codex must not receive a second concurrent request.

Avoid introducing a global lock that unnecessarily serializes all providers.

## Test

Trigger:

* timer + manual refresh
* repeated manual clicks
* popup-open + timer
* slow/failing provider while other providers work

Record evidence that each provider has at most one in-flight request.

## Status

* [x] Complete

---

# P5-T4 — Better Compact Panel

## Objective

Make the panel useful without turning it into a dashboard.

## Preferred Design

Compact panel shows a single meaningful value representing the most constrained enabled provider quota.

Concept:

```text
AI 72%
```

The value should be the lowest meaningful current remaining percentage among enabled providers.

Tooltip provides the provider summary:

```text
Codex      94%
Cursor     98% / 100%
StepFun    72% / 61%
```

Do not expose provider-specific upstream fields.

Do not overcrowd the panel with three full provider readouts.

If all providers are unavailable, show a neutral/error state rather than a misleading percentage.

## Test

* three providers
* one provider
* provider disabled
* one provider stale
* provider auth failure
* all providers unavailable

## Status

* [x] Complete

---

# P5-T5 — Better Stale / Error / Auth UX

## Objective

Make failures understandable without making Horizon noisy.

## Desired States

### Fresh

Normal presentation.

### Stale

Show cached data plus clear indication:

```text
Cached · 18m old
```

or equivalent.

### Authentication unavailable

Show:

```text
Needs authentication
```

Provider-local guidance may be available in details/settings.

### Upstream unavailable

Show:

```text
Unavailable
```

If stale cache exists:

```text
Unavailable · cached 18m ago
```

### Collector/provider unavailable

Use a simple actionable label.

Avoid dumping raw exception text into normal UI.

Detailed diagnostics may remain available through CLI/docs.

## Important

Error state remains provider-local.

One broken provider must never visually imply Horizon itself is broken.

## Test

All normalized statuses:

* `ok`
* `stale`
* `auth_unavailable`
* `provider_unavailable`
* `upstream_error`
* `collector_error`

## Status

* [x] Complete

---

# P5-T6 — StepFun Credential Settings UX

## Objective

Make StepFun usable without requiring users to know the collector CLI.

Reuse the existing Phase 4 KWallet implementation.

Do not redesign authentication.

## Settings Behavior

StepFun section should expose credential state only:

```text
StepFun
Status: Configured

[Replace token]
[Remove token]
```

If missing:

```text
StepFun
Status: Not configured

[Set token]
```

Token input must:

* use password/secret input
* never display existing token
* never expose token in QML state longer than necessary
* write through existing secure secret-store path
* never persist in Plasma configuration
* never log token
* never add token to command arguments

Prefer invoking a narrow collector credential operation rather than teaching QML direct KWallet internals.

Existing CLI remains supported:

```bash
ai-usage auth stepfun set
ai-usage auth stepfun status
ai-usage auth stepfun clear
```

## Explicit Exclusions

Do not:

* store StepFun username/password
* implement StepFun login
* refresh Oasis tokens
* import browser cookies
* inspect Zen/browser storage automatically
* create generic Oasis UI
* expose token/device JWT contents

Oasis remains StepFun-specific.

## Test

Lifecycle:

```text
missing
→ configure
→ live usage
→ replace
→ live usage
→ remove
→ missing
```

Run repository/cache/log secret audit afterward.

## Status

* [x] Complete

---

# P5-T7 — Configuration Persistence

## Objective

Validate all Phase 5 configuration behaves like a normal Plasma widget.

Persist:

* provider enabled states
* refresh interval
* notification configuration only if notifications are implemented

Do not persist secrets.

## Test

Verify persistence after:

* widget close/open
* Plasma restart/reload
* plasmoid upgrade
* normal logout/login where practical

Verify StepFun token remains in KWallet independently of widget settings.

## Status

* [x] Complete

---

# P5-T8 — Installation / Upgrade / Uninstall

## Objective

Move Horizon from development checkout instructions to a usable local installation.

## Requirements

Provide a simple installation method that installs:

* collector
* Python support files
* Plasma widget

Collector must live in a stable location, not depend on a symlink into the Git checkout.

Provide:

```text
install
upgrade
uninstall
```

The installer should detect or clearly document required dependencies.

Likely dependencies include:

* Plasma 6
* Python 3
* Python D-Bus bindings / KWallet access
* provider applications/auth where appropriate

Do not bundle or copy provider credentials.

Uninstall should not silently delete KWallet credentials unless explicitly documented/requested.

## Test

Perform a clean-install test from a fresh directory/location:

1. install
2. run collector
3. configure StepFun if required
4. add widget
5. verify three providers
6. upgrade
7. verify settings/cache/credentials survive
8. uninstall
9. verify installed files removed

## Status

* [x] Complete

---

# P5-T9 — User-Facing README

## Objective

Replace development-era README with documentation suitable for somebody discovering Horizon.

README should explain:

## What Horizon is

KDE Plasma widget displaying remaining AI coding-agent quotas.

## Supported providers

* OpenAI Codex
* Cursor
* StepFun Step Plan

## Screens / behavior

Brief explanation of compact panel and expanded provider view.

## Installation

Actual installation procedure.

## Authentication

### Codex

Reuse existing Codex authentication.

### Cursor

Reuse local Cursor session read-only.

### StepFun

User supplies Oasis token.

Stored only in KWallet.

No StepFun password/login automation.

## Configuration

* provider enable/disable
* refresh interval
* notifications if implemented

## Security

Short clear explanation:

* credentials reused where possible
* StepFun token stored in OS credential store
* usage cache contains normalized non-secret data only
* no telemetry

## Known limitations

Make unofficial/private upstream API dependencies explicit.

Link detailed provider docs.

Remove outdated Phase 2 language.

## Status

* [x] Complete

---

# P5-T10 — Packaging and Versioning

## Objective

Prepare Horizon as a usable first release.

Current target:

```text
0.1.0
```

Ensure version is consistently represented where necessary.

Add minimal release documentation/process:

* version source
* how package/install artifact is produced
* required validation
* release notes/changelog convention
* Git tag convention

Do not create a complex release pipeline.

A basic reproducible manual release process is enough.

## Test

Build/install from release artifact or clean tagged tree.

Verify metadata reports expected version.

## Status

* [x] Complete

---

# P5-T11 — Optional Low-Quota Notifications

## Objective

Only implement if P5-T1 through P5-T10 are stable and notifications still provide meaningful value.

This task may be deferred without failing Phase 5.

## Behavior

Notifications must be:

* opt-in or conservatively configured
* threshold based
* rate-limited
* provider/window aware
* not repeated every refresh

Example:

```text
StepFun Weekly Usage
9% remaining
```

Suggested thresholds may include:

```text
20%
10%
5%
```

But keep initial UX simple.

A notification must not repeatedly fire for the same threshold during the same quota window.

Notifications must not contain secrets or raw upstream data.

## Test

* threshold crossing
* repeated refresh does not repeat
* reset allows future notification
* provider disabled
* notifications disabled
* multiple quota windows

## Status

* [ ] Complete
* [x] Deferred

---

# P5-T12 — Three-Provider Regression and Normal Session Test

## Objective

Prove Horizon works as a daily Plasma widget.

## Test

Run with Codex, Cursor, and StepFun enabled.

Verify:

* startup
* automatic refresh
* manual refresh
* compact display
* popup
* settings persistence
* provider toggles
* stale behavior
* auth failure
* upstream failure
* StepFun token lifecycle
* no overlapping requests
* logout/login or Plasma reload
* installation from clean state

Run secret audit again.

## Status

* [x] Complete

---

# P5-T13 — Phase 5 Handoff

## Objective

Validate against the immutable Phase 5 contract.

Create:

`docs/handoffs/phase-5.md`

Record exact acceptance results:

1. Horizon works reliably during normal Plasma sessions.
2. Refresh behavior does not create overlapping provider requests.
3. Provider failures remain isolated.
4. User-visible stale/error states are understandable.
5. Configuration introduced in this phase persists correctly.
6. Notifications, if implemented, are rate-limited and useful.
7. Installation and usage documentation is sufficient for a clean installation.
8. Core three-provider functionality remains intact.

Document:

* implemented polish tasks
* tests
* installation verification
* operating documentation
* unofficial upstream/API limitations
* security audit
* deferred items
* release/version state

Remaining ideas must be clearly marked future work.

Do not silently expand Phase 5 to include them.

Record exactly:

```text
PHASE 5 HANDOFF: PASS
```

or:

```text
PHASE 5 HANDOFF: FAIL
```

If PASS:

STOP.

Do not begin another provider or capability phase.

---

# Deferred / Future Work

Possible future ideas, not Phase 5 requirements:

* additional providers
* usage history
* graphs
* provider ordering/custom layouts
* browser credential import
* generalized OAuth/Oasis support
* account management
* richer notification policy
* release automation
* distribution through KDE Store/package repositories

These require future explicit decisions/contracts.

---

# STOP CONDITION

When Phase 5 handoff passes:

**STOP.**

The repository should represent a usable Horizon v0.1.0.

Any additional provider or significant capability requires a new phase contract.
