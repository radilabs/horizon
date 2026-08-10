# Phase 2 Handoff — Provider Architecture and Local State

Date: 2026-08-10  
Environment: openSUSE Tumbleweed, Plasma 6.7.3 Wayland

## Deliverables

* `collector/ai-usage` — generic CLI dispatch + cache fallback
* `collector/providers/codex.py` — Codex provider implementation
* `collector/providers/__init__.py` — `ProviderError` / helpers
* `collector/cache.py` — XDG last-successful cache
* `plasmoid/contents/ui/main.qml` — provider-agnostic + stale UI
* `docs/provider-contract.md`
* `docs/usage-schema.md`
* `docs/cache.md`
* `docs/handoffs/phase-2.md` — this report
* `decisions/0005-explicit-provider-registry.md`
* `decisions/0006-xdg-usage-cache.md`

## Provider Architecture

* Contract: identity + `detect()` + `fetch_usage()` returning normalized dict; errors via `ProviderError`
* Registered providers: `codex` → `CodexProvider`
* Dispatch: explicit `PROVIDERS` map in CLI (no plugins)
* QML boundary: runs `ai-usage status <configuredProvider> --json` and renders normalized fields only

## Normalized Schema

Documented in `docs/usage-schema.md` (statuses include `ok`, `stale`, `auth_unavailable`, `provider_unavailable`, `upstream_error`, `collector_error`).

## Cache Behavior

* Path: `~/.cache/horizon/usage-codex.json`
* Success writes envelope `{fetchedAt, provider, data}`
* Live failure with cache → `status=stale`, `stale=true`, preserves `fetchedAt`
* Corrupt/missing cache → normal error payload; no crash

## Tests Performed

1. `ai-usage status codex --json` → exit 0, ChatGPT Plus, remainingPercent live
2. Cache file created; contents match normalized ok data; no tokens
3. Unknown provider `nope` → exit 1, `provider_unavailable`
4. Missing auth with warm cache → exit 1, `stale` + cached remainingPercent
5. Missing auth with `--no-cache` → `auth_unavailable`
6. Corrupt cache + missing auth → `auth_unavailable` (no crash)
7. Plasmoid upgraded and re-added to panel
8. Secret audit on repo + cache

## Acceptance Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Codex through common provider interface | PASS |
| 2 | No provider-specific upstream data in QML | PASS |
| 3 | Normalized schema documented | PASS |
| 4 | Last successful state cached | PASS |
| 5 | Cached data shown when fresh fails | PASS |
| 6 | Cached data clearly stale | PASS |
| 7 | Manual refresh still works | PASS |
| 8 | Codex behavior does not regress | PASS |

**PHASE 2 HANDOFF: PASS**

## Regression Results

Observable Codex CLI JSON fields for success remain compatible with Phase 1 (`provider`, `displayName`, `plan`, `remainingPercent`, `resetAt`, `status=ok`). Auth ownership unchanged (ADR-0004).

## Security Validation

* Credentials remain in `~/.codex/auth.json` only
* Cache contains normalized plan/percent/timestamps only
* No new secret-bearing Horizon store
* Repository/cache secret checks clean for this handoff

## Decisions

* `decisions/0005-explicit-provider-registry.md`
* `decisions/0006-xdg-usage-cache.md`

## Deferred Work

* Cursor provider → Phase 3
* StepFun → Phase 4
* Periodic refresh / notifications / settings → Phase 5
* Multi-provider UI → later phase when second provider exists

## Stop

Phase 2 handoff satisfied. **Do not begin Phase 3** without a new explicit execution instruction.
