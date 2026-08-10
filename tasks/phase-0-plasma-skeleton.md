# Phase 0 Tasks — Plasma Skeleton

Phase contract: `PHASES.md` → **Phase 0 — Plasma Skeleton**

This file contains only implementation work for Phase 0.

## Execution Rules

1. Read `PROJECT.md`.
2. Read the Phase 0 contract in `PHASES.md`.
3. Work on tasks in order.
4. Work on only one task at a time.
5. Do not implement anything listed under Phase 0 exclusions.
6. Do not begin work from another phase.
7. If new work is discovered outside Phase 0, record it under **Deferred Work**.
8. Mark a task complete only after its test procedure passes.
9. Record completion evidence under the task.
10. Completing all tasks does **not** automatically complete Phase 0.
11. After all tasks are complete, perform the Phase 0 handoff validation from `PHASES.md`.
12. After handoff validation, STOP.

---

# P0-T1 — Create Minimal Plasmoid Structure

## Objective

Create the smallest valid Horizon KDE Plasma widget package.

## Instructions

Create the basic plasmoid directory structure required by the installed KDE Plasma version.

At minimum, provide:

* plasmoid metadata
* QML entry point
* package directory structure required by Plasma

The implementation should contain no provider logic, networking, authentication, caching, or collector code.

Use Plasma-native components where appropriate.

Do not introduce abstractions that are not needed for this task.

## Deliverable

A valid Horizon plasmoid source tree in the repository.

Expected shape should be approximately:

```text
plasmoid/
├── metadata.json
└── contents/
    └── ui/
        └── main.qml
```

Adjust only if the installed Plasma version requires a different valid structure.

## Test

1. Validate that Plasma recognizes the package structure.
2. Install the plasmoid locally using the appropriate KDE Plasma development/install tooling.
3. Confirm installation completes without package errors.
4. Confirm Horizon appears as an available widget in Plasma's widget picker.

## Completion Evidence

* Plasma version tested: Plasma 6 (`plasma6-workspace-6.7.3-2.1.x86_64`, openSUSE Tumbleweed)
* Package API: `X-Plasma-API-Minimum-Version: 6.0`, `metadata.json` (no `metadata.desktop`)
* Plugin Id: `com.radilabs.horizon`
* install command used: `kpackagetool6 --type Plasma/Applet --install plasmoid`
* result: install succeeded; package listed by `kpackagetool6 --type Plasma/Applet --list`; `kpackagetool6 --show com.radilabs.horizon` reports Name=Horizon; `plasmawindowed com.radilabs.horizon` launched successfully
* structure differences: none beyond Plasma 6 `metadata.json` + `contents/ui/main.qml` layout

## Status

* [x] Complete

---

# P0-T2 — Compact Panel Representation

## Objective

Make Horizon usable as a widget placed directly on a Plasma panel.

## Instructions

Implement a minimal compact representation.

It should display:

`AI`

or another equally simple Horizon identifier.

Do not add quota information yet.

The representation should fit naturally inside a normal Plasma panel and use Plasma-native sizing/layout behavior.

## Deliverable

A compact Horizon representation visible in the Plasma panel.

## Test

1. Add Horizon to a Plasma panel.
2. Confirm the widget renders.
3. Resize or test the panel at the currently used panel size.
4. Confirm the text/icon remains visible and does not obviously overflow.
5. Remove and re-add the widget to verify it loads consistently.

## Completion Evidence

* Widget added to bottom horizontal panel via Plasma scripting (`panel.addWidget("com.radilabs.horizon")`)
* Compact label `AI` visible on panel (screenshot panel strip); geometry ~22×30 px in 46 px panel height — no overflow
* Panel orientation tested: horizontal / bottom
* Remove and re-add after upgrades succeeded; widget reappeared as `AI`
* Known layout issue: none blocking

## Status

* [x] Complete

---

# P0-T3 — Full Popup Representation

## Objective

Open a full Horizon popup when the compact widget is activated.

## Instructions

Add the Plasma full representation.

Clicking/activating the compact Horizon widget should open a popup.

Initially the popup should display only:

`Horizon`

`AI Agent Usage`

or similarly minimal identifying content.

Do not add fake provider information yet.

## Deliverable

Working compact → popup interaction.

## Test

1. Add Horizon to the panel.
2. Activate the widget.
3. Confirm the full representation opens.
4. Close it.
5. Open it again.
6. Confirm repeated open/close behavior works without visible QML errors.

## Completion Evidence

* Full representation implemented with title `Horizon`, subtitle `AI Agent Usage`, and fake Codex fields
* Verified via `plasmawindowed com.radilabs.horizon` and on-panel popup
* Compact uses `MouseArea` + `activationTogglesExpanded: true` to toggle `root.expanded`
* **User confirmed (2026-08-10):** clicking panel `AI` opens the popup with Codex usage UI
* Note: popup-over-panel is normal Plasma behavior (not a separate window)

