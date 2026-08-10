# Cursor provider notes (Phase 3)

## Cursor installation observed

* Cursor version: **3.15.6** (desktop; Electron/VS Code fork)
* Config home: `~/.config/Cursor/`
* Relevant auth/session store:
  `~/.config/Cursor/User/globalStorage/state.vscdb`
* Related Electron artifacts that must never enter Git: `Cookies`, `Cookies-journal`, `storage.json`, `state.vscdb*`

## Authentication / session mechanism

Cursor stores signed-in session material in a **SQLite** database (`state.vscdb`), table `ItemTable` (key/value).

Relevant keys observed (names only; values never logged or committed):

| Key | Role |
|-----|------|
| `cursorAuth/accessToken` | Bearer token for Cursor API calls |
| `cursorAuth/refreshToken` | Present locally; **Horizon does not use or refresh it** |
| `cursorAuth/stripeMembershipType` | Local membership label hint (e.g. `pro`) |
| `cursorAuth/stripeSubscriptionStatus` | Local status hint (e.g. `active`) |

Not used by Horizon:

* OS keyring / KWallet
* A Horizon-owned Cursor credential store
* Browser cookie jars as the primary auth source for this integration

### Preferred reuse method (implemented)

**Transient read-only access** to `state.vscdb`:

1. Open the DB with SQLite URI `mode=ro` (read-only).
2. Read `cursorAuth/accessToken` into memory for the request.
3. Call Cursor DashboardService over HTTPS with `Authorization: Bearer <token>`.
4. Discard the token when the process exits; never write tokens to Horizon cache, config, stdout, or docs.

Horizon must **not**:

* write refreshed tokens back into Cursor’s DB
* copy tokens into `~/.cache/horizon/`
* implement a Cursor login / OAuth flow
* modify Cursor authentication state

Optional overrides (testing / unusual layouts only):

* `--auth-file <path>` → treat path as `state.vscdb`
* `CURSOR_STATE_VSCDB` → alternate state DB path
* `CURSOR_API_BASE` → alternate API origin (failure tests)

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
| `plan` | `GetPlanInfo.planName` or membership type |
| `remainingPercent` | **Cursor Models**: `round(100 - autoPercentUsed)` |
| `secondaryRemainingPercent` | **Other Models**: `round(100 - apiPercentUsed)` |
| `breakdown[0]` | Cursor Models (+ shared `resetAt`) |
| `breakdown[1]` | Other Models (+ shared `resetAt`) |
| `resetAt` | `billingCycleEnd` (ms → local ISO offset); same value on each breakdown line |
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

| Condition | Result |
|-----------|--------|
| Missing/unreadable `state.vscdb` or missing access token | `auth_unavailable` |
| HTTP 401/403 from usage API | `auth_unavailable` |
| Network / non-auth HTTP / bad JSON | `upstream_error` |
| Live fail + warm cache | `stale` |
| Live fail + no cache | error status as above |

Cursor failures do not affect the Codex provider path (separate CLI invocations and cache files).

## Security constraints

* Credentials remain owned by Cursor (`state.vscdb`).
* Horizon opens the DB read-only and never persists tokens.
* Docs and evidence must use redacted/sanitized examples only.
* Repository ignores Cursor session artifacts (see `.gitignore`).

## Upstream fragility

* DashboardService paths and JSON field names are **unofficial** and can break on Cursor updates.
* Access tokens expire; Horizon does **not** refresh them into Cursor storage. If the token is expired, the user must re-authenticate inside Cursor.
* `Connect-Protocol-Version: 1` appears required for these POSTs.

## Unknowns / deferred

* Whether token refresh without writing Cursor’s DB is worthwhile mid-request → deferred
* StepFun → Phase 4
