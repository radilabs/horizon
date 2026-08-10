# ADR-0005: Explicit provider registry (no plugins)

## Status

Accepted

## Context

Phase 2 needs a seam for additional providers without inventing a plugin system.

## Decision

* Providers are Python classes registered in a small explicit map in the collector CLI
* No setuptools entry points, filesystem plugin discovery, or DI containers

## Consequences

* Adding a provider requires a code change + registry entry (acceptable for Horizon’s small provider set)
* Phase 3/4 implement new modules and register them explicitly
