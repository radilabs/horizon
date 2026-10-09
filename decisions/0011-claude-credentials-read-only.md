# ADR-0011 — Claude Code credentials stay read-only

## Status

Accepted (Phase 6.5)

## Context

Claude Code stores a Claude.ai OAuth session in `~/.claude/.credentials.json`, including an access token and a refresh token.

Codex (ADR-0004) may refresh tokens and write them back into `~/.codex/auth.json`. Doing the same for Claude could invalidate the user’s Claude Code session. Phase 6.5 forbids refreshing, rotating, or copying that file, and forbids a Horizon-owned Claude credential store.

## Decision

1. Horizon reads `~/.claude/.credentials.json` **read-only** (`O_RDONLY`).
2. The access token is held **only in memory** for the duration of one usage request.
3. Horizon **never** writes the credentials file, **never** calls the OAuth token endpoint, and **never** copies Claude tokens into KWallet, cache, config, logs, docs, or Git.
4. Horizon does **not** implement Claude login.
5. If the access token is missing, locally expired, or rejected (401/403), Horizon reports `auth_unavailable` and the user re-authenticates inside Claude Code.

## Consequences

* An expired Claude Code session stays expired until the user signs in again with Claude Code.
* Future work, including Phase 7, must not treat Codex write-back refresh as a template for Claude.
* Test overrides (`--auth-file`, `CLAUDE_CREDENTIALS_FILE`, `CLAUDE_API_BASE`) must not become a credential store.
