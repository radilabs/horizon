# Stage 2 / Phase 9 — Compact UX and Release Polish

**Status: ACCEPTED** (2026-10-09). This file is historical execution evidence. It is **not** executable.

Accepted snapshot: `docs/handoffs/phase-9.md`. The owner approved Horizon **0.2.0** with this acceptance.

**Authority:** `PHASES.md` Stage 2 / Phase 9 (the immutable contract), `TASKS.md`  
**Previous accepted snapshot:** `docs/handoffs/phase-8.md`  
**Information contract:** ADR-0012 (`decisions/0012-ordered-usage-meters.md`), `docs/usage-schema.md`  
**Branch:** `phase-9-compact-ux-release-polish` (from `0a06644`)  
**Worktree:** `/home/naorw/.t3/worktrees/horizon/phase-6.5-claude-usage`

## Goal

Make the compact summary, tooltip, popup height and Refresh action honest and readable for 1..N ordered meters. Bring the screenshots, docs, changelog and reload/upgrade guidance up to date. Produce release-readiness evidence and a version recommendation without releasing.

## Baseline (`0a06644`, `plasmoid/contents/ui/main.qml`)

- `lowestQuotaPercent()` takes the minimum of `remainingPercent` and every `breakdownJson` row. `updateCompactSummary()` then writes `AI <min>%`. With Cursor Other Models at 0, the panel shows `AI 0%` even when every other meter is high. Phase 8 recorded exactly that.
- `breakdownJson` is still built the pre-Phase-8 way: `line.resetAt || obj.resetAt`, and the primary/secondary fallback copies the payload reset onto the second row. Only compact and tooltip read it.
- Tooltip: one line per provider, `name  <primary>% / <secondary>%` plus `(cached)`, or a status label. No meter labels and no `error` text.
- Popup: `implicitWidth` `gridUnit*20`, `implicitHeight` `*32`, minimum width/height `*16`, maximum height `*36`. A `ScrollView` fills the middle. A Refresh button plus an "Updating…" label are pinned under a separator at the bottom.
- The popup reads meters through `MeterIntake.js`: `meters`, then `breakdown`, then primary/secondary. A reset is shown only from that meter's own `resetAt`. This is accepted Phase 8 behavior and must not regress.

## Rules to implement (from the contract)

**Compact summary.** Read from the `MeterIntake.js` intake, not from `breakdownJson`. Only `ok`/`stale` providers with quota contribute.

| Contributing meters | Compact text |
|---|---|
| none at 0 | `AI <n>%`, where n is the lowest remaining |
| some at 0, some above 0 | `AI <n>% · <k> at 0%`, where n is the lowest remaining among meters above 0 and k is the count at 0 |
| all at 0 | `AI 0%` |
| no contributing provider | existing `AI` (none enabled) / `AI !` (auth) / `AI —` (error) / `AI …` (loading) |

The rule is provider-neutral. Do not treat any provider's meters as alternatives or as joint limits.

**Tooltip.** One block per enabled provider, read from the same meter intake.

- First a provider line: the name, then ` · <plan>` when the plan is known, then ` (cached <age>)` when stale.
- Then one indented line per meter: `<label> <n>%`, in payload order.
- A failing provider shows `<name>  <status label>`, with the user-safe `error` text on one line and shortened if long.
- No resets, no Primary/Secondary, no invented plan.

**Popup height.**

- Preferred height follows content.
- Minimum height: `gridUnit * 12`.
- Maximum height: the smaller of `gridUnit * 40` and about 80% of the available screen height.
- The `ScrollView` scrolls beyond the maximum.
- Width stays as in Phase 8.
- No pixel constants.

**Refresh.**

- A `view-refresh` tool button in the popup header, with a tooltip, `Accessible.name` and `Accessible.description`.
- Keyboard focus, Enter/Space, and F5 while the popup has focus all work.
- Busy state while any provider is in flight. Disabled with no providers enabled.
- Remove the bottom footer row unless it still carries something non-redundant.
- The existing per-provider overlap guard stays.

## Execution Tasks