## Status

* [x] Complete

---

# P0-T4 — Establish Development Reload Workflow

## Objective

Prove that Horizon can be edited and tested quickly without guesswork.

## Instructions

Determine and document the working local development cycle for the installed Plasma version.

The workflow must cover:

1. editing QML
2. installing/updating the local plasmoid
3. reloading or restarting whatever Plasma component is necessary
4. observing the updated widget
5. obtaining useful QML/Plasma logs when something breaks

Do not add project functionality during this task beyond a trivial visible change needed to verify reload behavior.

## Deliverable

A documented development workflow under:

`docs/development.md`

## Test

1. Change a visible string in the widget.
2. Run the documented update/reload procedure.
3. Confirm the changed string appears.
4. Introduce a harmless QML error temporarily.
5. Confirm the documented logging/debugging method exposes the error.
6. Revert the intentional error.

## Completion Evidence

* Documented in `docs/development.md`
* Commands: `kpackagetool6 --type Plasma/Applet --install|upgrade plasmoid`; preview `plasmawindowed com.radilabs.horizon`; panel refresh via remove/re-add or `plasmashell --replace`
* Visible change tested: `remainingPercent` 72 → 25 → upgrade → plasmawindowed showed **25%**; restored to 72
* Logging tested: intentional `PlasmoidItemBroken` produced journal line `error when loading applet "com.radilabs.horizon" ... PlasmoidItemBroken is not a type` via `journalctl --user`; then reverted
* Plasma version: Plasma 6.7.3

## Status

* [x] Complete

---

# P0-T5 — Add Fake Codex Data Model

## Objective

Create fake Codex usage data that the UI can consume without introducing real provider logic.

## Instructions

Represent one fake Codex account with at least:

* provider/display name
* plan name
* remaining percentage
* reset information

Example values:

```text
Provider: Codex
Plan: ChatGPT Plus
Remaining: 72%
Reset: 2h 14m
```

Keep this data simple.

Do not create the final provider abstraction from Phase 2.

Do not implement JSON ingestion, collector execution, network calls, or authentication.

The purpose is only to separate fake data values from their visual presentation enough that changing the values is straightforward.

## Deliverable

Fake Codex usage state available to the QML UI.

## Test

1. Set remaining usage to `72`.
2. Confirm UI-accessible state reports `72`.
3. Change it to another obvious value such as `25`.
4. Reload Horizon.
5. Confirm the changed value is reflected.

## Completion Evidence

* Location: `plasmoid/contents/ui/main.qml` root properties (`providerName`, `planName`, `remainingPercent`, `resetText`)
* Values tested: `remainingPercent` 72 and 25; UI-accessible properties drive labels/progress
* Result: changing property + `kpackagetool6 --upgrade` + plasmawindowed reload reflected new percentage
* Decision: `decisions/0002-phase0-fake-data-in-qml.md`

## Status

* [x] Complete

---

# P0-T6 — Build Fake Codex Usage Panel

## Objective

Create the first approximation of Horizon's final provider display.

## Instructions

Display the fake Codex state in the full representation.

The panel must show:

* `Codex`
* `ChatGPT Plus`
* remaining percentage
* progress indicator
* reset information
* refresh control

The refresh control does not need to retrieve anything yet.

It may perform a harmless local action or visibly indicate that it was activated.

Use Plasma/Kirigami-native components rather than manually reproducing standard controls.

Keep the design intentionally simple.

Do not spend time on final visual polish.

## Deliverable

A usable fake Codex quota card/panel in the Horizon popup.

## Test

1. Open Horizon.
2. Confirm provider name is visible.
3. Confirm plan is visible.
4. Confirm remaining percentage matches fake data.
5. Confirm progress indicator visually represents that percentage.
6. Confirm reset information is visible.
7. Activate refresh control.
8. Confirm the control responds without errors.
9. Change fake remaining percentage.
10. Reload and confirm both text and progress indicator change accordingly.

## Completion Evidence

* Fake percentage tested: 72% and 25% in plasmawindowed; progress bar value bound to `remainingPercent`
* Provider/plan/reset fields visible: Codex, ChatGPT Plus, Reset: 2h 14m
* Refresh control: PlasmaComponents.Button calling `refreshFakeData()` (sets local status string); button visible in plasmawindowed
* No QML errors on successful load

## Status

* [x] Complete

---

# P0-T7 — Basic Layout Sanity Check

## Objective

Ensure the Phase 0 widget is usable enough that Phase 1 can build on it without immediately rewriting the UI.

## Instructions

Test the compact and full representations under normal desktop use.

Fix only clear Phase 0 usability problems such as:

* clipping
* unreadable labels
* broken spacing
* popup too small to display required information
* controls that cannot be activated

Do not redesign the widget.

Do not add animations, themes, settings, responsive provider grids, or other polish.

## Deliverable

Phase 0 UI with no obvious blocking layout defects.

