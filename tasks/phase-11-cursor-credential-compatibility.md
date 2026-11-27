# Stage 3 / Phase 11 — Cursor Credential Compatibility

**Status: ACCEPTED** (2026-11-27). Historical. **Not executable.** Snapshot: `docs/handoffs/phase-11.md`.

**Authority:** `PHASES.md` Phase 11 (the immutable contract), `TASKS.md`
**Decision:** ADR-0013 (`decisions/0013-cursor-dual-source-read-only-credentials.md`), which supersedes only ADR-0007's single-source restriction and its only-remediation rule
**Contracts to preserve:** ADR-0007 (all other boundaries), ADR-0012 (`decisions/0012-ordered-usage-meters.md`), `docs/usage-schema.md`, ADR-0004/0009/0010/0011
**Previous accepted snapshot:** `docs/handoffs/phase-10.md`
**Branch:** `phase-11-cursor-credential-compatibility` (from `3891626`, `v0.2.1`)
**Worktree:** `/home/naorw/.t3/worktrees/horizon/phase-11-cursor-credential-compatibility`

## Goal

Restore Cursor usage for a signed-in user whose desktop `state.vscdb` holds an opaque, non-JWT `cursorAuth/accessToken`. Add the Cursor CLI's `~/.config/cursor/auth.json` `accessToken` as a second read-only, Cursor-owned source. Change nothing else.

## Problem statement (evidence summary, no secrets)

On 2026-11-27 (Cursor desktop 3.28.7, CLI `agent` 2026.11.22-e9042b2), the owner signed out of the GUI and back in. The rewritten IDE `accessToken` is not JWT-shaped (no dots, three colon-separated parts) and equals the IDE `refreshToken`. `ai-usage status cursor --json --no-cache` returned `auth_unavailable` / `Cursor usage unauthorized (HTTP 401)`. The CLI `auth.json` `accessToken` is JWT-shaped, and the same POST with it returned HTTP 200 with both percent fields.

## Baseline (`3891626`, recorded by the Architect on 2026-11-27)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests` | 48 tests, OK |

The Coder re-records this baseline, plus the QML suites (`qmltestrunner6` on `tests/test_compact_summary.qml`, `tests/test_meter_intake.qml`, `tests/test_refresh_keys.qml`), before the first change.

## Architectural lines the Coder must not cross

- Never write, touch, chmod, lock-upgrade or re-serialize `state.vscdb` or `auth.json`. Use SQLite `mode=ro` for the IDE database and a plain read-only open for the CLI file.
- Never decode, split, base64-decode, decrypt or exchange any token. The JWT check is **shape only**: a non-empty `str`, `value.split(".")` has length 3, and every part is non-empty. Do not inspect any part.
- Never read `refreshToken` into use from either source. Keep only the `accessToken` string of the parsed CLI object.
- Never run `agent`, Cursor, a browser or any login/OAuth/refresh endpoint.
- Never persist a token anywhere: no cache, config, KWallet, log, stderr, stdout or exception text. Do not add a token-carrying field to `ProviderError`.
- No fallback on anything other than HTTP 401/403 from `GetCurrentPeriodUsage`.
- No new status codes, no schema change, no meter change, no QML change.
- No shared or general authentication abstraction. The change stays inside `CursorProvider`.

## Execution Tasks

Each task is complete only when its acceptance check has direct evidence in the Evidence section.

### T1 — Credential candidates

- **Task.** In `collector/providers/cursor.py`:
  1. Add `DEFAULT_CLI_AUTH = Path.home() / ".config" / "cursor" / "auth.json"`.
  2. The constructor gains an optional `cli_auth` path and resolves it as: explicit argument, then `CURSOR_CLI_AUTH_FILE` (expanded), then the default. IDE resolution (`state_db` argument / `--auth-file`, then `CURSOR_STATE_VSCDB`, then default) is unchanged.
  3. Replace the single-token read with a function that returns the IDE candidate (a token, or a fixed outcome) plus the membership hint.
  4. Add a CLI read that returns the CLI candidate (a token, or a fixed outcome).
  5. Outcomes come only from the ADR-0013 set: `not found`, `unreadable`, `no token`, `unsupported format`.
  6. A non-JWT IDE value gives `unsupported format` and is dropped.
