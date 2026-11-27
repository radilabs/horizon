# Changelog

## 0.2.1 — 2026-11-27

* StepFun shows Subscription Credits and Top-up Credits when those rates are separate, and reuses the usage check after a token refresh
* A StepFun outage is reported as unavailable. A rejected token is still auth_failed
* The cache refuses secret-like keys nested in a payload
* Reset and cache-age text stay current while the popup is open
* Installer pipe safety, Refresh key handling, and the 0.2.0 audit's doc corrections

## 0.2.0 — 2026-10-09

* Claude Pro/Max usage from the existing Claude Code login (`~/.claude/.credentials.json`), read-only. Horizon does not refresh or copy those credentials
* Ordered usage meters: each row has the provider’s own label, percent remaining, and that meter’s own reset
* Popup shows one section per provider, scrolls when the list is taller than the screen, and puts Refresh in the header
* Compact panel keeps the lowest remaining quota when another meter is at 0 (`AI 75% · 1 at 0%`). The tooltip lists every meter

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
