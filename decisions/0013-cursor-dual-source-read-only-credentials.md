# ADR-0013 — Cursor credentials: two read-only, Cursor-owned sources

## Status

Accepted (owner-approved 2026-11-27). Phase 11 accepted 2026-11-27. No release in that checkpoint.

Supersedes **only** these parts of ADR-0007:

* the restriction that `state.vscdb` is the **only** Cursor credential source (ADR-0007 Context and Decision item 1), and
* "the user re-authenticates inside Cursor" as the **only** remediation for a missing or rejected token (ADR-0007 Decision item 5).

Everything else in ADR-0007 stays in force and is restated below for both sources. ADR-0007's text is not edited.

## Context

On 2026-11-27, with Cursor desktop **3.28.7** and the Cursor CLI `agent` **2026.11.22-e9042b2**:

* The owner signed out of the Cursor GUI and signed back in. `state.vscdb` was rewritten. The new `ItemTable` value `cursorAuth/accessToken` is **not** JWT-shaped: it has no dots and three colon-separated parts, and it equals `cursorAuth/refreshToken`. Local hints showed an active Pro subscription.
* `POST https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage` with that value as `Authorization: Bearer` and `Connect-Protocol-Version: 1` returned **HTTP 401**. Horizon reported `auth_unavailable`.
* `~/.config/cursor/auth.json` (lowercase `cursor`, owned by the Cursor CLI `agent`) holds an `accessToken` that **is** JWT-shaped. The same request with that value returned **HTTP 200** with `planUsage.autoPercentUsed` and `planUsage.apiPercentUsed`.

The account and the endpoint work, and only the single credential source named by ADR-0007 stopped working. ADR-0007's remediation, signing in again inside Cursor, was done and did not help. This is upstream drift (the Phase 3 discovery was made against Cursor desktop 3.15.6), not a user sign-in failure.

Values, lengths beyond the format description above, claims, emails and user ids are deliberately not recorded.

## Decision

### Sources (both Cursor-owned)

| Id | Source | Value used | Override (testing / unusual layouts only) |
|----|--------|-----------|------------------------------------------|
| **IDE** | `~/.config/Cursor/User/globalStorage/state.vscdb`, `ItemTable` key `cursorAuth/accessToken` | the key's value, only if it is JWT-shaped | `--auth-file <path>`, `CURSOR_STATE_VSCDB` (unchanged) |
| **CLI** | `~/.config/cursor/auth.json` | the top-level `accessToken` string only | `CURSOR_CLI_AUTH_FILE` (new, test-only) |

**JWT-shaped** means a non-empty string of exactly three non-empty segments separated by `.`. This is a shape check only. Horizon does not decode, parse, verify or inspect any segment or claim.

### Order and fallback

1. If the IDE value exists and is JWT-shaped, send it to `GetCurrentPeriodUsage`.
2. A non-JWT IDE value is **not sent**. It is recorded as `unsupported format` and Horizon moves to the CLI source.
3. Horizon tries the CLI `accessToken` only if (a) the IDE source gave no sendable value, or (b) the IDE attempt returned **HTTP 401 or 403**.
4. Network errors, non-auth HTTP statuses, non-200 responses, invalid JSON and unexpected response shapes from any attempt **do not fall through**. They stop the fetch as `upstream_error`, as today.
5. The bearer that got HTTP 200 from `GetCurrentPeriodUsage` is the only one used for `GetPlanInfo`. A `GetPlanInfo` failure still falls back to the local `stripeMembershipType` label, as today, and never triggers a credential fallback.
6. `detect()` raises `auth_unavailable` only when **neither** source file is present.

### Boundaries (restated from ADR-0007, now for both sources)

1. Both files are opened **read-only**: `state.vscdb` through the SQLite URI `mode=ro`, and `auth.json` through a plain read-only open. Neither file's contents, mtime, permissions or locks are changed.
2. Tokens are held **in memory only** for one collector request.
3. Horizon **never** writes any token or auth key back into either file. It **never** copies tokens into the Horizon cache, config, KWallet, logs, stdout/stderr, docs, test fixtures (other than obviously fake values) or Git.
4. **No Cursor login**, OAuth or device flow, and Horizon never runs `agent login`, the `agent` binary or the Cursor app.
5. **No refresh, rotation or token exchange.** `cursorAuth/refreshToken` and the CLI `refreshToken` are never used, sent or kept. If the parser reads the whole `auth.json` object, it keeps only `accessToken`.
6. **No decoding** of the opaque IDE envelope: no splitting, decrypting, base64 work or exchanging it for another token.
7. `CURSOR_CLI_AUTH_FILE`, like `--auth-file`, `CURSOR_STATE_VSCDB` and `CURSOR_API_BASE`, is an override path for tests or unusual layouts. Horizon never writes to it and it never becomes a credential store.

### Failure reporting

The status vocabulary does not change: `auth_unavailable`, `upstream_error` and `stale` (through the existing cache fallback).

When no source yields an HTTP 200, the result is `auth_unavailable`, and the message names each source with one outcome from this fixed set:

| Outcome | Meaning |
|---------|---------|
| `not found` | source file absent |
| `unreadable` | file present but cannot be opened or parsed (SQLite error, OS error, invalid JSON, non-object JSON) |
| `no token` | file readable, but the key or field is absent, empty or not a string |
| `unsupported format` | IDE value present but not JWT-shaped (IDE source only; never sent) |
| `rejected (HTTP 401)` | the API rejected this source's bearer with 401 |
| `rejected (HTTP 403)` | the API rejected this source's bearer with 403 |

Message form: `Cursor usage unauthorized: IDE <outcome>; CLI <outcome>. Sign in to Cursor or the Cursor CLI (agent login).` The remediation points the user to Cursor's own tools. Horizon never runs them.

Messages never include token text, token lengths or prefixes, segment counts, JWT claims, emails, user ids or response bodies.

## Consequences

* A signed-in Cursor CLI restores usage when the desktop IDE stores an opaque, non-JWT session value.
* If the CLI credential expires, Horizon reports `auth_unavailable` with a per-source message. Cursor's own CLI renews it; Horizon does not.
* Both files are unofficial Cursor internals and may change on any Cursor update. The provider docs must record the Cursor versions observed.
* A local JWT `exp` check, to skip an expired CLI token without a round trip, is **not** part of this decision. It is Deferred Work.
* ADR-0004 (Codex write-back refresh) is still not a template for Cursor.
