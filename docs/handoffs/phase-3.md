# Phase 3 Handoff — Cursor Provider

Date: 2026-08-10 (mapping correction)  
Environment: openSUSE Tumbleweed, Plasma 6.7.3 Wayland, Cursor 3.15.6

## Deliverables

* `collector/providers/cursor.py` — Cursor provider (read-only `state.vscdb` + DashboardService)
* `collector/ai-usage` — registry entry for `cursor`
* `plasmoid/contents/ui/main.qml` — multi-provider UI; labeled `breakdown` meters with per-line reset
* `docs/providers/cursor.md` — discovery + **corrected** two-meter mapping + unused aggregate notes
* `docs/provider-contract.md`, `docs/usage-schema.md`, `docs/cache.md`, `docs/security.md`
* `decisions/0007-cursor-credentials-read-only.md`
* `decisions/0008-optional-usage-breakdown.md` — labeled meters; no Included aggregate meter
* `.gitignore` — Cursor session artifacts
* `docs/handoffs/phase-3.md` — this report
* `tasks/phase-3-cursor.md`

## Cursor Discovery

* **Auth/session source:** SQLite `~/.config/Cursor/User/globalStorage/state.vscdb` (`cursorAuth/accessToken`), opened read-only.
* **Usage mechanism:** `POST …/DashboardService/GetCurrentPeriodUsage` with Bearer token + `Connect-Protocol-Version: 1`.
* **Credential ownership:** Remains with Cursor; Horizon never persists tokens.

## Corrected quota mapping

Horizon mirrors the **current Cursor Usage UI** only:

| Horizon meter (order) | Upstream field | Display |
|-----------------------|----------------|---------|
| 1. Cursor Models | `planUsage.autoPercentUsed` | remaining `%` = `round(100 - autoPercentUsed)` |
| 2. Other Models | `planUsage.apiPercentUsed` | remaining `%` = `round(100 - apiPercentUsed)` |

* Primary `remainingPercent` = Cursor Models; `secondaryRemainingPercent` = Other Models.
* `breakdown` carries both labeled rows; each includes `resetAt` from shared `billingCycleEnd` (no per-pool reset fields observed).
* **Not shown as a meter:** included/spend aggregate (`remaining`/`limit`/`totalSpend` / `displayMessage`). No literal `includedPercentUsed` field was present. `totalPercentUsed` is observed-but-unused. See `docs/providers/cursor.md`.

## Provider Integration

* Registry: `PROVIDERS["cursor"] = CursorProvider`
* Schema: existing fields + optional `breakdown` (ADR-0008); no architecture redesign
* Cache: `~/.cache/horizon/usage-cursor.json`

## Multi-Provider UI

* Explicit list `["codex", "cursor"]`
* Independent collector commands / state
* Cursor section shows Cursor Models then Other Models (remaining %), with reset per line

## Tests Performed (mapping correction)

1. Live `ai-usage status cursor --json` → Cursor Models **98%** remaining, Other Models **100%** remaining
2. Direct upstream compare: `autoPercentUsed≈2.07` → UI “2% used”; `apiPercentUsed=0` → “0% used”; Horizon remaining matches `100 - used`
3. Upstream `displayMessage` (“62% of your included usage”) present but **not** in Horizon payload / UI meters
4. Assert no `Included` label in collector JSON
5. Shared `resetAt` `2026-09-02T21:24:02+02:00` on payload and both breakdown rows (= `billingCycleEnd`)
6. Codex live unchanged: ChatGPT Plus, 94%, no `breakdown`
7. Cursor auth failure (`--auth-file` missing) → `auth_unavailable`
8. Cursor upstream fail → `stale` with cached two-meter breakdown preserved
9. Cursor recovery → `ok` again
10. Cache inspection: normalized fields only
11. Secret audit: no credential artifacts tracked; cache clean
12. Plasmoid upgraded via `kpackagetool6`

## Acceptance Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Detects usable Cursor authentication where present | PASS |
| 2 | Real Cursor usage can be retrieved | PASS |
| 3 | Cursor data normalized through common model | PASS |
| 4 | Does not expose or persist Cursor secrets | PASS |
| 5 | Cursor failure does not prevent Codex from working | PASS |
| 6 | Both Codex and Cursor appear correctly in the widget | PASS |
| 7 | Cursor provider discovery documented | PASS |

**PHASE 3 HANDOFF: PASS**

## Required Handoff Tests

| Scenario | Result |
|----------|--------|
| Cursor success | Two-meter remaining % matches Usage UI pools |
| Cursor auth failure | `auth_unavailable` |
| Cursor upstream failure | `stale` with cached meters |
| Codex during Cursor failure | Codex remains independent / `ok` when live |

## Security Validation

* Cursor credentials remain in `state.vscdb` only
* Cache: normalized plan/percent/timestamps/`breakdown` only
* No session artifacts committed; secret audit clean

## Decisions

* `decisions/0007-cursor-credentials-read-only.md`
* `decisions/0008-optional-usage-breakdown.md` (corrected: two UI meters only)

## Deferred Work

```text
- [2026-08-10] StepFun provider → Phase 4
- [2026-08-10] Provider settings / ordering → Phase 5
- [2026-08-10] Periodic refresh / notifications → Phase 5
- [2026-08-10] In-memory Cursor token refresh without writing state.vscdb → Future
- [2026-08-10] Derived display of unused included/spend aggregate → Future only if semantics proven
```

## Stop

Phase 3 handoff satisfied after mapping correction. **Do not begin Phase 4** without a new explicit execution instruction.
