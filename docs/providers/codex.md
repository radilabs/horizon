# Codex provider notes (Phase 1)

## Codex installation observed

* Config home: `~/.codex` (`CODEX_HOME` override supported)
* Auth file: `~/.codex/auth.json` (mode `0600`)
* `codex` CLI binary was **not** on `PATH` on the Phase 1 development machine; auth artifacts from a prior Codex ChatGPT login were present
* Config (`config.toml`) selects models/plugins only; it does not store tokens

## Authentication mechanism

* `auth_mode`: `chatgpt` (ChatGPT subscription OAuth, not API key)
* File-backed tokens under `tokens`:
  * `access_token`
  * `refresh_token`
  * `id_token`
  * `account_id`
* `last_refresh`: timestamp of last successful refresh
* `OPENAI_API_KEY`: null for this account
* No system keyring / KDE Wallet usage observed for Codex on this machine (Secret Service tools not used by Codex auth here)

### Preferred reuse method (implemented)

**Outcome C — transient read of existing Codex credential file**, with optional in-place refresh of `~/.codex/auth.json` using the same OAuth client id as the official Codex CLI.

Horizon / `ai-usage` does **not** create Horizon-owned credential storage.

Order attempted:

1. Codex CLI as auth broker — unavailable (`codex` not on PATH)
2. OS keyring — not used by local Codex auth
3. Transient read of `~/.codex/auth.json` (+ refresh write-back to that same Codex file) — **used**
4. Horizon-owned credential storage — not permitted / not used

### Token refresh

* Endpoint: `POST https://auth.openai.com/oauth/token`
* Body (JSON): `{ "client_id": "app_EMoamEEZ73f0CkXaXp7hrann", "grant_type": "refresh_token", "refresh_token": "…" }`
* Client id matches official Codex CLI (`codex-rs` login manager)
* On success, updated tokens are written atomically back to `~/.codex/auth.json` only
* Access tokens expire; refresh tokens rotate

## Usage / quota mechanism

Unofficial ChatGPT backend endpoint used by multiple local trackers and matching Codex web usage UI:

* `GET https://chatgpt.com/backend-api/wham/usage`
* Headers (non-secret):
  * `Authorization: Bearer <access_token>`
  * `ChatGPT-Account-ID: <account_id>` when present
  * `Referer: https://chatgpt.com/codex/settings/usage`
  * browser-like `User-Agent`
* Auth context: ChatGPT OAuth access token from local Codex auth

### Sanitized request shape

```http
GET /backend-api/wham/usage HTTP/1.1
Host: chatgpt.com
Authorization: Bearer <redacted>
ChatGPT-Account-ID: <redacted-uuid>
Accept: application/json
Referer: https://chatgpt.com/codex/settings/usage
```

### Sanitized example response

```json
{
  "plan_type": "plus",
  "rate_limit": {
    "allowed": true,
    "limit_reached": false,
    "primary_window": {
      "used_percent": 6,
      "limit_window_seconds": 604800,
      "reset_after_seconds": 568028,
      "reset_at": 1786953460
    },
    "secondary_window": null
  }
}
```

Identifiers such as email / user ids may appear upstream; Horizon drops them from normalized output.

### Quota windows

* **Primary window**: present; `used_percent` + `reset_at` (unix seconds). On the tested Plus account the primary window length was 604800s (7 days). Other accounts/plans may expose a ~5h primary and weekly secondary (as seen in community trackers).
* **Secondary window**: null on the tested account; when present, optional `secondaryRemainingPercent` may be included in collector JSON but is not required by the Phase 0/1 UI.
* Remaining percentage for Horizon = `100 - used_percent` (clamped 0–100).

### Upstream → Horizon mapping

| Upstream | Horizon field |
|----------|---------------|
| (constant) | `provider`: `codex` |
| (constant) | `displayName`: `Codex` |
| `plan_type` | `plan` (`plus` → `ChatGPT Plus`, etc.) |
| `100 - rate_limit.primary_window.used_percent` | `remainingPercent` |
| `rate_limit.primary_window.reset_at` | `resetAt` (ISO-8601 local offset) |
| success | `status`: `ok` |

### Fragility

* Endpoint is unofficial / private; fields and URL may change without notice
* Depends on ChatGPT subscription Codex access
* Requires valid local Codex login artifacts
* Concurrent refreshers could race on `auth.json` (refresh token rotation)

### External references (adapted, not vendored)

* [nick-ma/show-codex-usage](https://github.com/nick-ma/show-codex-usage) — `wham/usage` + local `auth.json`
* Official Codex CLI OAuth refresh client id / URL (public source)

## Normalized collector contract

Command:

```bash
ai-usage status codex --json
```

### Success

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": "ChatGPT Plus",
  "remainingPercent": 94,
  "resetAt": "2026-08-17T09:57:40+02:00",
  "status": "ok"
}
```

Exit code `0`. Secrets never appear in stdout.

### Failure

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": null,
  "remainingPercent": null,
  "resetAt": null,
  "status": "auth_unavailable",
  "error": "Codex auth file not found: /tmp/horizon-no-auth.json"
}
```

Exit code non-zero. `status` values used in Phase 1:

* `auth_unavailable`
* `upstream_error`
* `collector_error`

Intentionally ignored upstream fields: email, user ids, credits/spend details, promo blobs, raw token material.

## Collector invocation

* Implementation: `collector/ai-usage` with `collector/providers/codex.py`
* Selected via explicit registry (`PROVIDERS["codex"] = CodexProvider`)
* Recommended install: symlink to `~/.local/bin/ai-usage`
* Plasmoid executes: `$HOME/.local/bin/ai-usage status codex --json`
* Last-successful cache: `~/.cache/horizon/usage-codex.json` (normalized only)

## Authentication / storage conclusion (P1-T7)

**Outcome C** — existing Codex credential file, read transiently; refresh updates Codex’s own `auth.json` only.

Horizon stores no provider credentials. Phase 2 may cache **normalized non-secret** usage only.