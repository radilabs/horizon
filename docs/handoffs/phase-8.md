# Phase 8 Handoff — Plasma UI/UX Refresh

Date: 2026-10-09  
Environment: openSUSE, Plasma 6, Breeze Classic restored after Light and Dark checks  
Release: remains **0.1.1** (`v0.1.1`). This acceptance is not a version bump or tag.

**PHASE 8 HANDOFF: ACCEPTED**

## Owner acceptance

The project owner explicitly accepted Stage 2 / Phase 8 on 2026-10-09 after Watcher PASS.

Acceptance is recorded here. This file is the accepted-state snapshot. Watcher PASS alone was not acceptance.

## Deliverables

* Expanded popup reads ordered `meters`, then `breakdown`, then the primary/secondary compatibility fields (`plasmoid/contents/ui/MeterIntake.js`)
* Each meter shows its provider label, percent remaining, a theme progress bar, and a reset only when that meter has `resetAt`
* Popup scrolls inside Plasma/Kirigami bounds instead of clipping at a fixed height
* Compact panel text and tooltip generation are unchanged
* Collector, authentication, cache, and the meter contract are unchanged
* Fixture tests: `tests/test_meter_intake.qml`
* Independent Watcher report (runtime, gitignored): `reports/stage-2-phase-8-watcher-1.md` (PASS)
* Popup screenshots (runtime, gitignored): `reports/phase-8-breeze-light.png`, `reports/phase-8-breeze-dark.png`

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Four providers visible, with name and known plan, without clipping | PASS |
| 2 | 1..N meters render in order with provider labels; no Primary/Secondary label | PASS |
| 3 | Percents and bars are percent remaining and match live CLI values | PASS |
| 4 | A meter shows a reset only when it has its own `resetAt` | PASS |
| 5 | Legacy `breakdown` and primary/secondary payloads still render | PASS |
| 6 | Stale, auth, error, loading, and empty states are identifiable in text; failures show no bars | PASS |
| 7 | Theme colors and Kirigami units only; readable in Breeze Light and Breeze Dark | PASS |
| 8 | Collector diff empty; existing tests pass | PASS |
| 9 | Compact text and tooltip stay on the previous behavior | PASS |
| 10 | No secrets in QML, fixtures, or screenshots | PASS |
| 11 | Out-of-scope work deferred | PASS |
| 12 | Watcher PASS, then explicit owner acceptance | PASS |

## Tests / owner evidence

* `QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_meter_intake.qml` — 4 fixture tests passed
* `python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh` — 31 OK
* `git diff 0ca66c4 -- collector` empty
* Live CLI safe fields matched the popup: Codex Plus, 5-hour 99 and Weekly 99; Cursor Pro, Cursor Models 75 and Other Models 0; StepFun Plus, 5-Hour 97 and Weekly 86; Claude Pro, Current session 100 with no reset and Current week 78
* Compact panel stayed `AI 0%` while Cursor Other Models was 0
* `plasmawindowed com.radilabs.horizon` after install showed all four providers, plans, `% remaining`, per-meter resets, and Refresh in Breeze Light and Breeze Dark

Watcher attempt 1: **PASS**. Report: `reports/stage-2-phase-8-watcher-1.md`. No blocking findings.

Owner: accepted Phase 8 on 2026-10-09.

## Known limitations

* This Pro account returned two Claude windows. A third window is fixture-tested only
* Live auth and upstream failures were not on screen; those states use the existing status text and show no bars
* On this screen the four providers fit without scrolling. The popup scrolls when the list is taller than the window
* The compact panel and tooltip still use the compatibility percents

## Deferred work

```text
- Phase 9 compact panel, tooltip, and release screenshots
- Refresh-interaction polish and responsive refinements
- Removing compatibility fields remainingPercent, resetAt, secondaryRemainingPercent, and breakdown
- Any other provider, including Groq
```

## Stop

Phase 8 accepted. Stage 2 stays open. Horizon release remains **0.1.1**.

**Do not begin Phase 9** without an explicit new contract and `TASKS.md` authorization.
