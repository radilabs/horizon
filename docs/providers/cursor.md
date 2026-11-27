# Cursor provider notes (Phase 3, updated Phase 11)

## Cursor installation observed

* Phase 3 observation: Cursor desktop **3.15.6** (Electron/VS Code fork).
* Phase 11 observation (2026-11-27): Cursor desktop **3.28.7** and the Cursor CLI `agent` **2026.11.22-e9042b2**.
* Config homes: `~/.config/Cursor/` (desktop) and `~/.config/cursor/` (CLI).
* Credential sources (both Cursor-owned, both read-only):

| Id | Source | Value used |
|----|--------|-----------|
| **IDE** | `~/.config/Cursor/User/globalStorage/state.vscdb`, `ItemTable` key `cursorAuth/accessToken` | the key's value, only when it is JWT-shaped |
| **CLI** | `~/.config/cursor/auth.json` | the top-level `accessToken` string only |

* Related Electron artifacts that must never enter Git: `Cookies`, `Cookies-journal`, `storage.json`, `state.vscdb*`, and the CLI `auth.json`.

## Authentication / session mechanism

### IDE source (Phase 3 mechanism)

Cursor stores signed-in session material in a **SQLite** database (`state.vscdb`), table `ItemTable` (key/value).

Relevant keys observed (names only; values never logged or committed):

| Key | Role |
|-----|------|
| `cursorAuth/accessToken` | Bearer token for Cursor API calls |
| `cursorAuth/refreshToken` | Present locally; **Horizon does not use or refresh it** |
| `cursorAuth/stripeMembershipType` | Local membership label hint (e.g. `pro`) |
| `cursorAuth/stripeSubscriptionStatus` | Local status hint (e.g. `active`) |

**Phase 11 change.** On desktop **3.28.7**, after a sign-out and sign-in inside the GUI, `cursorAuth/accessToken` is an **opaque, non-JWT value**: it has no dots, three colon-separated parts, and it equals `cursorAuth/refreshToken`. Sending it as `Authorization: Bearer` returned **HTTP 401**. Horizon therefore treats the IDE value as sendable only when it is **JWT-shaped**.

**JWT-shaped** means a non-empty string of exactly three non-empty segments separated by `.`. This is a **shape check only**. Horizon does not decode, parse, verify or inspect any segment or claim, and never exchanges the opaque value for another token.

### CLI source (Phase 11 addition)

`~/.config/cursor/auth.json` is owned by the Cursor CLI `agent`. Horizon reads its top-level `accessToken` only. That value **is** JWT-shaped, and the same usage request with it returned **HTTP 200**. The CLI `refreshToken` is **never** used, sent or kept; if the parser reads the whole JSON object it keeps only `accessToken`.

### Preferred reuse method (implemented)

**Transient read-only access** to both files:

1. Open the DB with SQLite URI `mode=ro` (read-only); open `auth.json` with a plain read-only open.
2. Read the bearer for one attempt into memory only.
3. Call Cursor DashboardService over HTTPS with `Authorization: Bearer <token>`.
4. Discard the token when the process exits; never write tokens to Horizon cache, config, stdout, or docs.

Horizon must **not**:

* write refreshed tokens back into either Cursor file
* copy tokens into `~/.cache/horizon/`
* implement a Cursor login / OAuth / device flow, or run `agent login`, the `agent` binary or the Cursor app
* refresh, rotate or exchange a token
* modify Cursor authentication state
* decode the opaque IDE envelope (no splitting, decrypting, base64 work or exchange)

### Source order and fallback (ADR-0013)

1. If the IDE value exists and is JWT-shaped, send it to `GetCurrentPeriodUsage`.
2. A non-JWT IDE value is **not sent**. It is recorded as `unsupported format` and Horizon moves to the CLI source.
3. Horizon tries the CLI `accessToken` only if (a) the IDE source gave no sendable value, or (b) the IDE attempt returned **HTTP 401 or 403**.
4. **Network errors, non-auth HTTP statuses, non-200 responses, invalid JSON and unexpected response shapes do not fall through.** They stop the fetch as `upstream_error`.
5. The bearer that got **HTTP 200** from `GetCurrentPeriodUsage` is the only one used for `GetPlanInfo`. A `GetPlanInfo` failure still falls back to the local `stripeMembershipType` label, then to `Cursor`, and never triggers a credential fallback.
6. `detect()` raises `auth_unavailable` only when **neither** source file is present.

