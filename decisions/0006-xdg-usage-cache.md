# ADR-0006: XDG cache for last-successful normalized usage

## Status

Accepted

## Context

Phase 2 requires showing last successful usage when live retrieval fails, without storing credentials.

## Decision

* Cache under `$XDG_CACHE_HOME/horizon/` (default `~/.cache/horizon/`)
* One file per provider: `usage-<provider>.json`
* Envelope: `{ fetchedAt, provider, data }` where `data` is normalized usage only
* Atomic write; ignore corrupt cache; never cache failure payloads as success

## Consequences

* Cache is Horizon-owned state but must remain non-secret
* Future providers reuse the same location/format
* Credentials stay in provider-owned stores (e.g. `~/.codex/auth.json`)
