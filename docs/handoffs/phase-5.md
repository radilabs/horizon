# Phase 5 Handoff — Operational Polish

Date: 2026-08-11  
Environment: openSUSE Tumbleweed, Plasma 6, KWallet enabled  
Release: **0.1.0**

## Deliverables

* Provider enable/disable + refresh interval via Plasma config (`contents/config/main.xml`, `configGeneral.qml`)
* Periodic refresh (default 15 minutes) with per-provider in-flight overlap protection (`main.qml`)
* Compact panel `AI <lowest%>%` + multi-line tooltip
* Friendlier stale / auth / unavailable labels (no raw exceptions in normal UI)
* StepFun credential Set/Replace/Remove in settings (KWallet via `ai-usage` stdin + `kdialog`)
* `scripts/install.sh`, `upgrade.sh`, `uninstall.sh` — stable collector under `~/.local/share/horizon/collector/`
* User-facing `README.md`, updated `docs/development.md`, `docs/release.md`, `CHANGELOG.md`, `VERSION`
* `docs/handoffs/phase-5.md` — this report

## Implemented polish tasks

| Task | Result |
|------|--------|
| P5-T0 baseline | PASS (Codex/Cursor live; StepFun token present but currently 401 → auth_unavailable / needs replace) |
| P5-T1 enable/disable | PASS |
| P5-T2 periodic refresh | PASS (5/10/15/30/60; default 15) |
| P5-T3 overlap protection | PASS (per-provider `inFlight`) |
| P5-T4 compact panel | PASS |
| P5-T5 stale/error/auth UX | PASS |
| P5-T6 StepFun settings UX | PASS (KWallet path unchanged) |
| P5-T7 config persistence | PASS (Plasma kcfg) |
| P5-T8 install/upgrade/uninstall | PASS (clean install tested; KWallet retained) |
| P5-T9 README | PASS |
| P5-T10 packaging 0.1.0 | PASS |
| P5-T11 notifications | **Deferred** (optional; not required) |
| P5-T12 regression | PASS (collector + install path) |
| P5-T13 handoff | PASS |

## Tests performed

1. Phase 4 regression: `ai-usage status` for codex/cursor/stepfun
2. Clean `./scripts/uninstall.sh --purge` then `./scripts/install.sh`
3. Launcher is a wrapper script, not a git symlink
4. Codex/Cursor live ok after install; StepFun reports auth_unavailable with expired token (expected until user replaces)
5. Upgrade reinstalls plasmoid including config UI files
6. Uninstall removes plasmoid/collector launcher; KWallet token remains
7. Overlap gate unit logic: second refresh for same provider skipped; other providers independent
8. Secret audit: no credential artifacts tracked; caches clean of tokens

## Acceptance results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Works reliably during normal Plasma sessions | PASS |
| 2 | No overlapping provider requests | PASS |
| 3 | Provider failures remain isolated | PASS |
| 4 | Stale/error states understandable | PASS |
| 5 | Configuration persists | PASS |
| 6 | Notifications (if implemented) rate-limited | **N/A — deferred** |
| 7 | Install/usage docs sufficient | PASS |
| 8 | Core three-provider functionality intact | PASS |

**PHASE 5 HANDOFF: PASS**

## Security validation

* StepFun token only in KWallet; settings never persist it
* Usage cache normalized only
* Uninstall does not delete KWallet secrets by default
* Secret audit clean for this handoff

## Known limitations

* Upstream APIs remain unofficial (Codex/Cursor/StepFun)
* StepFun Oasis tokens expire; user must Set/Replace token (no login/refresh automation)
* After plasmoid upgrade, Plasma may require remove/re-add or `plasmashell --replace` to load new QML

## Deferred / future work

```text
- [2026-08-11] Low-quota notifications (P5-T11 optional) → Future
- [2026-08-11] Additional providers → new phase contract
- [2026-08-11] Usage history/graphs → Future
- [2026-08-11] Browser credential import → Rejected / Future only if approved
- [2026-08-11] KDE Store / distro packaging automation → Future
- [2026-08-11] StepFun in-memory token refresh without login → Future
```

## Stop

Phase 5 handoff satisfied. Repository represents usable Horizon **v0.1.0**.

**Do not begin another provider or capability phase** without a new explicit contract.
