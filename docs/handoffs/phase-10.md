# Phase 10 Handoff — Post-0.2.0 Remediation

Date: 2026-11-27  
Environment: openSUSE, Plasma 6  
Release: **0.2.1** (`v0.2.1`), approved by the owner with this acceptance

**PHASE 10 HANDOFF: ACCEPTED**

## Owner acceptance

The project owner accepted Stage 3 / Phase 10 on 2026-11-27 after Watcher PASS, and approved release **0.2.1** in the same action.

The owner wrote "phase 19". No Phase 19 exists. This snapshot records Phase 10, the only phase awaiting acceptance.

Acceptance is recorded here. Watcher PASS alone was not acceptance.

## Deliverables

* W-01..W-14 from `reports/post-v0.2.0-external-watcher-1.md` are resolved inside the Phase 10 contract
* StepFun credit labels stay separate when the payload has separate rates, and a refreshed token is stored only after a successful usage check
* Network or upstream failure is `unavailable`, not a rejected token
* Cache secret-key checks walk nested objects. The stored field list is unchanged
* Popup reset and cache-age text recompute while the popup is open
* Independent Watcher reports (gitignored): `reports/stage-3-phase-10-watcher-1.md` (FAIL), `reports/stage-3-phase-10-watcher-2.md` (FAIL), `reports/stage-3-phase-10-watcher-3.md` (PASS)

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | W-01..W-14 resolved or recorded as the contract's false positives | PASS |
| 2 | Credit labels kept separate; KWallet write only after a successful usage check | PASS |
| 3 | Offline or upstream failure is not reported as a rejected token | PASS |
| 4 | Four providers still work. Old and new tests pass | PASS |
| 5 | ADR-0012 unchanged except the W-01 labels becoming reachable | PASS |
| 6 | Cited qmllint warnings gone. Total at most the baseline of 71 | PASS |
| 7 | Real-desktop checks: popup, keys, settings, reset text, cache age | PASS |
| 8 | Secret audit passes | PASS |
| 9 | Owner approved 0.2.1 after the phase. No release during implementation | PASS |
| 10 | Deferred Work recorded | PASS |
| 11 | Watcher PASS, then explicit owner acceptance | PASS |

## Tests / owner evidence

* `python3 -m unittest discover -s tests` — 48 passed
* QML: compact 14, meter intake 6, refresh keys 7, command and times 6, all passed
* `qmllint6` — 28 warnings, down from 71. The W-11 warnings are gone
* `bash -n` on the install scripts passed
* `decisions/`, and the 0.2.0 version files, were unchanged until this acceptance release
* Desktop: F5, Space, and Return each started one wave of four provider fetches. Reset text moved back one minute with no new fetch. A stale fixture showed `Cached · 2m ago`, then `Cached · 3m ago`

Watcher attempt 3: **PASS**. Report: `reports/stage-3-phase-10-watcher-3.md`.

Owner: accepted Phase 10 on 2026-11-27 and approved release **0.2.1**.

## Known limitations

* Cache-age text appears only when a provider is stale. The live accounts were healthy, so that line was captured with a temporary collector on `PATH`. The installed `ai-usage` binary was not replaced

## Deferred work

```text
- Verifying a pasted StepFun token before it is stored
- A cross-process StepFun refresh lock
- Showing Subscription Credits and Top-up Credits at the same time
- A longer cache secret-key list
- qmllint warnings that were not in W-11
```

## Stop

Phase 10 accepted. Stage 3 is closed. Horizon **0.2.1**.

**Do not begin a new phase** without an explicit new contract and `TASKS.md` authorization.
