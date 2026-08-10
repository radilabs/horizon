# Phase 4 Handoff — StepFun Step Plan

Date: 2026-08-10  
Environment: openSUSE Tumbleweed, Plasma 6.7.3 Wayland, KWallet enabled

## Deliverables

* `collector/secret_store.py` — minimal KWallet-backed secret store
* `collector/providers/stepfun.py` — StepFun provider (Oasis token + Dashboard APIs)
* `collector/ai-usage` — `auth stepfun {set,status,clear}` + `status stepfun --json`
* `plasmoid/contents/ui/main.qml` — provider list `codex`, `cursor`, `stepfun`
* `docs/providers/stepfun.md`
* `docs/security.md`, `docs/provider-contract.md`, `docs/cache.md`, `docs/usage-schema.md`
* `decisions/0009-os-credential-store.md`
* `docs/handoffs/phase-4.md` — this report
* `.gitignore` — Oasis/token-shaped artifacts

## StepFun Discovery

* **Credential:** user-supplied Oasis token in KWallet (`Horizon` / `stepfun/oasis-token`); no username/password login
* **WebID:** JWT `device_id` from refresh half of `access...refresh` pair
* **App id:** JWT `app_id` from refresh half (observed `20700`)
* **API base:** `https://platform.stepfun.ai` (not CodexBar’s older `.com`/`10300` pair)
* **Usage:** `QueryStepPlanRateLimit`; **plan:** `GetStepPlanStatus` → `subscription.name` = **Plus**
* **Account shape:** rolling-window Coding Plan (`plan_family: 1`) with live 5-hour + weekly resets
* **Limitations:** unofficial APIs; token paste required; wrong host/app id fails auth

## Provider Integration

* Registry: `stepfun` → `StepFunProvider`
* Mapping: `breakdown` = **5-Hour Usage** + **Weekly Usage** as remaining % (`left_rate × 100`); per-line `resetAt`
* Credit-plan path implemented but not exercised on this account (shape-based; no fake 0% windows)
* Cache: `~/.cache/horizon/usage-stepfun.json` (normalized only)

## Multi-Provider UI

Explicit list: `codex`, `cursor`, `stepfun`. Independent collector commands; shared Refresh.

## Tests Performed

1. Secret-store lifecycle (set/get/delete/cross-process) with disposable non-secret
2. `auth stepfun set/status/clear`; `--token` rejected
3. Live `ai-usage status stepfun --json` → Plus, 5-Hour 100%, Weekly 100%, status ok
4. Upstream compare: rates/resets match; wrong WebID → `auth_unavailable`
5. Repeat usage request succeeds
6. Cache write; contents normalized only (no token)
7. Stale fallback (`STEPFUN_API_BASE=127.0.0.1:1`) preserves breakdown
8. `--no-cache` upstream fail → `upstream_error`
9. Recovery → ok
10. Isolation: StepFun stale while Codex/Cursor ok
11. Missing token → `auth_unavailable` (token restored afterward)
12. Codex + Cursor regression ok
13. Secret audit: no credential artifacts tracked; caches clean

## Acceptance Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Real StepFun usage/credit retrieved | PASS |
| 2 | Normalized through common model | PASS |
| 3 | Credentials not exposed | PASS |
| 4 | StepFun failure does not affect Codex/Cursor | PASS |
| 5 | All three providers can appear together | PASS |
| 6 | Discovery documented | PASS |

**PHASE 4 HANDOFF: PASS**

## Security Validation

* Oasis token only in KWallet
* No token in cache/repo/docs/stdout evidence
* No StepFun login or password storage
* Repository secret audit clean for this handoff

## Decisions

* `decisions/0009-os-credential-store.md`

## Deferred Work

```text
- [2026-08-10] Periodic refresh / notifications / settings → Phase 5
- [2026-08-10] StepFun token refresh write-back → Future (out of scope; no login/refresh mutation)
- [2026-08-10] Browser cookie auto-import → Rejected / Future only if explicitly approved
- [2026-08-10] Credit-plan live UI verification on a credit account → Future when available
```

## Stop

Phase 4 handoff satisfied. **Do not begin Phase 5** without a new explicit execution instruction.