- [x] Record the baseline: compact text, tooltip text and popup screenshots for the live payloads (gitignored `reports/`), plus live `ai-usage status <id> --json` safe fields for all four providers.
- [x] Move compact and tooltip derivation into pure JS (extend `MeterIntake.js` or add one sibling library) fed by the meter intake. Add `qmltestrunner6` tests for every row of the compact table and for the tooltip (multiple meters, stale, auth/error with `error` text, empty).
- [x] Wire compact/tooltip to the new functions. Remove `breakdownJson` / `secondaryRemainingPercent` model fields if they are now unused (QML only).
- [x] Popup height rule (content-driven, bounded, scrolling).
- [x] Refresh in the header, with accessibility, keyboard and F5 support, and a busy state.
- [x] Readability refinements: provider separation, spacing, heading hierarchy, progress bars. Theme values only. An exhausted meter may add the negative theme color next to its text.
- [x] Verify on the real Plasma desktop, in Breeze Light and Breeze Dark: compact (horizontal, and vertical if available), tooltip, popup on landscape and portrait/constrained height, with a freshly added widget. Use fixtures for states live data cannot show.
- [x] Documentation:
  - Recapture `docs/assets/horizon-usage.png` (popup), add compact plus tooltip, and recapture `docs/assets/horizon-settings.png` with all four providers. Capture on the real desktop and check that no secrets, tokens, emails or account ids are visible.
  - Update the README text, the `docs/release.md` compact checklist line and a `CHANGELOG.md` "Unreleased" entry.
  - Add Plasma reload guidance after install/upgrade (`plasmashell --replace` or log out/in, and re-add the widget if needed). Optionally print the hint from `scripts/install.sh`. Verify the guidance once.
- [x] Release readiness:
  - Run the `docs/release.md` validation checklist against this branch, and the secret audit.
  - Record the results and a version recommendation with its rationale in this file.
  - Leave `VERSION`, `metadata.json` and the README version line unchanged, and create no tag or GitHub release.
- [x] Run all tests (`QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/`; `python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh`) and confirm `git diff 0a06644 -- collector` is empty.
- [x] Independent Watcher evaluation against PHASES.md Phase 9 acceptance criteria 1–11 (`reports/stage-2-phase-9-watcher-3.md`, PASS). Attempts 1 and 2 failed; in-scope findings were fixed and rechecked.
- [x] Present the evidence, the version recommendation and Deferred Work to the owners. Owner accepted Phase 9 and approved **0.2.0** on 2026-10-09.

## Acceptance Criteria (summary; PHASES.md is authoritative)

1. Compact handles mixed states: one meter at 0 with others high shows `AI 75% · 1 at 0%`, not `AI 0%`. Also covered: all healthy, all at 0, auth/error, empty, loading, stale.
2. Compact text fits on a horizontal panel. A vertical panel may elide, with the full detail in the tooltip.
3. The tooltip lists each provider's meters (label and remaining %), stale age, and failure status with user-safe error text. Nothing invented.
4. Popup height: no excess space on landscape, stays on screen and scrolls on portrait, nothing clipped, checked on a fresh widget.
5. Refresh is in the header, works by keyboard and F5, has an accessible name and a busy state, is disabled with no providers, and causes no overlapping requests.
6. No Phase 8 popup regression (intake order, per-meter reset, percent remaining, failure states, `test_meter_intake.qml`).
7. Theme values only. Readable in Breeze Light and Breeze Dark, for the popup, compact panel and tooltip.
8. README screenshots are real-desktop, free of secrets and stored in `docs/assets/`. README, release doc and changelog are accurate. Reload guidance is verified.
9. Release checklist run, version recommendation recorded. No version change, tag or release.
10. Collector diff empty, tests pass, secret audit passes, Deferred Work recorded.
11. Watcher PASS, then explicit owner acceptance.

## Exclusions

Collector, provider, cache, auth and ADR-0012 changes. New providers (including Groq), billing, spend and accounts. Provider-specific compact logic. New settings or config keys, notifications, alternative compact modes, compact icon redesign. A general UI framework. Version bump, tag, GitHub release or publishing. Rewriting accepted Phase 0–8 history. Do not create `docs/handoffs/phase-9.md` before owner acceptance.

## Evidence

2026-10-09, branch `phase-9-compact-ux-release-polish`.

