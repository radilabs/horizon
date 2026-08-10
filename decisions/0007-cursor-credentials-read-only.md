# ADR-0007 — Cursor credentials stay read-only and Cursor-owned

## Status

Accepted (Phase 3)

## Context

Cursor stores session tokens in `~/.config/Cursor/User/globalStorage/state.vscdb`. Horizon needs an access token to call Cursor’s DashboardService usage API.

Codex (ADR-0004) may refresh tokens and write them back into `~/.codex/auth.json`. Doing the same for Cursor would mean Horizon modifies Cursor’s authentication database.

Phase 3 rules forbid modifying Cursor credentials and forbid Horizon-owned Cursor credential storage / login flows.

## Decision

1. Horizon reads Cursor `state.vscdb` **read-only** (`sqlite` URI `mode=ro`).
2. Access tokens are held **only in memory** for the duration of a collector request.
3. Horizon **never** writes tokens (or any auth keys) back into Cursor state, and **never** copies them into Horizon cache, config, logs, docs, or Git.
4. Horizon does **not** implement Cursor login or token refresh that mutates Cursor-owned storage.
5. If the access token is missing or rejected (401/403), Horizon reports `auth_unavailable` and the user re-authenticates inside Cursor.

## Consequences

* Expired Cursor sessions require the user to sign in again via Cursor; Horizon will not silently renew into Cursor’s DB.
* Future providers must not treat Codex’s write-back refresh as a template for Cursor.
* Test overrides (`--auth-file`, `CURSOR_STATE_VSCDB`, `CURSOR_API_BASE`) must not become a credential store.
