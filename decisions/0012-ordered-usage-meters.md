# ADR-0012 — Ordered usage meters

## Status

Accepted (Phase 7). Supersedes the primary/secondary pair as the information model in ADR-0008. ADR-0008 remains the historical reason `breakdown` exists; its text is not rewritten.

## Context

Phase 2 stored one remaining percent. Phase 3 added an optional second percent and an optional `breakdown` list because Cursor shows two pools. Claude (Phase 6.5) can expose more than two independently resetting windows. At Phase 7 the Plasma UI still assumed a primary bar plus an optional row labeled "Secondary" when `breakdown` was absent.

Phase 8 needs a provider-neutral list. It must not hard-code a universal pair, invent Codex's upstream field names as labels, or treat percent-used and percent-remaining as the same number.

## Decision

1. The canonical quota list is ordered `meters`, length 1..N on a successful or stale payload that has quota.
2. Each meter has:
   - `label` — non-empty provider-native display string
   - `remainingPercent` — integer 0–100, percent **remaining**
   - `resetAt` — ISO-8601 timestamp with offset, omitted when unknown
3. Horizon does not emit percent-used. Providers convert upstream used-percent before building meters.
4. Compatibility fields are projections of `meters` and stay on the payload:
   - `remainingPercent` and `resetAt` copy the first meter (`resetAt` is null when the first meter has no reset)
   - `secondaryRemainingPercent` is present only when a second meter exists, and copies that meter's remaining percent
   - `breakdown` is a copy of `meters`
5. Phase 7 left the QML on `breakdown` and the compatibility percents. Phase 8's expanded popup reads `meters` first and does not borrow a missing meter reset from the top-level `resetAt`. The compact panel and tooltip still use the compatibility percents.
6. Codex has no upstream display name. Labels come only from `limit_window_seconds`, in this order: `18000` → `5-hour limit`; `604800` → `Weekly limit`; any other positive multiple of 86400 → `{n}-day limit` (86400 is `1-day limit`, and 48 hours is `2-day limit`); any other positive multiple of 3600 that is under 48 hours → `{n}-hour limit`; otherwise `Usage limit`. Windows are not labeled Primary or Secondary. Duplicate labels are allowed; list order distinguishes them. Each window keeps its own `resetAt`.
7. Cursor meters stay `Cursor Models` and `Other Models`. Either pool may be absent, so a success payload can contain one meter. Integer rounding and clamping stay as each provider already implements them. The included/spend aggregate is not a meter. StepFun keeps `5-Hour Usage`, `Weekly Usage`, and the existing credit labels. Claude keeps Claude Code's window titles, in that order, including windows after the second. `seven_day_breakdown`, disabled `spend`, and `limits[]` are not meters.
8. Top-level fields that are not meters: `provider`, `displayName`, `plan` (null when unknown; never invented), `status`, `error`, `stale`, and `fetchedAt`. Failure payloads stay the existing `error_payload` shape and omit `meters`. They do not gain new null fields and do not invent 0% bars.
9. The cache allowlist includes `meters`. A stale read of a pre-Phase-7 cache rebuilds `meters` from `breakdown` when present, otherwise from the primary percent plus its payload reset, and from `secondaryRemainingPercent` as a second `Usage limit` meter with no reset. That rebuild does not add `breakdown`, so the legacy fallback path is still reachable for old Codex cache.
10. `remainingPercent`, `resetAt`, `secondaryRemainingPercent`, and `breakdown` are compatibility fields. Removing them is deferred. For Cursor, StepFun, and Claude their values must stay the same as before Phase 7.

## Consequences

* Phase 8 can render `meters` in order and ignore the primary/secondary pair.
* Phase 8's expanded popup reads `meters`, then `breakdown`, then the primary/secondary compatibility fields. A meter shows a reset only when that meter has its own `resetAt`; the top-level `resetAt` is never borrowed for a meter that lacks one. In the legacy primary/secondary fallback the first row carries the payload reset and the second has none.
* The Phase 8 popup does not change the compact panel, `compactText`, or `tooltipSummary`. Those still derive from the compatibility percents and `breakdown`, and stay a Phase 9 concern.
* Future balance, spend, rate-limit, and multi-account fields are not part of this contract.
