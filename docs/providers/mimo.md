# Xiaomi MiMo Token Plan provider notes (Phase 12)

The Xiaomi MiMo Token Plan is a subscription pool of **credits** for AI coding work. Horizon shows what is left of that pool as one meter. Discovery record: `docs/research/xiaomi-mimo-coding-plan.md`.

The quota endpoint is part of Xiaomi's official API reference (Finance → "Query Token Plan Credits"), unlike the unofficial endpoints used by the Codex, Cursor and StepFun providers. It still consumes no credits and returns read-only data.

## Credential source

There is no provider-owned local credential file Horizon may read. The Token Plan key is **user-supplied** and lives only in the OS credential store (ADR-0009), the same pattern as StepFun:

* KWallet wallet `kdewallet`, folder `Horizon`, entry `mimo/token-plan-key`
* Horizon never reads `XIAOMI_API_KEY`, `MIMO_API_KEY`, or any other environment variable for the key
* Horizon never parses `~/.bashrc` or any shell profile
* Horizon never reads MiMo-Code credentials (`~/.local/share/mimocode/auth.json`) or MiMo-Code config (`~/.config/mimocode/`)
* Horizon writes no plaintext file and has no CLI flag that carries the key

### Key shape check

The stored value is accepted only when it is a non-empty string that starts with `tp-`, contains no whitespace, and is 8–256 characters long. Horizon does not decode the key and does not check its expiry. Anything else is rejected without echoing the value.

### Managing the key

```bash
ai-usage auth mimo set       # non-echo TTY prompt, or one stdin line when not a TTY
ai-usage auth mimo status    # working | auth_failed | unavailable | missing
ai-usage auth mimo clear     # prints cleared
ai-usage status mimo --json
```

`--region {sgp,cn,ams}` is accepted by `status` and `auth`, defaults to `sgp`, and is used only by `mimo`.

`set` and `status` each verify with **one** usage GET to the configured region, so the status word reflects a live answer, not merely that KWallet has an entry. The printed word means:

| Word | Meaning |
|------|---------|
| `working` | The key was accepted and a usage payload was read |
| `auth_failed` | Xiaomi rejected the key (`auth_unavailable`, including HTTP 401) |
| `unavailable` | Network, upstream, or collector failure. The stored key is kept |
| `missing` | No key is stored (`status` only) |
| `cleared` | The stored key was deleted (`clear` only) |
| `invalid` | The value failed the shape check (`set` only). Nothing is stored |

