# Phase 6.5 Tasks — Claude Usage

Phase contract: `PHASES.md` → Stage 1 / **Phase 6.5 — Claude Usage**.

**Status: ACCEPTED** (2026-10-09). This file is historical execution evidence. It is **not** executable.

Accepted snapshot: `docs/handoffs/phase-6.5.md`. Horizon release remains **0.1.1**.

## Goal

Show real Claude subscription usage (Pro/Max), using the user's existing Claude Code authentication, alongside Codex, Cursor, and StepFun. Use the existing normalized usage schema and record enough sanitized discovery evidence for Claude to serve as a required design input to Phase 7.

## Read First

- `PROJECT.md`
- Stage 1 / Phase 6.5 in `PHASES.md`
- `docs/handoffs/phase-6.md`
- `docs/usage-schema.md`
- `docs/provider-contract.md`
- `docs/security.md`
- `decisions/0005-explicit-provider-registry.md`
- `decisions/0007-cursor-credentials-read-only.md`
- `decisions/0008-optional-usage-breakdown.md`
- current `collector/ai-usage` and `collector/providers/`

## P65-T0 — Baseline

Verify before changing provider behavior:

- Codex, Cursor, and StepFun still return through the existing collector
- repository secret audit has no live secrets
- Claude Code credentials exist locally, inspected by structure only

Record exact commands and sanitized results. Do not print tokens.

## P65-T1 — Discover Claude Code credentials

Using sanitized evidence only:

- locate the credential file Claude Code already owns
- record key names, value types, and expiry fields
- confirm Horizon can detect a present login without copying or writing the file

Do not refresh, rotate, or rewrite the credential store.

## P65-T2 — Discover the live usage mechanism

Verify against the current live service, using open-source trackers only as hints.

Determine:

- endpoint and required headers
- response shape
- every exposed usage window, its label, and reset semantics
- failure behavior for missing, expired, and rejected credentials

Document the proven mechanism in `docs/providers/claude.md`.

## P65-T3 — Implement read-only Claude provider

- Add `collector/providers/claude.py`.
- Register `claude` explicitly in `collector/ai-usage`.
- `detect()` fails with `auth_unavailable` when Claude Code credentials are missing.
- `fetch_usage()` reads credentials into memory, calls the usage endpoint, and returns the normalized schema.
- Primary meter: the window that best represents current session pressure, with `resetAt` when known.
- `breakdown` contains every proven window, using Claude's own labels.
- Missing, expired, or rejected credentials return `auth_unavailable` and tell the user to re-authenticate in Claude Code.
- Never refresh tokens. Never write the credential file. Never store Claude secrets in KWallet, cache, config, logs, or argv.

## P65-T4 — Display Claude in the existing UI

- Enable Claude through the existing provider list, settings checkbox, and collector command path.
- No visual redesign.

## P65-T5 — Tests and isolation

Cover, without live secrets:

- success normalization of every proven window
- missing credentials
- rejected/expired credentials (HTTP 401/403)
- upstream failure
- credential file is not written
- overlapping refresh is already prevented by the widget `inFlight` guard; collector must not start a second Claude HTTP call from one `fetch_usage`
- Codex, Cursor, and StepFun paths remain unchanged

Then run a live Claude fetch and confirm the other three providers still succeed.

## P65-T6 — Security and documentation

- Update `docs/security.md` and `docs/provider-contract.md`.
- Add a sanitized Claude example to `docs/usage-schema.md` only if the proven windows fit the existing schema. Do not redesign the schema.
- Secret audit must pass.
- Record upstream fragility.

## P65-T7 — Independent verification and handoff gate

Send the completed implementation to the existing Watcher thread.

If Watcher returns FAIL, correct in-scope findings and request re-verification.

After Watcher PASS, present evidence to the project owners and STOP.

Create `docs/handoffs/phase-6.5.md` only after owner acceptance.

## Explicit exclusions

Unchanged from `PHASES.md`: no Claude token refresh or credential writes, no Claude login, no KWallet copy, no Anthropic Console/API-key usage, no browser import, no schema redesign, no UI redesign, no Codex/Cursor/StepFun behavior changes except a demonstrated regression, no other provider.

## Deferred Work

Record, but do not implement:

- Claude OAuth refresh or credential rotation
- Anthropic API-key / Console billing
- Provider information contract redesign (Phase 7)
- Plasma UI/UX refresh (Phases 8–9)
- Any other provider, including Groq