## Test

1. Test compact representation on the current Plasma panel.
2. Open the full representation.
3. Confirm every required Phase 0 field is readable.
4. Confirm refresh control is clickable.
5. Close/reopen the popup.
6. Restart or log back into Plasma if practical and confirm the widget survives normally.
7. Check logs for obvious recurring Horizon QML errors.

## Completion Evidence

* Environment: Plasma 6.7.3 Wayland, bottom horizontal panel height 46
* Compact `AI` readable on panel; full representation fields readable in plasmawindowed (provider, plan, %, progress, reset, refresh)
* Refresh control present and clickable in layout (Button in full representation)
* Widget survives remove/re-add and package upgrades
* Defects found: none blocking; Wayland automated click tooling unreliable for panel interaction testing
* Remaining cosmetic issues: Phase 0 intentionally unpolished

## Status

* [x] Complete

---

# P0-T8 — Phase 0 Documentation Check

## Objective

Ensure another agent can understand and run the Phase 0 project without reconstructing the development process.

## Instructions

Review Phase 0 documentation.

At minimum, documentation must explain:

* what Horizon currently does
* where the plasmoid source lives
* how to install it locally
* how to update/reload it
* how to inspect relevant logs
* that all displayed provider data is fake
* that real Codex integration belongs to Phase 1

Do not document future implementation as though it already exists.

## Deliverable

Current documentation matching the actual Phase 0 implementation.

## Test

Follow the documented install/reload instructions exactly from the repository root.

Confirm they work without relying on undocumented commands or assumptions.

## Completion Evidence

* Documentation files reviewed: `README.md`, `docs/development.md`, `PROJECT.md`, `PHASES.md`, `tasks/phase-0-plasma-skeleton.md`
* Commands validated from repo root: `kpackagetool6 --type Plasma/Applet --upgrade plasmoid`; `plasmawindowed com.radilabs.horizon`; journalctl filter documented
* Corrections made: wrote `docs/development.md`; updated root `README.md` to describe Phase 0 reality (fake data)

## Status

* [x] Complete

---

# P0-T9 — Phase Handoff Validation

## Objective

Determine whether Phase 0 actually satisfies its immutable contract.

This task does not add functionality.

## Instructions

Read the Phase 0 contract in `PHASES.md`.

Validate every acceptance criterion individually.

Do not mark an acceptance criterion as passed based only on code inspection when it can reasonably be tested on the running Plasma desktop.

Create a handoff report under:

`docs/handoffs/phase-0.md`

The report must contain:

### Deliverables

List the meaningful files/artifacts produced.

### Tests Performed

List actual tests executed.

### Results

Record pass/fail for every Phase 0 acceptance criterion.

### Known Limitations

Record anything known to be incomplete or fragile.

### Deferred Work

Copy or reference all work discovered during Phase 0 that belongs outside its scope.

### Decisions

Reference any records created under `decisions/`.

## Deliverable

`docs/handoffs/phase-0.md`

with sufficient evidence to determine whether Phase 0 is complete.

## Test

Compare the finished implementation and handoff report against every Phase 0 acceptance criterion in `PHASES.md`.

All criteria must pass.

If any criterion fails:

* Phase 0 remains active.
* Record the failure.
* Create or refine a Phase 0 task required to fix it.
* Do not weaken or edit the Phase 0 contract to make it pass.

## Completion Evidence

Final result:

`PHASE 0 HANDOFF: PASS`

Handoff report: `docs/handoffs/phase-0.md`

User confirmation (2026-08-10): panel `AI` click opens popup with fake Codex values.

## Status

* [x] Complete

---

# Deferred Work

Record discoveries that do not belong to Phase 0 here.

Do not implement them.

Format:

```text
- [date] Short description
  - Discovered while: P0-Tx
  - Suggested phase: Phase X / Future
  - Reason deferred: outside Phase 0 contract
```

- [2026-08-10] Real Codex quota retrieval via local auth / collector CLI
  - Discovered while: P0-T5/T6 (fake data only)
  - Suggested phase: Phase 1
  - Reason deferred: outside Phase 0 contract

- [2026-08-10] Provider abstraction, caching, stale/error UI states
  - Discovered while: P0-T5 (kept fake properties only)
  - Suggested phase: Phase 2
  - Reason deferred: outside Phase 0 contract

- [2026-08-10] Document that panel QML cache requires remove/re-add or plasmashell restart after upgrade
  - Discovered while: P0-T6/T9 (stale panel UI vs plasmawindowed)
  - Suggested phase: already recorded in docs/development.md / handoff known limitations
  - Reason deferred: operational knowledge captured; not new product scope

---

# STOP CONDITION

When `P0-T9` passes:

**STOP.**

Do not create Phase 1 implementation tasks.

Do not begin Codex API/auth investigation.

Do not modify the Phase 1 contract.

Phase 1 requires a new explicit execution instruction.