- **Acceptance.** Unit tests on the readers with temporary fixtures:
  1. An IDE JWT is returned.
  2. An IDE non-JWT value (for example `a:bb:ccc`) gives `unsupported format`, and the value is not returned or kept.
  3. An IDE database without the key gives `no token`.
  4. An IDE path that is a non-SQLite file gives `unreadable`.
  5. An absent IDE file gives `not found`.
  6. A CLI file with an `accessToken` string returns it.
  7. A CLI file with only `refreshToken` gives `no token`.
  8. Invalid JSON, or a JSON array, gives `unreadable`.
  9. An absent CLI file gives `not found`.
  10. The membership hint is still read from the IDE database.

### T2 — Ordered fetch with auth-only fallback

- **Task.**
  1. `fetch_usage()` tries the IDE JWT first, if present, against `GetCurrentPeriodUsage`.
  2. On a `ProviderError` that came from HTTP 401/403, record `rejected (HTTP 401|403)` for IDE and try the CLI candidate, if present.
  3. Any other error propagates unchanged as `upstream_error`.
  4. When no candidate succeeds, raise `auth_unavailable` with `Cursor usage unauthorized: IDE <outcome>; CLI <outcome>. Sign in to Cursor or the Cursor CLI (agent login).`
  5. Keep the exact HTTP status so 401 and 403 produce distinct outcomes, for example through a small private exception or attribute that carries no token.
- **Acceptance.** Fake `CURSOR_API_BASE` HTTP server tests that record each request's path and `Authorization` header, comparing against fixture tokens in memory only:
  1. **(1a)** An IDE JWT returning 200 gives `ok`. Requests are `[usage(IDE), plan(IDE)]`.
  2. **(1b)** An IDE JWT returning 401, then a CLI 200, gives `ok`. Requests are `[usage(IDE), usage(CLI), plan(CLI)]`. The same holds for 403.
  3. **(1c)** A non-JWT IDE value plus a valid CLI token gives `ok`, and no request carries the IDE value.
  4. **(1d)** An absent IDE database plus a valid CLI token gives `ok`.
  5. **(1f)** These give `auth_unavailable` with the exact expected outcome per source:
     - IDE 401 and CLI 401;
     - IDE 403 and CLI absent;
     - IDE `unsupported format` and CLI `no token`;
     - IDE `unreadable` and CLI `unreadable`.
  6. Meter output for each success case equals the existing `CursorContractTests` expectations (labels `Cursor Models`, `Other Models`, order and percent semantics).

### T3 — No fallback on upstream failure

- **Task.** Confirm that no code path tries the CLI after a non-auth failure.
- **Acceptance.** Fake-server tests where the IDE JWT attempt meets each of these:
  1. a connection refused or closed (`URLError`);
  2. HTTP 500;
  3. HTTP 200 with invalid JSON;
  4. HTTP 200 with a JSON array;
  5. HTTP 200 missing both `autoPercentUsed` and `apiPercentUsed`.

  Each gives `upstream_error` with **zero** requests carrying the CLI bearer. One `ai-usage status cursor --json` run with a warm cache in `XDG_CACHE_HOME`, a fixture IDE JWT and a fake 500 gives `status=stale`.

### T4 — Plan info reuse

- **Task.** Call `GetPlanInfo` with the winning bearer only. A failed `GetPlanInfo` call still falls back to `stripeMembershipType`, then to `Cursor`. It never triggers a credential fallback.
- **Acceptance.**
  1. Request logs from T2 show the plan call uses the winning bearer.
  2. A test where `GetPlanInfo` returns 401 after a successful CLI usage call gives `ok` with the membership label, and no further usage calls.

### T5 — detect() and CLI wiring

- **Task.**
  1. `detect()` raises `auth_unavailable` only when neither the IDE database nor the CLI file is a file.
  2. `collector/ai-usage` `build_provider()` keeps mapping `--auth-file` to the IDE `state_db`. The CLI path comes only from `CURSOR_CLI_AUTH_FILE` or the default. No new CLI flag.
- **Acceptance.**
  1. A test shows neither file present gives `auth_unavailable` from `detect()`, and no HTTP request is made.
  2. The IDE-only and CLI-only cases each pass `detect()`.
  3. A subprocess test of `collector/ai-usage status cursor --json --no-cache --auth-file <fixture-db>`, with `CURSOR_CLI_AUTH_FILE` and `CURSOR_API_BASE` set, shows the override wiring works end to end.

### T6 — Security regression

