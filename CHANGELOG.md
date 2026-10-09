# Changelog

## Unreleased

Stage 2 / Phase 8 — Plasma popup. Accepted 2026-10-09. The tagged release is still 0.1.1.

* Expanded popup shows one section per provider and one row per remaining-quota meter
* A reset appears only on the meter that has one
* Compact panel and collector behavior are unchanged

Stage 2 / Phase 7 — Provider information contract. Accepted 2026-10-09. The tagged release is still 0.1.1.

* Ordered `meters` are the canonical quota list: provider label, percent remaining, and that meter's own reset (ADR-0012)
* Existing `remainingPercent`, `secondaryRemainingPercent`, and `breakdown` stay as compatibility copies
* Codex windows are labeled from their length (`5-hour limit`, `Weekly limit`), not Primary/Secondary

Stage 1 / Phase 6.5 — Claude usage. Accepted 2026-10-09. The tagged release is still 0.1.1.

* Claude Pro/Max usage from the existing Claude Code login (`~/.claude/.credentials.json`), read-only
* Current session and current week shown with the provider’s own labels
* Missing or rejected Claude sessions stay `auth_unavailable`; Horizon does not refresh or copy the credentials (ADR-0011)

## 0.1.1 — 2026-09-11

Stage 1 / Phase 6 — StepFun auth resilience.

* Automatic Oasis refresh from the KWallet-stored token pair when usage returns unauthorized
* At most one refresh attempt per fetch; new pair is validated against live usage before KWallet replacement
* Failed refresh leaves the previous secret in place; manual Set/Replace Token remains the fallback
* Unofficial `platform.stepfun.ai` Passport `RefreshToken` path (ADR-0010)

## 0.1.0 — 2026-08-11

First usable release.

* Codex, Cursor, and StepFun providers through a shared collector + Plasma widget
* Provider enable/disable and configurable periodic refresh (default 15 minutes)
* Per-provider refresh overlap protection
* Compact panel shows the lowest remaining quota; tooltip lists providers
* Clearer stale / auth / unavailable labels
* StepFun Oasis token stored only in KWallet (CLI + widget settings)
* User install/upgrade/uninstall scripts (no git-checkout symlink required)
