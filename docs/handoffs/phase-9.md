# Phase 9 Handoff — Compact UX and Release Polish

Date: 2026-10-09  
Environment: openSUSE, Plasma 6, Breeze Classic restored after Light and Dark checks  
Release: **0.2.0** (`v0.2.0`), approved by the owner with this acceptance

**PHASE 9 HANDOFF: ACCEPTED**

## Owner acceptance

The project owner explicitly accepted Stage 2 / Phase 9 on 2026-10-09 after Watcher PASS, and approved the recommended **0.2.0** release in the same action.

Acceptance is recorded here. This file is the accepted-state snapshot. Watcher PASS alone was not acceptance.

## Deliverables

* Compact summary uses the lowest remaining percent above 0, and counts meters at exactly 0 (`AI <n>% · <k> at 0%`)
* Tooltip lists every enabled provider and meter. A custom tooltip item avoids Plasma's 8-line default
* Popup height follows content, stays on screen, and scrolls past the cap. Refresh is a header tool button
* README screenshots, changelog, and Plasma reload guidance match that behavior
* Collector, authentication, and the ordered `meters` contract are unchanged
* Independent Watcher report (runtime, gitignored): `reports/stage-2-phase-9-watcher-3.md` (PASS)

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Compact mixed states, including one meter at 0 | PASS |
| 2 | Compact text fits; vertical text may elide | PASS |
| 3 | Tooltip lists meters, stale age, and failure text | PASS |
| 4 | Popup fits on landscape and scrolls when constrained | PASS |
| 5 | Header Refresh, F5, accessible name, busy state | PASS |
| 6 | Phase 8 meter intake and per-meter reset still hold | PASS |
| 7 | Readable in Breeze Light and Breeze Dark | PASS |
| 8 | README screenshots and user docs match the widget | PASS |
| 9 | Release checklist recorded; owner approved 0.2.0 | PASS |
| 10 | Collector diff empty; tests pass; no secrets | PASS |
| 11 | Watcher PASS, then explicit owner acceptance | PASS |

## Tests / owner evidence

* `qmltestrunner6 -input tests/test_compact_summary.qml` — 14 passed
* `qmltestrunner6 -input tests/test_refresh_keys.qml` — 4 passed
* `qmltestrunner6 -input tests/test_meter_intake.qml` — 6 passed
* `python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh` — 31 OK
* `git diff 0a06644 -- collector` empty
* Live panel showed `AI 70% · 1 at 0%` with Cursor Other Models at 0
* Tooltip hover captured in Breeze Light, Breeze Dark, and Breeze Classic
* Settings persistence: Claude off and a 30 minute interval survived Apply, then both defaults were restored

Watcher attempt 3: **PASS**. Report: `reports/stage-2-phase-9-watcher-3.md`. Attempts 1 and 2 failed and were corrected in scope.

Owner: accepted Phase 9 on 2026-10-09 and approved release **0.2.0**.

## Known limitations

* This desktop has a horizontal panel only. Vertical compact text elides; the tooltip carries the full summary
* Offscreen `qmltestrunner6` covers F5. Enter and Space are handled on the Refresh button and were not delivered by that runner
* `plasmawindowed` keeps the first saved window size, so landscape fit and scrolling were checked with explicit geometry
* `qmltestrunner6 -input tests/` only loads `tst_*.qml`. The three QML files above are run individually

## Deferred work

```text
- Removing compatibility fields remainingPercent, resetAt, secondaryRemainingPercent, and breakdown
- Any other provider, including Groq
```

## Stop

Phase 9 accepted. Stage 2 is closed. Horizon **0.2.0**.

**Do not begin a new phase** without an explicit new contract and `TASKS.md` authorization.