- **Task.** Add tests that prove the read-only and no-secret boundaries.
- **Acceptance.**
  1. **Files unchanged.** For every T2/T3/T5 path, both fixture files have the same SHA-256 and `st_mtime_ns` before and after the fetch.
  2. **No token in output.** No fixture `accessToken` or `refreshToken` substring (and no 8-character prefix of one) appears in:
     - the `ProviderError` message;
     - the subprocess stdout/stderr and `--json` payload;
     - the cache file written on success.
  3. **refreshToken never sent.** The fake server never receives either fixture `refreshToken` in any header or body.
  4. **No new credential store.** `git diff 3891626 --stat` shows no new file that stores Cursor credentials.
  5. **Repository secret audit.** `git grep -nE 'eyJ[A-Za-z0-9_-]{10,}\.'` finds no real-looking JWT. Fixtures use obviously fake values such as `fake.ide.jwt` and `fake.cli.jwt`.

### T7 — Writer docs (after T1–T6)

- **Task.** Update the current docs to match ADR-0013 and the implemented behavior:
  - **`docs/providers/cursor.md`:**
    - the observed Cursor versions (desktop 3.15.6 at Phase 3; 3.28.7 and CLI `agent` 2026.11.22 at Phase 11);
    - the opaque non-JWT IDE value;
    - both sources, their order and overrides;
    - the fixed outcome set and message;
    - the failure table;
    - the `Credentials remain owned by Cursor` line now covering both files.
  - **`docs/provider-contract.md`:** the Cursor provider line, plus the `--auth-file` note and `CURSOR_CLI_AUTH_FILE`.
  - **`docs/security.md`:** add `~/.config/cursor/auth.json` to the provider-owned sources and the never-commit list.

  Do not edit `docs/handoffs/phase-3.md`, ADR-0007 or other historical records.
- **Acceptance.**
  1. A diff review shows each statement matches ADR-0013 and the code.
  2. `git grep -n 'state.vscdb' docs/providers/cursor.md docs/provider-contract.md docs/security.md` no longer describes it as the only source.

### T8 — Regression and live check

- **Acceptance.**
  1. `python3 -m unittest discover -s tests` passes, with more tests than the baseline of 48.
  2. All three QML suites pass with the same counts as the baseline.
  3. `scripts/install.sh`, then `~/.local/bin/ai-usage status <id> --json` for `codex`, `cursor`, `stepfun` and `claude`, each give `ok`. The Cursor result has `Cursor Models` and `Other Models` meters.
  4. Live output is recorded in sanitized form: no tokens, emails or ids.

## Acceptance Criteria (summary; PHASES.md is authoritative)

| # | Criterion | Evidence |
|---|---|---|
| 1 | Dual source with a fake `CURSOR_API_BASE` | T1, T2, T4, T5 tests |
| 2 | No fallback on upstream or network errors; stale with a warm cache | T3 |
| 3 | Fixture files unchanged | T6.1 |
| 4 | Secret audit | T6.2–T6.5 |
| 5 | Endpoints, headers, meters, cache fields and status vocabulary preserved | T2.6, diff review |
| 6 | No regression; four providers work live | T8 |
| 7 | Scope fence: `git diff 3891626 --stat` touches only allowed paths; `decisions/0007-*`, `VERSION`, `plasmoid/` and `docs/handoffs/` show no diff | Watcher command output |
| 8 | Docs match ADR-0013 | T7 |
| 9 | Deferred Work recorded | below |
| 10 | Watcher PASS, then stop for owner acceptance | `reports/stage-3-phase-11-watcher-<n>.md` |

## Exclusions

See `PHASES.md` Phase 11 Explicit Exclusions. In brief:
- no refresh, rotation, write-back, login, OAuth or token exchange;
- no token decoding or `exp` check;
- no new providers or authentication framework;
- no ADR-0012 or schema change;
- no edits to ADR-0007 or historical handoffs;
- no `VERSION`, tag, release or push to `main`;
- no plasmoid changes;
- no `docs/handoffs/phase-11.md` before acceptance.

## Evidence

### Baseline (Coder re-recorded at `3891626`, 2026-11-27)

```text
$ python3 -m unittest discover -s tests
Ran 48 tests in 0.081s -> OK

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input <file>:
  tests/test_compact_summary.qml:    14 passed, 0 failed
  tests/test_meter_intake.qml:        6 passed, 0 failed
  tests/test_refresh_keys.qml:        7 passed, 0 failed
  tests/test_command_and_times.qml:   6 passed, 0 failed
```

### Post-implementation verification (T1–T6, T8 tests & live check, 2026-11-27)

#### Python unit tests (`tests/test_cursor_credentials.py` + existing suite)

