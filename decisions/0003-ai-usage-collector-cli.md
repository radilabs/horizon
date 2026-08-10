# ADR-0003: External `ai-usage` collector CLI (Python)

## Status

Accepted

## Context

Phase 1 requires real Codex quota in the Plasma widget without embedding auth/HTTP logic in QML, and without building the Phase 2 provider plugin framework.

## Decision

* Introduce a small external CLI at `collector/ai-usage` invoked as `ai-usage status codex --json`
* Implement Phase 1 in **Python 3** (stdlib only) for fastest correct HTTP/JSON handling on this system
* Plasma talks only to the normalized JSON contract; it never sees tokens or raw upstream schemas

## Consequences

* Operators must have `ai-usage` available at `~/.local/bin/ai-usage` (or adjust the plasmoid command later)
* Phase 2 may reorganize providers behind this CLI, but should preserve the command shape if possible
* Language choice is Phase 1 pragmatism, not a permanent multi-provider platform commitment
