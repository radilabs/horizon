# Phase 11 Handoff — Cursor Credential Compatibility

Date: 2026-11-27  
Environment: openSUSE, Plasma 6  
Release: unchanged, Horizon **0.2.1** (`v0.2.1`)

**PHASE 11 HANDOFF: ACCEPTED**

## Owner acceptance

The project owner accepted Stage 3 / Phase 11 on 2026-11-27 after Watcher PASS, and asked for the README Cursor section to be updated in the same checkpoint.

Acceptance is recorded here. Watcher PASS alone was not acceptance. No version bump, tag, or GitHub release was requested or made.

## Deliverables

* ADR-0013 adds `~/.config/cursor/auth.json` as a second read-only, Cursor-owned source. It supersedes only ADR-0007's single-source restriction and its only-remediation rule. ADR-0007's text is unchanged.
* A JWT-shaped IDE `cursorAuth/accessToken` is tried first. A non-JWT IDE value is not sent. HTTP 401/403 falls through to the CLI `accessToken`. Network and other non-auth failures stay `upstream_error`.
* The bearer that gets HTTP 200 is reused for `GetPlanInfo`.
* README, `docs/providers/cursor.md`, `docs/provider-contract.md`, and `docs/security.md` describe both sources.
* Independent Watcher reports (gitignored): `reports/stage-3-phase-11-watcher-1.md` (FAIL), `reports/stage-3-phase-11-watcher-2.md` (PASS)

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Dual source with a fake API, including plan-bearer reuse | PASS |
| 2 | No fallback on upstream or network errors, including invalid UTF-8 | PASS |
| 3 | Fixture files unchanged after a fetch | PASS |
| 4 | Secret audit | PASS |
| 5 | Endpoints, headers, meters, cache fields, and status vocabulary preserved | PASS |
| 6 | Python and QML tests pass. Four providers live `ok` | PASS |
| 7 | Scope stayed inside the phase, plus the owner-requested README update at acceptance | PASS |
| 8 | Docs match ADR-0013 | PASS |
| 9 | Deferred Work recorded | PASS |
| 10 | Watcher PASS, then explicit owner acceptance | PASS |

## Tests / owner evidence

* `python3 -m unittest discover -s tests` — 61 passed (baseline 48)
* QML: compact 14, meter intake 6, refresh keys 7, command and times 6, all passed
* Live `ai-usage status <id> --json --no-cache`: Codex ok, Cursor ok (Pro, Cursor Models, Other Models), StepFun ok, Claude ok
* Watcher attempt 1 FAIL on invalid UTF-8 (`UnicodeDecodeError`). Fixed. Attempt 2 PASS

Watcher attempt 2: **PASS**. Report: `reports/stage-3-phase-11-watcher-2.md`.

Owner: accepted Phase 11 on 2026-11-27. No release.

## Known limitations

* The desktop app can store an opaque session value that Horizon will not send. Usage then depends on `~/.config/cursor/auth.json`, which a GUI sign-in does not update
* Horizon does not refresh either Cursor token

## Deferred work

```text
- A local JWT expiry check before the usage request
- A supported way to use the opaque IDE session value, if Cursor provides one
- CLI auth files outside ~/.config/cursor/auth.json
```

## Stop

Phase 11 accepted. Stage 3 is closed. Horizon remains **0.2.1**.

**Do not begin a new phase** without an explicit new contract and `TASKS.md` authorization.