```text
$ python3 -m unittest discover -s tests -v
...
test_1a_ide_jwt_accepted_sends_no_cli_request ... ok
test_1b_ide_401_and_403_fall_back_to_cli_and_reuse_cli_for_plan ... ok
test_1c_non_jwt_ide_never_sent_and_cli_used ... ok
test_1d_absent_ide_db_with_valid_cli_gives_ok ... ok
test_1f_both_sources_fail_exact_outcome_messages ... ok
test_t3_no_fallback_on_upstream_failures ... ok
test_t3_warm_cache_gives_stale_on_fake_500 ... ok
test_t4_plan_info_401_falls_back_to_membership_without_retrying_usage ... ok
test_t5_detect_and_cli_subprocess_wiring ... ok
test_cli_reader_outcomes ... ok
test_ide_reader_outcomes_and_membership ... ok
test_jwt_shape_gate ... ok
...
Ran 60 tests in 8.114s

OK
```

#### QML regression tests (unchanged QML)

```text
$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_compact_summary.qml
Totals: 14 passed, 0 failed, 0 skipped, 0 blacklisted, 3ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_meter_intake.qml
Totals: 6 passed, 0 failed, 0 skipped, 0 blacklisted, 3ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_refresh_keys.qml
Totals: 7 passed, 0 failed, 0 skipped, 0 blacklisted, 6ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_command_and_times.qml
Totals: 6 passed, 0 failed, 0 skipped, 0 blacklisted, 2ms
```

#### Scope & secret audit (T6)

```text
$ git grep -nE 'eyJ[A-Za-z0-9_-]{10,}\.'
(no matches)

$ git diff 3891626 -- decisions/0007-* VERSION plasmoid/ docs/handoffs/ | wc -l
0
```

#### Live install & four-provider check (T8, sanitized — status, plan, meter labels only)

```text
$ ./scripts/install.sh
Upgrading package from file: /home/naorw/.t3/worktrees/horizon/phase-11-cursor-credential-compatibility/plasmoid
Successfully upgraded /home/naorw/.local/share/plasma/plasmoids/com.radilabs.horizon/
Horizon installed.
  collector: /home/naorw/.local/share/horizon/collector
  launcher:  /home/naorw/.local/bin/ai-usage
  plasmoid:  com.radilabs.horizon

$ ~/.local/bin/ai-usage status <id> --json --no-cache (sanitized summary):
{"provider": "codex", "rc": 0, "status": "ok", "plan": "ChatGPT Plus", "meterLabels": ["5-hour limit", "Weekly limit"]}
{"provider": "cursor", "rc": 0, "status": "ok", "plan": "Pro", "meterLabels": ["Cursor Models", "Other Models"]}
{"provider": "stepfun", "rc": 0, "status": "ok", "plan": "Plus", "meterLabels": ["5-Hour Usage", "Weekly Usage"]}
{"provider": "claude", "rc": 0, "status": "ok", "plan": "Pro", "meterLabels": ["Current session", "Current week (all models)"]}
```

#### W11-01 remediation (invalid UTF-8 HTTP 200 body)

Caught `UnicodeDecodeError` alongside `json.JSONDecodeError` in `collector/providers/cursor.py` `_post_json()` (both map to `ProviderError("upstream_error", "Cursor usage response was not valid JSON")`), and added `test_t3_invalid_utf8_body_gives_upstream_error_without_cli_fallback` in `tests/test_cursor_credentials.py`.

```text
$ python3 -m unittest discover -s tests
.............................................................
----------------------------------------------------------------------
Ran 61 tests in 8.596s

OK
```

_(T7 Writer docs pending; independent Watcher evaluation pending.)_

## Deferred Work

- **Local JWT `exp` check** for the CLI token, to skip an expired token without a round trip and report a precise `expired` outcome. It needs reading claims, which this phase forbids. Owner decision required.
- **Cursor desktop opaque-token format.** If Cursor publishes or exposes a supported way to use the 3.28.x IDE session value, revisit whether the IDE source can be used again without decoding.
- **Non-default CLI config locations**, for example `XDG_CONFIG_HOME`. This phase uses only the observed `~/.config/cursor/auth.json` default and the test override.

## Handoff

- Watcher PASS, then explicit owner acceptance.
- Only after acceptance: `docs/handoffs/phase-11.md` and the checkpoint commit. The Coder does not create the handoff.
- Any release is a separate owner action.
- STOP. Do not start another phase.
