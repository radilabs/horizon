# Phase 1 Handoff — Real Codex Usage

Date: 2026-08-10  
Environment: openSUSE Tumbleweed, Plasma 6.7.3 Wayland  
Plugin Id: `com.radilabs.horizon`

## Deliverables

* `collector/ai-usage` — Python CLI (`ai-usage status codex --json`)
* `plasmoid/contents/ui/main.qml` — executes collector; displays real quota / errors
* `docs/security.md` — credential ownership rules + secret-check procedure
* `docs/providers/codex.md` — auth, usage endpoint, normalized contract, outcome C
* `docs/development.md` — updated install/reload including collector symlink
* `docs/handoffs/phase-1.md` — this report
* `.gitignore` — credential-shaped ignore rules
* `decisions/0003-ai-usage-collector-cli.md`
* `decisions/0004-codex-auth-file-reuse.md`
* `tasks/phase-1-codex.md` — task evidence

## Tests Performed

1. Secret-boundary checks (`git status` / `git grep` style audits) — no tokens in repo
2. Inspected `~/.codex/auth.json` **structure only** (`auth_mode=chatgpt`, token key names); no secret values recorded
3. OAuth refresh against `auth.openai.com/oauth/token` (Codex CLI client id) updating Codex `auth.json` only
4. `GET https://chatgpt.com/backend-api/wham/usage` returned plan + primary window usage
5. `ai-usage status codex --json` → exit 0, valid JSON, plan ChatGPT Plus, remainingPercent matched upstream
6. Repeated collector runs remained valid
7. Controlled failure: `--auth-file` missing → exit 1, `status=auth_unavailable`, no fake success
8. Plasmoid upgrade + plasmawindowed: displayed ChatGPT Plus, 94%, reset relative time, Refresh control
9. Fixed Plasma `file://` home path bug that previously broke collector execution
10. Repository PII/secret scans for JWTs / known account identifiers — clean

## Acceptance Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Collector retrieves real Codex usage | PASS |
| 2 | `ai-usage status codex --json` normalized JSON | PASS |
| 3 | No auth secrets printed or persisted by Horizon | PASS |
| 4 | Existing local authentication reused | PASS |
| 5 | Logged-out/unavailable auth clear error | PASS |
| 6 | Plasmoid displays real remaining usage | PASS |
| 7 | Plasmoid displays reset time where available | PASS |
| 8 | Provider discovery notes complete | PASS (`docs/providers/codex.md`) |
| 9 | Phase 0 functionality still works | PASS (compact/popup/refresh) |

**PHASE 1 HANDOFF: PASS**

## Authentication Model

* Reuse ChatGPT OAuth tokens from `~/.codex/auth.json`
* Refresh via official Codex OAuth client id; write-back only to Codex auth file
* Horizon stores **no** provider credentials
* Keyring/KDE Wallet: not used by local Codex auth on this machine

## Security Validation

* No credentials committed
* No Horizon-owned credential store created
* Collector stdout JSON contains no tokens
* Docs/task evidence sanitized (no token values, no account email in docs)
* Repository secret audit passed for this handoff

## Known Limitations

* `wham/usage` is an unofficial private endpoint; schema may change
* Depends on prior Codex ChatGPT login artifacts
* Concurrent tools refreshing `auth.json` may race
* Plasmoid expects `~/.local/bin/ai-usage` symlink
* Primary window semantics vary by plan (tested Plus: weekly-length primary, no secondary)
* `codex` CLI binary was not on PATH during discovery

## Deferred Work

See `tasks/phase-1-codex.md` Deferred Work.

* Provider architecture / cache / stale UI → Phase 2
* Cursor → Phase 3
* StepFun → Phase 4
* Periodic refresh / notifications / settings → Phase 5

## Decisions

* `decisions/0003-ai-usage-collector-cli.md`
* `decisions/0004-codex-auth-file-reuse.md`

## Stop

Phase 1 handoff satisfied. **Do not begin Phase 2** without a new explicit execution instruction.