Optional overrides (testing / unusual layouts only):

* `--auth-file <path>` → treat path as the IDE `state.vscdb`
* `CURSOR_STATE_VSCDB` → alternate IDE state DB path
* `CURSOR_CLI_AUTH_FILE` → alternate CLI `auth.json` path
* `CURSOR_API_BASE` → alternate API origin (failure tests)

Overrides are paths only. Horizon never writes to them and none becomes a credential store.

## Usage / quota mechanism

Internal Connect-RPC-style DashboardService endpoints on `api2.cursor.sh` (unofficial; may change without notice).

Primary:

```text
POST https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage
```

Plan label helper:

```text
POST https://api2.cursor.sh/aiserver.v1.DashboardService/GetPlanInfo
```

### Sanitized request shape

```http
POST /aiserver.v1.DashboardService/GetCurrentPeriodUsage HTTP/1.1
Host: api2.cursor.sh
Authorization: Bearer <redacted>
Content-Type: application/json
Accept: application/json
Connect-Protocol-Version: 1

{}
```

### Sanitized response example

```json
{
  "billingCycleStart": "1756754642000",
  "billingCycleEnd": "1759433042000",
  "planUsage": {
    "totalSpend": 1218,
    "includedSpend": 1218,
    "remaining": 782,
    "limit": 2000,
    "autoPercentUsed": 2.03,
    "apiPercentUsed": 0,
    "totalPercentUsed": 1.89
  },
  "displayMessage": "You've used 61% of your included usage",
  "autoModelSelectedDisplayMessage": "You've used 2% of your included total usage",
  "namedModelSelectedDisplayMessage": "You've used 0% of your included API usage"
}
```

Horizon meters use only `autoPercentUsed` and `apiPercentUsed`. Spend/`remaining`/`limit`/`displayMessage`/`totalPercentUsed` are documented as unused for UI meters.

### Quota semantics (UI meters)

Horizon mirrors the **two** meters on the current Cursor Usage page:

| Cursor UI | Upstream field | Horizon remaining % |
|-----------|----------------|---------------------|
| **Cursor Models** | `planUsage.autoPercentUsed` | `round(100 - autoPercentUsed)` |
| **Other Models** | `planUsage.apiPercentUsed` | `round(100 - apiPercentUsed)` |

* Both pools share the plan **billing cycle** (`billingCycleStart` / `billingCycleEnd`). No separate per-pool reset timestamps were observed in `GetCurrentPeriodUsage`; each breakdown row therefore uses the same `billingCycleEnd`.
* Horizon displays **remaining %**, not used % (Cursor’s UI text says “N% used”).
* Plan label: prefer `GetPlanInfo.planInfo.planName` (e.g. `Pro`); fall back to capitalized local `stripeMembershipType`.

### Observed but unused aggregate fields

These appear in `GetCurrentPeriodUsage` / related messages but are **not** mapped to Horizon meters:

