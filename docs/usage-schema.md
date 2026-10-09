# Normalized usage schema (Phase 7)

Contract version: `2` (Phase 7, ADR-0012). Version `1` was the Phase 2 payload plus the optional Phase 3 `breakdown` list.

This is the only shape the Plasma UI understands. Provider-specific upstream data must not appear here. The popup, compact panel, and tooltip read `meters` when that list is present, then `breakdown`, then the primary/secondary fields. A missing meter reset is not copied from the top-level `resetAt`. The compact summary uses the lowest remaining percent above 0, and counts meters at 0 separately.

## Canonical meter

`meters` is an ordered list of the provider's displayable quota windows. Length is 1..N when quota is known. Each meter:

| Field | Type | Meaning |
|-------|------|---------|
| `label` | string | Provider-native human label. Required and non-empty on new payloads. |
| `remainingPercent` | integer | Percent **remaining**, 0–100. Never percent used. |
| `resetAt` | string | ISO-8601 timestamp with offset. Omitted when that meter has no known reset. |

Meters reset independently when the provider says so. A missing reset is unknown, not "same as the first meter", unless the provider evidence says the resets are shared (Cursor's billing cycle).

Do not add a used-percent field. Do not invent 0% meters for missing windows.

## Required payload fields

| Field | Type | Meaning |
|-------|------|---------|
| `provider` | string | Stable provider id (`codex`, `cursor`, `stepfun`, `claude`) |
| `displayName` | string | Human label |
| `plan` | string \| null | Subscription/plan label when known |
| `remainingPercent` | number \| null | Compatibility copy of `meters[0].remainingPercent`, or null when no quota |
| `resetAt` | string \| null | Compatibility copy of the first meter's reset, or null |
| `status` | string | See statuses below |

Successful and stale payloads that have quota also include `meters`.

## Compatibility fields

These stay so current CLI output, cache, and QML keep working (ADR-0012). They are projections, not a second model.

| Field | Type | Meaning |
|-------|------|---------|
| `secondaryRemainingPercent` | number | Present only when a second meter exists. Copies `meters[1].remainingPercent`. It has no label and no reset of its own. |
| `breakdown` | array | Copy of `meters`. The popup uses it only when `meters` is absent. |
| `error` | string | User-safe error text (no secrets) |
| `stale` | boolean | `true` when serving last-successful cache after live failure |
| `fetchedAt` | string | ISO-8601 time when the **successful** payload was originally fetched |

Pre-Phase-7 cache may lack `meters`. On a stale read the collector rebuilds `meters`: from `breakdown` when that list exists, otherwise one `Usage limit` meter from `remainingPercent` (keeping the payload reset) and, when `secondaryRemainingPercent` exists, a second `Usage limit` meter with no reset. Duplicate labels are allowed; order distinguishes them. The popup applies the same fallback order when `meters` is absent, so a legacy payload renders as labeled meters rather than a blank label plus "Secondary".

## Status values

| Status | Meaning |
|--------|---------|
| `ok` | Fresh live success |
| `stale` | Live retrieval failed; returning cached last success |
| `auth_unavailable` | Provider auth missing/expired/unusable; no usable cache |
| `provider_unavailable` | Provider not installed/detectable |
| `upstream_error` | Network/API/schema failure; no usable cache |
| `collector_error` | Internal collector/dispatch failure |

Failure statuses omit `meters`. Quota fields are null. They do not fabricate a plan, a reset, or a 0% bar.

`stale` copies the cached meters and sets `stale=true`.

## Provider meter labels

| Provider | Meters | Not meters |
|----------|--------|------------|
| Codex | Duration label from `limit_window_seconds`: `5-hour limit` (18000), `Weekly limit` (604800), then any other whole number of days as `{n}-day limit` (86400 is `1-day limit`; 48 hours is `2-day limit`), then a whole number of hours that is not a whole number of days and is under 48 hours as `{n}-hour limit`, otherwise `Usage limit`. Never `Primary` or `Secondary`. Duplicate labels stay; order distinguishes them. | Email, account ids, credits/spend |
| Cursor | `Cursor Models` when `autoPercentUsed` is present, `Other Models` when `apiPercentUsed` is present. Either pool may be absent, so a successful payload can have one meter. Shared billing-cycle reset when both exist. | Included/spend aggregate, `displayMessage`, `totalPercentUsed` |
| StepFun | `5-Hour Usage` and `Weekly Usage`, or the credit labels `Credits`, `Subscription Credits`, `Top-up Credits` | Raw Oasis token, WebID |
| Claude | Claude Code window titles, in that order, including windows after the second. `Extra usage` only when enabled. | `limits[]` (a mirror), `seven_day_breakdown` (surface mix, not remaining quota), disabled `spend` |

Upstream Claude `utilization` and Cursor `*PercentUsed` are percent **used**. Horizon stores percent remaining: `round(100 - used)`, clamped to 0–100. A Claude utilization of `1.0` is 1% used and 99% remaining.

## Sanitized Codex success

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": "ChatGPT Plus",
  "remainingPercent": 94,
  "resetAt": "2026-08-17T12:00:00+02:00",
  "status": "ok",
  "meters": [
    {
      "label": "Weekly limit",
      "remainingPercent": 94,
      "resetAt": "2026-08-17T12:00:00+02:00"
    }
  ],
  "breakdown": [
    {
      "label": "Weekly limit",
      "remainingPercent": 94,
      "resetAt": "2026-08-17T12:00:00+02:00"
    }
  ]
}
```

## Sanitized failure

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": null,
  "remainingPercent": null,
  "resetAt": null,
  "status": "auth_unavailable",
  "error": "Codex auth file not found"
}
```

