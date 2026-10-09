# Claude provider notes (Phase 6.5)

Observed 2026-10-09 on the development machine against Claude Code **2.1.295** and a live Claude Pro subscription. The usage endpoint is unofficial and can change without notice.

## Credential source

Claude Code owns the session file:

* Path: `~/.claude/.credentials.json`
* Mode observed: `0600`
* Top-level key: `claudeAiOauth`

Sanitized field names (values never logged):

| Field | Role |
|-------|------|
| `accessToken` | Bearer token for the usage request. Held in memory only. |
| `refreshToken` | Present locally. **Horizon does not read it for requests and does not refresh it.** |
| `expiresAt` | Access-token expiry, unix milliseconds |
| `refreshTokenExpiresAt` | Present locally. Unused. |
| `scopes` | Includes `user:inference` on the observed login |
| `subscriptionType` | Plan hint (`pro` observed → display label `Pro`) |
| `rateLimitTier` | Present (`default_claude_ai` observed). Unused for quota math. |

Horizon opens the file with `O_RDONLY`. It never writes, rotates, or copies the file, and it never stores Claude credentials in KWallet, Plasma config, the usage cache, argv, or logs.

Optional overrides (tests and unusual layouts only):

* `--auth-file <path>` → alternate credentials JSON
* `CLAUDE_CREDENTIALS_FILE` → same
* `CLAUDE_API_BASE` → alternate API origin

## Usage mechanism

```text
GET https://api.anthropic.com/api/oauth/usage
```

Required headers:

```http
GET /api/oauth/usage HTTP/1.1
Host: api.anthropic.com
Authorization: Bearer <redacted>
anthropic-beta: oauth-2025-04-20
Accept: application/json
```

`anthropic-beta: oauth-2025-04-20` is the beta Claude Code 2.1.295 sends for OAuth API calls. A Horizon `User-Agent` of `horizon-ai-usage` was accepted on the live Pro account (HTTP 200).

One `fetch_usage` performs one GET. `force_refresh` does not add a request and does not call `/v1/oauth/token`.

### Utilization

Named windows use `utilization` as **percent used, 0–100**, not a 0–1 fraction. The live Pro response reported `five_hour.utilization` of `1.0`, which is 1% used (99% remaining), matching `limits[].percent` of `1` for the session window.

`resets_at` is an ISO-8601 timestamp with a numeric offset.

### Windows Claude Code shows

Claude Code 2.1.295 titles, in dialog order. Horizon uses these labels when the window object contains a numeric `utilization`. Null windows are omitted.

| Payload key | Claude Code label | Live Pro account (2026-10-09) |
|-------------|-------------------|--------------------------------|
| `five_hour` | Current session | present, utilization 1, reset `2026-10-09T13:59:59Z` (second fetch later the same hour) |
| `seven_day` | Current week (all models) | present, utilization 22, reset `2026-10-12T01:59:59Z` |
| `seven_day_opus` | Opus limit | null |
| `seven_day_sonnet` | Current week (Sonnet only) | null |
| `seven_day_oauth_apps` | OAuth apps limit | null |
| `seven_day_cowork` | Cowork limit | null |
| `seven_day_omelette` | Omelette limit | null |
| `seven_day_overage_included` | Fable limit | null |

The first present window in that order (session, when present) is `meters[0]`. Every later present window is another meter, including windows after the second. `breakdown` is a copy of `meters`. `remainingPercent` copies the first meter. `secondaryRemainingPercent` copies only the second meter and is not a cap on the list.

Additional payload keys that were **null** on this account and are not quota bars unless a future response gives them a numeric `utilization`: `tangelo`, `iguana_necktie`, `omelette_promotional`, `nimbus_quill`, `cinder_cove`, `copper_kite`, `brass_thimble`, `harbor_lantern`, `wattle_ember`, `amber_ladder`, `amber_cistern`, `juniper_tide`, `cedar_ember`, `amber_gauge`. If one of those objects later includes `utilization`, Horizon keeps it as an extra meter and prefers a short `label` field when the payload has one. Claude Code itself special-cases `cinder_cove` (“Claude Code and Cowork credit”) and `wattle_ember` (its own `label`, else “Credit”).

`extra_usage` is a spend/credit block (`is_enabled`, `monthly_limit`, `used_credits`, `utilization`, …). It was disabled on this account. Horizon adds an “Extra usage” row only when `is_enabled` is true and `utilization` is numeric.

### Not quota meters

These were present and are documented for Phase 7. Horizon does not map them as remaining-quota bars:

* `limits[]` — server summary that mirrored the named windows (`kind=session` / `weekly_all`, same percents and reset times).
* `seven_day_breakdown` — composition of the weekly window by surface (`Claude Code` 93, `Chats` 3, `Cowork` 4, `Other` 0). Percents are shares of usage, not remaining quota.
* `spend` — extra-credit balance. `enabled` was false. Includes a disclaimer string that is not a quota.
* `weekly_scoped_shares` — null.
* `member_dashboard_available` — false.

Dollar fields (`limit_dollars`, `used_dollars`, `remaining_dollars`) were null and are not copied into the normalized schema.

## Failure behavior

| Condition | Result |
|-----------|--------|
| Credentials file missing | `auth_unavailable`. No file is created. |
| Access token missing, or `expiresAt` already past | `auth_unavailable`. No HTTP call. No refresh. |
| Usage HTTP 401 or 403 | `auth_unavailable`. File bytes unchanged. Live check with a fake token returned HTTP 401. |
| Other HTTP errors, network errors, or no utilization windows | `upstream_error` |

User-facing text tells the user to re-authenticate in Claude Code. Horizon does not start a Claude login and does not refresh the OAuth token.

## Normalized example

```json
{
  "provider": "claude",
  "displayName": "Claude",
  "plan": "Pro",
  "remainingPercent": 99,
  "secondaryRemainingPercent": 78,
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
  ],
  "resetAt": "2026-10-09T14:00:00+00:00",
  "status": "ok"
}
```

## Fragility

This is an unofficial Claude.ai OAuth usage route used by Claude Code, not a documented Anthropic Console billing API. Window names, the `oauth-2025-04-20` beta header, and null experimental keys can change. Horizon’s Max/Opus/Sonnet rows are implemented from the Claude Code 2.1.295 labels and covered by fixtures; this Pro account did not return those windows live.