## Harness note

The provider-stream interruption that preceded this task file is recorded only in `reports/stage-1-phase-6.5-infra-failure-1.md`. It is not a Horizon product finding.

## Execution evidence (Coder, 2026-10-09)

Worktree: `/home/naorw/.t3/worktrees/horizon/phase-6.5-claude-usage` on branch `phase-6.5-claude-usage`. Not committed. `main` was not modified.

### P65-T0 Baseline (before Claude code)

`python3 collector/ai-usage status {codex,cursor,stepfun} --json --no-cache`

| Provider | Result |
|----------|--------|
| Codex | `ok` / ChatGPT Plus / 100 |
| Cursor | `ok` / Pro / 80 (Other Models 0) |
| StepFun | `ok` / Plus / 100 |

### P65-T1 Credentials (sanitized)

`~/.claude/.credentials.json`, mode `0600`, 519 bytes. Top-level key `claudeAiOauth`. Fields: `accessToken` (length 108), `refreshToken` (length 108, unused), `expiresAt` `2026-10-09T18:57:01+02:00` (unix ms), `subscriptionType` `pro`, `rateLimitTier` `default_claude_ai`. Claude Code binary `2.1.295`.

### P65-T2 Live usage

`GET https://api.anthropic.com/api/oauth/usage` with `anthropic-beta: oauth-2025-04-20` returned HTTP 200. `utilization` is percent used, 0–100. Pro account exposed `five_hour` (1% used) and `seven_day` (22% used). Other named windows were null. A fake token returned HTTP 401. File hash and mtime were unchanged. Details: `docs/providers/claude.md`.

### P65-T3 / T4 Implementation

Read-only provider `collector/providers/claude.py`, registry entry `claude`, settings checkbox, `enableClaude` default true. No schema redesign. ADR-0011 forbids refresh and writes.

### P65-T5 Tests

`python3 -m unittest tests.test_claude_usage tests.test_stepfun_oasis_refresh -q` → 17 tests OK.

Live installed launcher after `./scripts/install.sh`: `claude ok Pro 99` with breakdown `Current session`, `Current week (all models)`. Stdout had no `sk-` prefix. Codex, Cursor, and StepFun still `ok` after the change.

Cache written under a temporary `XDG_CACHE_HOME` and later `~/.cache/horizon/usage-claude.json` contained normalized fields only (no `sk-`, `accessToken`, or `refreshToken`).

Plasmashell was restarted so the upgraded applet loaded. The panel applet `com.radilabs.horizon` (id 27) is present. Compact label reads `AI 0%`, the existing lowest-meter summary (Cursor Other Models is 0).

The fixed popup height (`gridUnit * 36`) clipped Claude under the panel. It is now `gridUnit * 48` so the existing column can show the fourth provider. That is not a visual redesign. A temporary open-on-load timer was used only to capture the popup, then removed.

Screenshot: `reports/phase-6.5-widget-popup.png`. The expanded widget shows Codex, Cursor, StepFun, and Claude Pro with **Current session 99%** and **Current week (all models) 78%**, plus Refresh.

### P65-T6 Security

`git grep` bearer/token hits are existing field names, docs, and tests. New test fixtures use `sk-ant-test-access` / `sk-ant-test-refresh` only. No live credential file is tracked.

### Known limitations

- Usage route is unofficial (Claude Code 2.1.295).
- This Pro account did not return Opus, Sonnet, or extra-usage windows live. Those rows are fixture-tested from the Claude Code labels.
- `seven_day_breakdown` and disabled `spend` are documented for Phase 7 and are not quota bars.
- README screenshots are still the pre-Claude widget.
- Release remains `0.1.1`. This acceptance did not bump the version or create a tag.

### P65-T7

Watcher attempt 1: **FAIL** (`reports/stage-1-phase-6.5-watcher-1.md`), W65-01, popup not observed. Corrected by raising the existing popup height and capturing `reports/phase-6.5-widget-popup.png`.

Watcher attempt 2: **PASS** (`reports/stage-1-phase-6.5-watcher-2.md`), 2026-10-09. W65-01 resolved. No blocking findings.

Owner acceptance granted 2026-10-09. Accepted snapshot: `docs/handoffs/phase-6.5.md`.

**PHASE 6.5: ACCEPTED.** Stage 2 and Phase 7 are not authorized.