## Sanitized stale fallback

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": "ChatGPT Plus",
  "remainingPercent": 94,
  "resetAt": "2026-08-17T12:00:00+02:00",
  "status": "stale",
  "stale": true,
  "fetchedAt": "2026-08-10T20:30:00+02:00",
  "error": "Current refresh failed",
  "meters": [
    {
      "label": "Weekly limit",
      "remainingPercent": 94,
      "resetAt": "2026-08-17T12:00:00+02:00"
    }
  ],
  "breakdown": [
    {
      "label": "Weekly limit",
      "remainingPercent": 94,
      "resetAt": "2026-08-17T12:00:00+02:00"
    }
  ]
}
```

## Sanitized Cursor success

```json
{
  "provider": "cursor",
  "displayName": "Cursor",
  "plan": "Pro",
  "remainingPercent": 98,
  "secondaryRemainingPercent": 100,
  "resetAt": "2026-09-02T21:24:02+02:00",
  "status": "ok",
  "meters": [
    {
      "label": "Cursor Models",
      "remainingPercent": 98,
      "resetAt": "2026-09-02T21:24:02+02:00"
    },
    {
      "label": "Other Models",
      "remainingPercent": 100,
      "resetAt": "2026-09-02T21:24:02+02:00"
    }
  ],
  "breakdown": [
    {
      "label": "Cursor Models",
      "remainingPercent": 98,
      "resetAt": "2026-09-02T21:24:02+02:00"
    },
    {
      "label": "Other Models",
      "remainingPercent": 100,
      "resetAt": "2026-09-02T21:24:02+02:00"
    }
  ]
}
```

## Sanitized StepFun success

```json
{
  "provider": "stepfun",
  "displayName": "StepFun",
  "plan": "Plus",
  "remainingPercent": 84,
  "secondaryRemainingPercent": 62,
  "resetAt": "2026-04-30T12:00:00+02:00",
  "status": "ok",
  "meters": [
    {
      "label": "5-Hour Usage",
      "remainingPercent": 84,
      "resetAt": "2026-04-30T12:00:00+02:00"
    },
    {
      "label": "Weekly Usage",
      "remainingPercent": 62,
      "resetAt": "2026-05-05T12:00:00+02:00"
    }
  ],
  "breakdown": [
    {
      "label": "5-Hour Usage",
      "remainingPercent": 84,
      "resetAt": "2026-04-30T12:00:00+02:00"
    },
    {
      "label": "Weekly Usage",
      "remainingPercent": 62,
      "resetAt": "2026-05-05T12:00:00+02:00"
    }
  ]
}
```

## Sanitized Claude success

`utilization` on the Claude usage payload is percent **used**. Session is the first meter when present. Further windows stay in `meters`; `secondaryRemainingPercent` is only the second meter.

```json
{
  "provider": "claude",
  "displayName": "Claude",
  "plan": "Pro",
  "remainingPercent": 99,
  "secondaryRemainingPercent": 78,
  "resetAt": "2026-10-09T14:00:00+00:00",
  "status": "ok",
  "meters": [
    {
      "label": "Current session",
      "remainingPercent": 99,
      "resetAt": "2026-10-09T14:00:00+00:00"
    },
    {
      "label": "Current week (all models)",
      "remainingPercent": 78,
      "resetAt": "2026-10-12T02:00:00+00:00"
    }
  ],
  "breakdown": [
    {
      "label": "Current session",
      "remainingPercent": 99,
      "resetAt": "2026-10-09T14:00:00+00:00"
    },
    {
      "label": "Current week (all models)",
      "remainingPercent": 78,
      "resetAt": "2026-10-12T02:00:00+00:00"
    }
  ]
}
```

## Out of contract

Not represented, and not to be added without a later authorized phase: account balances, dollar spend, rate-limit policy objects, multiple accounts per provider, and Claude's weekly surface composition (`seven_day_breakdown`).

## Forbidden fields

Tokens, cookies, authorization headers, credential paths with secrets, raw upstream API blobs.
