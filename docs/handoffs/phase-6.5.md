# Phase 6.5 Handoff — Claude Usage

Date: 2026-10-09  
Environment: openSUSE, Plasma 6, Claude Code 2.1.295  
Release: remains **0.1.1** (`v0.1.1`). This acceptance is not a version bump or tag.

**PHASE 6.5 HANDOFF: ACCEPTED**

## Owner acceptance

The project owner explicitly accepted Stage 1 / Phase 6.5 on 2026-10-09 after Watcher PASS. The owner had already seen Claude in the installed widget.

Acceptance is recorded here. This file is the accepted-state snapshot. Watcher PASS alone was not acceptance.

## Deliverables

* Read-only Claude provider: `collector/providers/claude.py`, registered as `claude` in `collector/ai-usage`
* Plasma enable checkbox and existing popup path, with popup height raised from `gridUnit * 36` to `gridUnit * 48` so Claude is not clipped
* `scripts/install.sh` installs the Claude module
* Unit tests: `tests/test_claude_usage.py`
* Durable docs: `docs/providers/claude.md`, `docs/security.md`, `docs/provider-contract.md`, `docs/usage-schema.md`, ADR-0011
* Independent Watcher reports (runtime, gitignored): `reports/stage-1-phase-6.5-watcher-1.md` (FAIL), `reports/stage-1-phase-6.5-watcher-2.md` (PASS)
* Popup evidence (runtime, gitignored): `reports/phase-6.5-widget-popup.png`

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Credential source, usage mechanism, and windows documented from sanitized evidence | PASS |
| 2 | Horizon detects usable Claude Code authentication | PASS |
| 3 | Real Claude windows normalized through the common provider model | PASS |
| 4 | Claude appears in the widget beside Codex, Cursor, and StepFun | PASS |
| 5 | Missing, expired, or rejected credentials are `auth_unavailable`; no token refresh or credential write | PASS |
| 6 | No Claude secrets in repo, config, cache, logs, stdout, argv, docs, or task evidence | PASS |
| 7 | Claude failure does not affect Codex, Cursor, or StepFun | PASS |
| 8 | Periodic and manual refresh do not overlap Claude requests | PASS |
| 9 | Discovery docs record the Claude window structure for Phase 7 | PASS |

## Tests / owner evidence

Coder (2026-10-09, sanitized):

* Credentials file `~/.claude/.credentials.json`, mode `0600`, key `claudeAiOauth`. Access token used in memory only. Refresh token unused. `subscriptionType` `pro`.
* `GET https://api.anthropic.com/api/oauth/usage` with `anthropic-beta: oauth-2025-04-20`. `utilization` is percent used, 0–100.
* Live Pro windows: Current session 99%, Current week (all models) 78%. Other named windows null on this account.
* Fake token: HTTP 401, credentials file unchanged.
* `python3 -m unittest tests.test_claude_usage tests.test_stepfun_oasis_refresh -q` — 17 OK
* Expanded widget screenshot shows Codex, Cursor, StepFun, and Claude Pro with both windows and Refresh

Watcher: attempt 1 FAIL (popup not observed). Height correction, then attempt 2 `WATCHER RESULT: PASS`.

Owner: accepted Phase 6.5 on 2026-10-09.

Closeout re-check (2026-10-09, after acceptance, `--no-cache`): Codex `ok` ChatGPT Plus 100; Cursor `ok` Pro 78; StepFun `ok` Plus 100; Claude `ok` Pro 99. No `sk-` material in those outputs.

## Security validation

* Claude Code credentials stay read-only (ADR-0011)
* No OAuth refresh, no credential-file write, no KWallet copy, no login flow
* Cache files hold normalized usage only

## Known limitations

* The usage route is unofficial and matches Claude Code 2.1.295
* This Pro account did not return Opus, Sonnet, or extra-usage windows live; those rows are fixture-tested from Claude Code labels
* `seven_day_breakdown` and disabled `spend` are documented for Phase 7 and are not quota bars
* README screenshots are still the pre-Claude widget
* Tagged release remains 0.1.1

## Stage 1 exit check

Checked 2026-10-09. Not an authorization of Stage 2.

* Authorized Stage 1 phases are accepted: Phase 6 and Phase 6.5
* Codex, Cursor, and StepFun still return `ok`
* Security boundaries are documented, including ADR-0011
* No unauthorized provider was added. Claude was the owner-amended Stage 1 phase

Stage 1 is closed. Stage 2 is not opened. Phase 7 is not authorized.

## Deferred work

```text
- Claude OAuth refresh or credential rotation
- Anthropic API-key / Console billing
- Phase 7 provider information contract
- Phase 8–9 Plasma UI refresh
- Any other provider, including Groq
- README screenshot refresh
```

## Stop

Phase 6.5 accepted. Horizon release remains **0.1.1**.

**Do not begin Stage 2 or Phase 7** without an explicit new contract and `TASKS.md` authorization.
