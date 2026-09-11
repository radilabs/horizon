# Phase 6 Handoff — StepFun Auth Resilience

Date: 2026-09-11  
Environment: openSUSE Tumbleweed, Plasma 6, KWallet enabled  
Release: **0.1.1** (`v0.1.1`)

**PHASE 6 HANDOFF: ACCEPTED**

**Path proven:** `AUTOMATIC REFRESH SUPPORTED`

## Owner acceptance

Owners explicitly accepted Stage 1 / Phase 6 after Watcher PASS. The owner tested the installed artifact and confirmed it works.

Acceptance is recorded here. This file is the accepted-state snapshot. Do not treat Watcher PASS alone as acceptance.

## Deliverables

* Bounded Oasis `RefreshToken` recover in `collector/providers/stepfun.py` (one attempt per usage fetch on `auth_unavailable`)
* Validate-before-replace: `QueryStepPlanRateLimit` must succeed before KWallet `secret_set`
* Failed refresh/validation leaves the previous KWallet value unchanged; CLI/settings still point at Set/Replace Token
* Unit tests: `tests/test_stepfun_oasis_refresh.py`
* Durable docs: `docs/providers/stepfun.md`, `docs/security.md`, ADR-0010
* Independent Watcher report (runtime, gitignored): `reports/stage-1-phase-6-watcher-1.md`
* Horizon version **0.1.1**

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Oasis credential structure and expiry/refresh documented from sanitized evidence | PASS |
| 2 | Conclusive: automatic renewal using stored KWallet material alone | PASS — Path A |
| 3 | If supported: one bounded refresh, validate before KWallet replace, live usage succeeds | PASS |
| 4 | If unsupported: no unsafe workaround | N/A (Path A) |
| 5 | No secrets in repo/config/cache/logs/stdout/argv/docs/task evidence | PASS |
| 6 | StepFun recovery failure does not affect Codex or Cursor | PASS |
| 7 | No auth-refresh loop / overlapping recovery | PASS (in-process lock + one retry) |
| 8 | Docs match supported recovery path and upstream fragility | PASS |

## Tests / owner evidence

Coder/Watcher (2026-09-11, sanitized):

* Baseline: Codex `ok`, Cursor `ok`, StepFun HTTP 401 / `auth_failed` (expired stored pair)
* Live recover: KWallet sha12 `eb2819b3a0e0` → `b0909bb6f0fb`; StepFun `ok` / Plus / 100%
* Second fetch: sha unchanged (no refresh loop on valid token)
* `python3 -m unittest tests.test_stepfun_oasis_refresh -v` — 8 OK
* Watcher: `WATCHER RESULT: PASS` (`reports/stage-1-phase-6-watcher-1.md`)
* Codex/Cursor remained `ok` after StepFun recover

Owner: tested the upgraded local artifact and confirmed it works (2026-09-11). Explicit Phase 6 acceptance granted.

Closeout re-check (2026-09-11, after 0.1.1 version bump): Codex `ok` ChatGPT Plus 100%; Cursor `ok` Pro 95%; StepFun `ok` Plus 100%; `ai-usage auth stepfun status` → `working`; `VERSION` and `plasmoid/metadata.json` → `0.1.1`; unit tests 8 OK; cache files contain no JWT/token material.

## Security validation

* Token remains KWallet-only (`Horizon` / `stepfun/oasis-token`)
* Refresh write-back only after usage validation (ADR-0010)
* No username/password login, no browser/Zen import
* Secret audit clean at closeout

## Known limitations

* Passport/Dashboard APIs are unofficial; host/app id can change
* JWT `exp` is not a complete predictor of whether `RefreshToken` still accepts the stored pair
* If `RefreshToken` rejects the stored material, the user must paste a fresh Oasis token
* Refresh serialization lock is in-process only
* Stage 1 as a product stage is not closed; only Phase 6 is accepted. No further Stage 1 phase is authorized.

## Deferred work

```text
- StepFun username/password login
- browser/session import (including Zen)
- generic Oasis framework
- additional providers including Groq
- account/subscription management
- Low-quota notifications (Phase 5 leftover)
- Official StepFun public quota API
```

## Stop

Phase 6 accepted. Horizon **0.1.1**.

**Do not begin another Stage/Phase** (including Groq) without an explicit new contract and `TASKS.md` authorization.
