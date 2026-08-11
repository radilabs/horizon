# Changelog

## 0.1.0 — 2026-08-11

First usable release.

* Codex, Cursor, and StepFun providers through a shared collector + Plasma widget
* Provider enable/disable and configurable periodic refresh (default 15 minutes)
* Per-provider refresh overlap protection
* Compact panel shows the lowest remaining quota; tooltip lists providers
* Clearer stale / auth / unavailable labels
* StepFun Oasis token stored only in KWallet (CLI + widget settings)
* User install/upgrade/uninstall scripts (no git-checkout symlink required)