| Observed material | Notes |
|-------------------|--------|
| `planUsage.remaining` / `limit` / `totalSpend` / `includedSpend` | Spend-style allowance numbers (cents-like). Combined they align with `displayMessage` (“You've used N% of your included usage”), **not** with either Cursor Models or Other Models %. |
| `displayMessage` | Human string for that included/spend aggregate. |
| `planUsage.totalPercentUsed` | Numeric field present alongside the two UI pools; value does **not** match the included/spend “N%” in `displayMessage`, nor a clear third UI meter. Treat as **legacy/observed-but-unused**. |
| Literal `includedPercentUsed` | **Not present** in the live DashboardService payload observed here. Do not invent or expose it. |

Do **not**:

* show the included/spend aggregate as a normal quota meter
* use it to calculate Cursor Models or Other Models
* describe it as an official Cursor quota until semantics are proven

If a derived aggregate later proves useful, consider it separately.

Other endpoints observed but not used as primary:

* `GET https://api2.cursor.sh/auth/usage` — older/legacy shape
* `GET https://www.cursor.com/api/usage` / summary paths — not reliable here

## Normalized schema mapping

| Normalized field | Cursor source |
|------------------|---------------|
| `provider` | `"cursor"` |
| `displayName` | `"Cursor"` |
| `plan` | `GetPlanInfo.planInfo.planName` or membership type |
| `meters` / `breakdown` | Cursor Models when `autoPercentUsed` is present, then Other Models when `apiPercentUsed` is present. Either pool may be absent. |
| `remainingPercent` | Compatibility copy of the first meter (Cursor Models when present, otherwise Other Models) |
| `secondaryRemainingPercent` | Compatibility copy of Other Models, only when both pools exist |
| `resetAt` | `billingCycleEnd` (ms → local ISO offset); same value on each meter |
| `status` | `ok` / errors / `stale` via cache |

Intentionally omitted from normalized output:

* included/spend aggregate (`remaining`, `limit`, `totalSpend`, `displayMessage`)
* `totalPercentUsed`
* full `autoBucketModels` list
* any token or email fields

## Cache behavior

Uses the shared XDG cache:

```text
~/.cache/horizon/usage-cursor.json
```

Same rules as Codex: success writes normalized data only; live failure may return `status=stale`.

## Failure behavior

The status vocabulary does not change: `auth_unavailable`, `upstream_error`, and `stale` through the existing cache fallback.

| Condition | Result |
|-----------|--------|
| Neither source file present | `auth_unavailable` (from `detect()`; no HTTP request) |
| No source yields HTTP 200 | `auth_unavailable`, with a per-source message (see below) |
| Network error, non-auth HTTP, non-200, invalid JSON, unexpected shape | `upstream_error` (no credential fallback) |
| Live fail + warm cache | `stale` |
| Live fail + no cache | error status as above |

Cursor failures do not affect the Codex provider path (separate CLI invocations and cache files).

### Per-source outcomes

When no source yields HTTP 200, the result is `auth_unavailable` and the message names each source with one outcome from this fixed set:

| Outcome | Meaning |
|---------|---------|
| `not found` | source file absent |
| `unreadable` | file present but cannot be opened or parsed (SQLite error, OS error, invalid JSON, non-object JSON) |
| `no token` | file readable, but the key or field is absent, empty or not a string |
| `unsupported format` | IDE value present but not JWT-shaped (IDE source only; never sent) |
| `rejected (HTTP 401)` | the API rejected this source's bearer with 401 |
| `rejected (HTTP 403)` | the API rejected this source's bearer with 403 |

Message form:

```text
Cursor usage unauthorized: IDE <outcome>; CLI <outcome>. Sign in to Cursor or the Cursor CLI (agent login).
```

The remediation points the user at Cursor's own tools; Horizon never runs them. Messages never include token text, token lengths or prefixes, segment counts, JWT claims, emails, user ids or response bodies.

## Security constraints

* Credentials remain owned by Cursor, now in **both** files: the IDE `state.vscdb` and the CLI `auth.json`.
* Horizon opens both read-only and never persists tokens.
* Docs and evidence must use redacted/sanitized examples only.
* Repository ignores Cursor session artifacts (see `.gitignore`).

## Upstream fragility

* DashboardService paths and JSON field names are **unofficial** and can break on Cursor updates.
* Both credential files are unofficial Cursor internals. The desktop IDE's `accessToken` became opaque on **3.28.7**, which is why the CLI source exists. Either file's format can change on any Cursor update.
* Horizon does **not** refresh tokens into Cursor storage. If a token is rejected, sign in to Cursor or run the Cursor CLI `agent login`; Horizon does neither.
* `Connect-Protocol-Version: 1` appears required for these POSTs.

## Unknowns / deferred

* A local JWT `exp` check, to skip an expired CLI token without a round trip, is **not** implemented. It is Deferred Work, not current behavior.
* Whether token refresh without writing either Cursor file is worthwhile mid-request → deferred
