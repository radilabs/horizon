# Normalized usage schema (Phase 2)

Version: `1`

This is the only shape the Plasma UI understands. Provider-specific upstream data must not appear here.

## Required fields

| Field | Type | Meaning |
|-------|------|---------|
| `provider` | string | Stable provider id (`codex`, `cursor`, …) |
| `displayName` | string | Human label |
| `plan` | string \| null | Subscription/plan label when known |
| `remainingPercent` | number \| null | Remaining quota 0–100 when known |
| `resetAt` | string \| null | ISO-8601 timestamp with offset when known |
| `status` | string | See statuses below |

## Optional fields

| Field | Type | Meaning |
|-------|------|---------|
| `error` | string | User-safe error text (no secrets) |
| `stale` | boolean | `true` when serving last-successful cache after live failure |
| `fetchedAt` | string | ISO-8601 time when the **successful** payload was originally fetched |
| `secondaryRemainingPercent` | number | Extra window when a provider proves it |
| `breakdown` | array | Optional labeled meters: `{ "label": string, "remainingPercent": number, "resetAt"?: string }[]` (see ADR-0008) |

## Status values

| Status | Meaning |
|--------|---------|
| `ok` | Fresh live success |
| `stale` | Live retrieval failed; returning cached last success |
| `auth_unavailable` | Provider auth missing/expired/unusable; no usable cache |
| `provider_unavailable` | Provider not installed/detectable |
| `upstream_error` | Network/API/schema failure; no usable cache |
| `collector_error` | Internal collector/dispatch failure |

`stale` always implies cached quota fields may be populated and `stale=true`.

## Sanitized success

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": "ChatGPT Plus",
  "remainingPercent": 94,
  "resetAt": "2026-08-17T12:00:00+02:00",
  "status": "ok"
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
  "error": "Current refresh failed"
}
```

## Sanitized Cursor success (multi-meter)

```json
{
  "provider": "cursor",
  "displayName": "Cursor",
  "plan": "Pro",
  "remainingPercent": 98,
  "secondaryRemainingPercent": 100,
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
  ],
  "resetAt": "2026-09-02T21:24:02+02:00",
  "status": "ok"
}
```

## Sanitized StepFun success (rolling-window)

```json
{
  "provider": "stepfun",
  "displayName": "StepFun",
  "plan": "Plus",
  "remainingPercent": 84,
  "secondaryRemainingPercent": 62,
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
  ],
  "resetAt": "2026-04-30T12:00:00+02:00",
  "status": "ok"
}
```

## Forbidden fields

Tokens, cookies, authorization headers, credential paths with secrets, raw upstream API blobs.