The settings helper (`collector/mimo_auth_helper.py`, used by the widget's MiMo credential section) prints the same words, plus `empty` (clipboard was empty) and `store_error` (KWallet unreachable). It reads the clipboard with `wl-paste`, falling back to Klipper over `qdbus6`. After a save attempt that stored a key and then returned `working`, `auth_failed`, or `unavailable`, it clears the clipboard. The key never appears in process arguments.

## Endpoint

One `GET` per fetch, and no other request:

```http
GET /v1/platform/token_plan HTTP/1.1
Host: token-plan-{region}.xiaomimimo.com
Authorization: Bearer <tp- key>
Accept: application/json
```

The whole URL is `https://token-plan-{region}.xiaomimimo.com/v1/platform/token_plan`. `MIMO_API_BASE` replaces the origin for offline tests only; it never adds a region fallback.

### Region

The region is explicit configuration: `sgp`, `cn`, or `ams`, defaulting to `sgp`. It is set in widget settings (MiMo region) or on the CLI with `--region`. Regions are **never probed** — a key is bound to one regional host, and a wrong region answers HTTP 401 exactly like a bad key. Horizon sends the key to the configured host only, and an unsupported region is rejected before any request.

## Usage mechanism

One `fetch_usage` performs one GET. `force_refresh` does not add a request.

Observed response shape (values omitted):

```json
{
  "object": "token_plan",
  "plan_code": "lite:year",
  "period": {
    "start_at": "2026-11-27 00:00:00",
    "end_at": "2027-11-27 23:59:59"
  },
  "quota": {
    "total_credits": 0,
    "used_credits": 0,
    "remaining_credits": 0
  },
  "auto_renew": false,
  "claw_enabled": false
}
```

`start_at` / `end_at` are 19-character UTC strings with no `T` and no offset. `total_credits` includes Xiaomi's compensation credits.

## Meters

Exactly one meter, following the ADR-0012 ordered `meters` contract (Phase 7):

| Horizon field | MiMo source |
|---------------|-------------|
| `meters[0].label` | Constant `Credits` |
| `meters[0].remainingPercent` | `max(0, min(100, round(remaining_credits / total_credits * 100)))` |
| `meters[0].resetAt` | `period.end_at`, parsed as UTC, stored as ISO-8601 with `+00:00` |
| `plan` | Mapped from `plan_code` (see below) |
| `remainingPercent` | Compatibility copy of the one meter |
| `secondaryRemainingPercent` | Absent. There is no second meter |
| `breakdown` | Compatibility copy of `meters` |

`remaining_credits` is clamped to `0..total_credits` before the division, so a negative or oversized value cannot produce a percent outside 0–100. When `remaining_credits` is absent, `used_credits` is used instead and the remaining value is `max(0, total_credits - used_credits)`.

Absolute credit counts are **not** shown. Horizon shows the percent remaining, not the number of credits.

### Annual plans

`resetAt` is Xiaomi's `period.end_at`. For an annual plan that is the plan expiry or renewal, about a year away, and **not** a monthly refill. Xiaomi reports one pool per billing period with no daily, weekly, or monthly sub-reset, and Horizon does not invent one. When `period.end_at` is missing or unparseable the meter keeps its percent and simply omits `resetAt`.

### Plan names

`plan_code` is a code, not a display name. Documented tiers and periods map to readable names:

| `plan_code` | Displayed `plan` |
|-------------|------------------|
| `lite` | `Lite` |
| `standard` | `Standard` |
| `pro` | `Pro` |
| `max` | `Max` |
| `lite:year` | `Lite · Annual` |
| `lite:month` | `Lite · Monthly` |
| anything else | the raw code, preserved |
| missing or empty | `null` |

Unknown tiers, and known tiers with an unknown suffix, are **preserved**: the raw code is trimmed, limited to printable characters, and truncated to 64 characters, then shown as is. It is never dropped and never replaced with a guess. Mapping is case-insensitive.

## Failure behavior

| Condition | Result |
|-----------|--------|
| No key in KWallet | `auth_unavailable` |
| KWallet unreachable | `auth_unavailable` |
| Stored value fails the `tp-` shape check | `auth_unavailable` |
| HTTP 401 | `auth_unavailable`, naming the configured region and telling the user to check the key and the region |
| Any other non-200 status, including HTTP 403 | `upstream_error` |
| Network error, timeout | `upstream_error` |
| Invalid JSON, or a body that is not an object | `upstream_error` |
| Missing `quota`, or `total_credits` missing, non-integer, or `<= 0` | `upstream_error`, with no meter and no 0% bar |
| `remaining_credits` invalid and `used_credits` missing or invalid | `upstream_error` |

No new status code is introduced. The existing `stale` fallback applies unchanged: a warm cache from an earlier manual refresh is shown as `stale` when a later fetch fails.

## Fetch timing: manual refresh only

MiMo is fetched **only** when the user asks:

* the popup **Refresh** button (click, `Space`, `Return`, `Enter`);
* the `F5` shortcut;
* `ai-usage status mimo` run by hand;
* `ai-usage auth mimo set` / `status`, which each perform their own single verify GET.

The interval timer, widget startup, popup open, and configuration changes (including `enableMimo` and `mimoRegion`) **never** fetch MiMo. A MiMo result already in the model, or the stale cache fallback, may still be shown. The rule lives in `MeterIntake.js` (`MANUAL_ONLY_PROVIDERS`), which `refreshIds(enabledIds, manual)` applies.

Reason: Xiaomi's Token Plan subscription terms say the quota "is only available for use in programming tools" and prohibit "API calls for request behaviors in obvious non-coding scenarios … such as automated scripts and custom application backends" (`https://mimo.mi.com/static/docs/tokenplan/Token%20Plan/subscription.md`). That text does not clearly permit unattended polling, so Horizon leaves MiMo polling to the user.

MiMo is also **disabled by default**: `enableMimo` defaults to `false` in `plasmoid/contents/config/main.xml`. Until it is enabled and a key is stored, the idle MiMo row shows a manual-refresh hint instead of making requests.

## Cache

`~/.cache/horizon/usage-mimo.json` — normalized non-secret fields only. Never the `tp-` key, the raw upstream body, or absolute credit counts.

## Out of scope

* Console/dashboard endpoints (`platform.xiaomimimo.com/api/v1/tokenPlan/*`), browser cookies, or Xiaomi Account SSO
* Pay-as-you-go balance, daily consumption, or bill endpoints (cash, not quota)
* Any inference call, or any call that consumes credits
* Team seats, multiple keys, multiple regions, or per-model breakdowns (Xiaomi reports one shared pool)
* Reading MiMo-Code credentials
* Reading the key from the environment or shell profiles
* A new authentication framework, or any change to the other providers

## Upstream fragility

The Token Plan credits endpoint is recent (it appeared after 2026-09-22 and before 2026-11-11). Its path, response fields, region hosts, and the full `plan_code` vocabulary can change. Keys are region-bound, so a wrong region is indistinguishable from a rejected key. Horizon reports those as `auth_unavailable` and leaves the diagnosis to the user.
