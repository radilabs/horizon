# Stage 2 / Phase 7 — Provider Information Contract

**Status: ACCEPTED** (2026-10-09). This file is historical execution evidence. It is **not** executable.

Accepted snapshot: `docs/handoffs/phase-7.md`. Horizon release remains **0.1.1**.

**Authority:** `PHASES.md` Stage 2 / Phase 7, `TASKS.md`  
**Previous accepted snapshot:** `docs/handoffs/phase-6.5.md`  
**Branch:** `phase-7-provider-information-contract` (from `1bda0af`, not `main`)  
**Worktree:** `/home/naorw/.t3/worktrees/horizon/phase-6.5-claude-usage`

## Goal

Establish and verify the minimal provider-neutral information contract for the four existing providers. Preserve operational behavior; prepare a sound contract for Phase 8 UI redesign.

## Execution Tasks

- [x] Inspect current usage schema, cache behavior, QML bindings and four collectors; record sanitized evidence and semantics for existing meters and states.
- [x] Draft the smallest necessary provider/meter schema and explicit old-to-new compatibility strategy. Use Claude's multiple windows as mandatory evidence. Record only durable decisions.
- [x] Implement any **necessary** contract/normalization/adapter changes without changing existing visible UI or authentication flows.
- [x] Add deterministic fixtures/tests for each provider, multiple windows, unavailable/auth/error/stale outputs and compatibility with existing consumers.
- [x] Run relevant automated tests, provider isolation checks and secret audit; record direct evidence.
- [x] Independent Watcher evaluation against Phase 7 acceptance criteria; fix in-scope findings and rerun if needed.
- [x] Present verification and any deferred work for owner review. **STOP pending owner acceptance.**

## Contract decision

ADR-0012. Canonical list is ordered `meters`. Each meter has a provider-native `label`, integer `remainingPercent` (percent remaining, 0–100), and optional `resetAt`.

Compatibility projections, produced only by `providers.contract.project_ok`:

- `remainingPercent` / `resetAt` copy the first meter
- `secondaryRemainingPercent` exists only for a second meter and copies its percent
- `breakdown` is a copy of `meters`

Current QML is unchanged and still reads `breakdown`, not `meters`.

Architect review (thread `82f565ff-7a65-457a-ab20-857f4f83c261`, 2026-10-09) agreed, with corrections applied:

- Cursor, StepFun, and Claude compatibility fields stay on the same projection as before
- Codex gaining labels and per-window resets through existing `breakdown` is the one deliberate visible change
- stale reads rebuild `meters` for old cache and do not invent `breakdown`
- failure payloads keep today's `error_payload` keys and omit `meters`
- 86400 seconds is `1-day limit`, not `24-hour limit`
- duplicate labels are kept; order distinguishes them

## Inventory (sanitized)

| Provider | Meters | Direction | Resets | Not meters |
|----------|--------|-----------|--------|------------|
| Codex | duration label from `limit_window_seconds` | upstream `used_percent` → remaining | each window's own `reset_at` | email, account ids, spend |
| Cursor | `Cursor Models`, `Other Models` | `100 - autoPercentUsed` / `apiPercentUsed` | shared `billingCycleEnd` | included/spend aggregate, `displayMessage`, `totalPercentUsed` |
| StepFun | `5-Hour Usage`, `Weekly Usage` (or credit labels) | `left_rate` is already remaining | independent epoch fields | Oasis token |
| Claude | Claude Code titles, 1..N, plus enabled Extra usage | `utilization` is percent used; `1.0` → 99 remaining | each window's `resets_at` | `limits[]`, `seven_day_breakdown`, disabled `spend` |

Live `ai-usage status <id> --json` on 2026-10-09, safe fields only:

- Codex exit 0, `ok`, ChatGPT Plus, remaining 100, secondary 99, labels `5-hour limit`, `Weekly limit`, meters equal breakdown, no secret markers
- Cursor exit 0, `ok`, Pro, 77 / 0, `Cursor Models`, `Other Models`
- StepFun exit 0, `ok`, Plus, 99 / 86, `5-Hour Usage`, `Weekly Usage`
- Claude exit 0, `ok`, Pro, 95 / 78, `Current session`, `Current week (all models)`

`git diff -- plasmoid` was empty.

## Tests

```text
python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh
Ran 31 tests in 0.067s
OK
```

Covers projection, legacy stale rebuild, error key set, Codex duration labels and independent resets, duplicate labels, Cursor aggregate ignored, StepFun independent resets, Claude used-vs-remaining and a third window, cache round-trip, and secret-field refusal.

## Boundaries

No provider additions, authentication changes, UI redesign, invented account hierarchy, generalized plugin framework, or work from Phases 8–9. Future balance/spend/rate-limit designs are exploratory notes only unless directly supported by current provider data.

## Deferred Work

- Phase 8 popup/compact redesign around `meters`
- Phase 8 must not fill a missing meter `resetAt` from the top-level `resetAt` (current QML does `line.resetAt || obj.resetAt`)
- Removing compatibility fields `remainingPercent`, `resetAt`, `secondaryRemainingPercent`, and `breakdown`
- Codex OAuth, Claude refresh, new providers, spend/balance/multi-account fields

## Documentation review

Writer thread `ea677843-81df-4425-9d0f-eba542a16bc8` reviewed the contract docs on 2026-10-09. Applied in-scope corrections: provider-contract and cache titles now say Phase 7, Cursor documents a possible single pool, Codex success example is identified as the older one-window capture, Claude extra windows are meters, and the Codex hour/day label order is explicit (48 hours is `2-day limit` because the day rule runs first). The Writer's suggestion that exactly 48 hours falls back to `Usage limit` was not applied: 48 hours is 172800 seconds, a whole number of days.

## Evidence and Handoff

Watcher: **PASS**, attempt 1, `reports/stage-2-phase-7-watcher-1.md` (2026-10-09). No blocking findings.  
Owner decision: **accepted** Phase 7 on 2026-10-09. Snapshot: `docs/handoffs/phase-7.md`.

STOP. Do not start Phase 8.
