# ADR-0004: Reuse `~/.codex/auth.json` with in-place OAuth refresh

## Status

Accepted

## Context

Local Codex auth is ChatGPT OAuth stored in `~/.codex/auth.json`. Access tokens expire. Horizon must not own credentials or implement login.

## Decision

* **Outcome C**: read existing Codex auth file transiently
* On expiry/401, refresh via `https://auth.openai.com/oauth/token` using the public Codex CLI client id
* Persist rotated tokens only by updating Codex’s own `auth.json` (atomic replace, mode `0600`)
* Never copy tokens into Horizon config/cache/docs/logs/stdout

## Consequences

* Horizon depends on a prior Codex/ChatGPT login having created `auth.json`
* Refresh may race with other tools updating the same file
* This is acceptable for Phase 1 personal use; Phase 2+ may revisit keyring brokerage if Codex adopts it
