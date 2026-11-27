# Phase 12 Handoff — Xiaomi MiMo Token Plan

Date: 2026-11-27  
Environment: openSUSE, Plasma 6  
Release: unchanged, Horizon **0.2.1** (`v0.2.1`)

**PHASE 12 HANDOFF: ACCEPTED**

## Owner acceptance

The project owner accepted Stage 4 / Phase 12 on 2026-11-27 after Watcher PASS, then asked for a documentation check and for the checkpoint to be pushed to `main`.

Acceptance is recorded here. Watcher PASS alone was not acceptance. No version bump, tag, or GitHub release was requested or made.

## Deliverables

* Provider `mimo` (display name Xiaomi MiMo), off by default
* One `Credits` meter from Xiaomi's official `GET /v1/platform/token_plan`
* User-supplied `tp-` key stored only in KWallet (`mimo/token-plan-key`)
* Explicit region `sgp`, `cn`, or `ams`, default `sgp`, with no probing
* Plan labels such as `Lite · Annual`; unknown codes preserved
* `resetAt` is Xiaomi's UTC period end, including annual plans
* Manual refresh only: the interval timer, startup, popup open, and settings changes do not fetch MiMo
* Docs checked against the code. The clipboard-clear and `invalid` shape-check wording was tightened to match the helper and CLI
* Independent Watcher report (gitignored): `reports/stage-4-phase-12-watcher-1.md` (PASS)

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | One Credits meter, percent formula, UTC reset | PASS |
| 2 | Plan labels, including unknown codes | PASS |
| 3 | Monthly and annual period ends kept as given | PASS |
| 4 | KWallet only; no env, bashrc, or MiMo-Code reads | PASS |
| 5 | Configured region only; 401 is one request | PASS |
| 6 | Failure states stay `upstream_error` or `auth_unavailable` | PASS |
| 7 | Manual refresh only | PASS |
| 8 | Secret audit | PASS |
| 9 | Settings checkbox, region, and key controls | PASS |
| 10 | Existing providers unchanged | PASS |
| 11 | Live MiMo check | Skipped: no KWallet key |
| 12 | Scope fence | PASS |
| 13 | Deferred Work recorded | PASS |
| 14 | Watcher PASS, then owner acceptance | PASS |

## Tests / owner evidence

* `python3 -m unittest discover -s tests` — 78 passed (baseline 61)
* QML: compact 14, meter intake 6, refresh keys 8, command and times 8, all passed
* Live `ai-usage status` for Codex, Cursor, StepFun, and Claude: all `ok`
* MiMo live request skipped because no key is stored in KWallet
* Settings page on the installed widget showed the MiMo switch, region selector, and key controls

Watcher: **PASS**. Report: `reports/stage-4-phase-12-watcher-1.md`.

Owner: accepted Phase 12 on 2026-11-27. No release.

## Known limitations

* MiMo stays idle until a manual Refresh or `ai-usage status mimo`
* A key that exists only in the shell environment is ignored
* A wrong region is reported as a rejected key, because Xiaomi answers that way

## Deferred work

```text
- Unattended or periodic MiMo polling
- Showing a cached MiMo result at startup without calling the collector
- A monthly label for a bare tier code, if Xiaomi documents that meaning
- Team seats, multiple keys, or more than one region at once
```

## Stop

Phase 12 accepted. Stage 4 is closed. Horizon remains **0.2.1**.

**Do not begin a new phase** without an explicit new contract and `TASKS.md` authorization.
