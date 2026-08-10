# ADR-0009 — OS credential store for providers without local auth

## Status

Accepted (Phase 4)

## Context

Codex and Cursor expose local provider-owned credential/session state that Horizon can reuse transiently.

StepFun Step Plan has **no** local desktop credential store. Usage APIs require an Oasis token. Username/password login automation is out of scope and must not be implemented.

## Decision

1. Prefer provider-owned local credentials whenever they exist (Codex, Cursor pattern).
2. When no provider-owned local source exists, Horizon may securely store a **user-supplied** credential in the **OS credential store** (on this platform: KWallet via `org.kde.kwalletd6`).
3. For StepFun, store only the Oasis token under folder `Horizon`, entry `stepfun/oasis-token`.
4. Never store StepFun username/password.
5. Never store the token in Horizon config, XDG usage cache, env files, repository, docs, logs, stdout/stderr, or CLI arguments.
6. Do not invent Horizon encryption, a generic secrets DB, browser import, or settings UI for credentials.
7. Future providers may reuse this minimal `secret_store` only when similarly justified.

## Consequences

* First Horizon-owned provider secret (OS-backed).
* Users must paste an existing Oasis token via `ai-usage auth stepfun set`.
* Token expiry requires the user to supply a new token; Horizon does not implement StepFun login/refresh write-back.