* Compact and tooltip text come from `MeterIntake.compactText` / `tooltipText`, which read the same intake as the popup. `breakdownJson` and `secondaryRemainingPercent` are gone from the QML model.
* Live safe fields: Codex Plus, 5-hour 100 and Weekly 99; Cursor Pro, Cursor Models 73–75 and Other Models 0; StepFun Plus, 5-Hour 92 and Weekly 84; Claude Pro, Current session 90 and Current week 77. One Claude fetch was stale with `Claude usage failed (HTTP 429)` and still showed the cached meters.
* Panel after `plasmashell --replace`: **`AI 73% · 1 at 0%`**. Screenshot: `docs/assets/horizon-compact.png`. Before the reload the same panel still said `AI 0%`.
* Popup: header `view-refresh` button, plan on the provider row, `% remaining`, `Resets in …` only when that meter has a reset, Other Models `0% remaining` in the negative theme color. Light: `reports/phase-9-popup-light.png` (also `docs/assets/horizon-usage.png`). Dark: `reports/phase-9-popup-dark.png`. Color scheme restored to BreezeClassic.
* Height: KWin reported minimum 288×216 (`gridUnit * 16` by `gridUnit * 12`). With saved geometry cleared, the window opened at 500×528, which is the `gridUnit * 40` cap on this screen, and showed a scrollbar with Claude at the bottom edge. A temporary `gridUnit * 18` cap (reverted before this note; installed QML matches the worktree) made the window 420×480 with a scrollbar and StepFun still on screen. `reports/phase-9-scroll.png`.
* `scripts/install.sh` prints the `plasmashell --replace` hint. Running that reload is what updated the panel text above.
* Tests: `qmltestrunner6 -input tests/test_meter_intake.qml` 6 passed; `qmltestrunner6 -input tests/test_compact_summary.qml` 14 passed. `qmltestrunner6 -input tests/` exits 1 because that runner only loads `tst_*.qml`. `python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh` 31 OK. `git diff 0a06644 -- collector` empty. No secret markers in the new QML, JS, or tests. `VERSION`, `metadata.json`, and the README version line are unchanged. No tag.
* Watcher attempt 1: **FAIL** (`reports/stage-2-phase-9-watcher-1.md`), findings W9-01 through W9-05.
* Follow-up on the final QML, after that report:
  * Landscape 1920×1080, final build, window 520×728: all four providers visible, no scrollbar. `reports/phase-9-popup-landscape.png`. Display restored to rotation left (KScreen rotation 2, geometry 1080×1920).
  * Short window 520×420 of the same build: scrollbar, Claude below the fold. `reports/phase-9-scroll-final.png`. The earlier `reports/phase-9-scroll.png` used a temporary cap and is not the final build.
  * `enableClaude=false` and `refreshIntervalMinutes=30` in `plasmawindowedrc` hid Claude. `reports/phase-9-settings-persist.png`. Those keys were removed and the preview was relaunched with Claude enabled.
  * `tests/test_refresh_keys.qml` covers F5 and the disabled-with-no-providers case. Enter/Space handlers are on the header button. Offscreen `keyClick` does not deliver Enter/Space to that control in this runner.
* Watcher attempt 2: **FAIL** (`reports/stage-2-phase-9-watcher-2.md`), remaining findings W9-03, W9-04, W9-05.
* Plasma's default tooltip stops at 8 lines, so later providers were cut off. The compact representation now supplies its own Kirigami-themed tooltip item and shows every provider. Hover captures: `reports/phase-9-tooltip-light.png`, `reports/phase-9-tooltip-dark.png`, `reports/phase-9-tooltip-classic.png`. README image: `docs/assets/horizon-compact.png` (panel text `AI 70% · 1 at 0%` plus the full tooltip).
* Settings opened from the panel's Configure Horizon action, with all four providers and a 15 minute interval. `docs/assets/horizon-settings.png`. The token field is empty.
* Settings persistence: Apply with Claude unchecked and the interval at 30 minutes stored `enableClaude=false` and `refreshIntervalMinutes=30`, read back from the running applet. Dialog: `reports/phase-9-settings-persist-ui.png`. Both were restored to the defaults (the keys are absent again). The popup after restore still shows four providers (`reports/phase-9-popup-after-restore.png`).
* Color scheme is BreezeClassic. Display rotation was not changed.

## Version recommendation

**0.2.0.** Since 0.1.1 the user-visible product gained Claude, ordered meters, the Phase 8 popup, and this compact summary. Install and config keys are unchanged. The owner approved this recommendation on 2026-10-09.

## Release checklist (`docs/release.md`)

1. Collector JSON for all four providers: ok, except one Claude response was stale after HTTP 429 and still carried cached meters.
2. Widget installs and is on the panel.
3. Compact shows `AI 73% · 1 at 0%` with one meter exhausted.
4. Popup shows the enabled providers.
5. Settings persistence: Claude unchecked and a 30 minute interval survived Apply (`enableClaude=false`, `refreshIntervalMinutes=30`). Both were restored to the defaults afterward. The StepFun token was not rewritten.
6. StepFun token was not rewritten.
7. Claude still uses the existing read-only credential path. This phase did not change it.
8. Secret audit of the new UI files found no tokens. Screenshots show plan names and percents only.

## Deferred Work

_None recorded yet._ Known carry-over: removing the collector compatibility fields `remainingPercent`, `resetAt`, `secondaryRemainingPercent` and `breakdown`; any other provider, including Groq.

## Handoff

Owner accepted Phase 9 on 2026-10-09. Snapshot: `docs/handoffs/phase-9.md`. The same action approved release **0.2.0**.

STOP. Do not start new work automatically.
