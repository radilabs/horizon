# ADR-0008 — Optional labeled usage breakdown

## Status

Accepted (Phase 3 Cursor mapping correction)

## Context

Cursor’s live Usage UI shows two concurrent meters on the same billing cycle:

* **Cursor Models** ← `planUsage.autoPercentUsed`
* **Other Models** ← `planUsage.apiPercentUsed`

A single `remainingPercent` cannot represent both. Codex already has an unlabeled `secondaryRemainingPercent` for a second rate window.

An older aggregate (“included usage” from `remaining`/`limit`/`totalSpend` / `displayMessage`) exists upstream but is **not** shown as a normal Cursor Usage meter in the current UI and must not be mapped as a Horizon quota bar.

## Decision

1. Keep `remainingPercent` as the primary meter (for Cursor: **Cursor Models** remaining).
2. Keep `secondaryRemainingPercent` as an optional unlabeled second meter (for Cursor: **Other Models** remaining).
3. Keep optional `breakdown`: `{ "label": string, "remainingPercent": number, "resetAt"?: string }[]` for labeled multi-meter display with per-line reset when known.
4. Plasma UI prefers `breakdown` when present; otherwise falls back to the primary bar (+ secondary if present).
5. Cache may persist `breakdown` (normalized labels/percents/timestamps only).
6. Do **not** expose the included/spend aggregate as a breakdown row unless future work proves it as a useful derived aggregate with clear semantics.

## Consequences

* Shared schema gains one optional field (`breakdown`); Codex unchanged unless it emits `breakdown`.
* Providers must not put secrets or raw upstream blobs in `breakdown`.
* Labels are provider-chosen user-facing strings, not free-form upstream dumps.
