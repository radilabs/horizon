# Stage 3 / Phase 10 — Post-0.2.0 Remediation

**Status: implemented; Watcher PASS; awaiting owner acceptance** (authorized 2026-11-27). Not accepted.

**Authority:** `PHASES.md` Stage 3 / Phase 10 (the immutable contract), `TASKS.md`
**Input:** `reports/post-v0.2.0-external-watcher-1.md` (external Watcher audit of `v0.2.0`, findings W-01..W-14)
**Previous accepted snapshot:** `docs/handoffs/phase-9.md`
**Contracts to preserve:** ADR-0012 (`decisions/0012-ordered-usage-meters.md`), `docs/usage-schema.md`, ADR-0009/0010 (StepFun credential store and bounded refresh), ADR-0004/0007/0011 (Codex/Cursor/Claude credentials)
**Branch:** `phase-10-post-0.2.0-remediation` (from `eadcfb3`)
**Worktree:** `/home/naorw/.t3/worktrees/horizon/phase-10-post-0.2.0-remediation`

## Goal

Resolve W-01..W-14 with the smallest correction each one needs, with direct evidence for each. No providers, billing, login flows or features. Horizon stays at **0.2.0**.

## Baseline (`eadcfb3`, recorded by the Architect on 2026-11-27)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests` | 31 tests, OK |
| `qmltestrunner6` `test_compact_summary.qml` / `test_meter_intake.qml` / `test_refresh_keys.qml` | 14 / 6 / 4 passed, 0 failed |
| `qmllint6 plasmoid/contents/ui/main.qml plasmoid/contents/ui/configGeneral.qml plasmoid/contents/config/config.qml` | exit 0; **71 warnings** (main.qml 45, configGeneral.qml 25, config.qml 1), all `[unqualified]`; plus Info-level unused-import / ComponentBehavior / implicit-model notes |

The Coder re-records this baseline before the first change. Later counts compare against it.

## Finding → task → acceptance map

Each row is one task. A task is complete only when its acceptance check has direct evidence in the Evidence section below.

### W-01 — StepFun credit breakdown dead branch (Medium)

- **Confirmed.** `_combined_credit_left_rate()` (`collector/providers/stepfun.py:445-464`) falls back to `subscription_credit_left_rate` / `topup_credit_left_rate`. `credit_breakdown()` therefore always returns early with `Credits`, and the `Subscription Credits` / `Top-up Credits` branch (`:421-441`) never runs.
- **Task.** Restrict `_combined_credit_left_rate()` to valid `credit_buckets`. Remove its rate fallbacks so the existing separate-rate branch is reachable. Keep that branch's current rules (`Subscription Credits` from the subscription rate with its reset; `Top-up Credits` from the top-up rate when there is no subscription rate). Never add separate rates together. Update the credit section of `docs/providers/stepfun.md` so it names the labels. `docs/usage-schema.md:69` already lists all three labels and needs no change unless the code disagrees.
- **Acceptance.** Unit tests with sanitized fixtures:
  1. Valid buckets give one `Credits` meter equal to sum(residual)/sum(total).
  2. No buckets plus a subscription rate gives `Subscription Credits` with its reset, and never `Credits`.
  3. No buckets and only a top-up rate gives `Top-up Credits`.
  4. Invalid buckets plus a subscription rate gives `Subscription Credits`.
  5. No meter reports a sum of rates.

### W-02 — Duplicate `QueryStepPlanRateLimit` after refresh (Medium)

- **Confirmed.** `_recover_after_auth_rejection()` validates with `QueryStepPlanRateLimit` and discards the body. The rotated-token early return (`stepfun.py:68-72`) does the same. `fetch_usage()` then posts again (`:69-72` vs `:104`). `tests/test_stepfun_oasis_refresh.py:149-150` expects that duplicate.
- **Task.** Return `(token, usage)` from both recovery paths. `fetch_usage()` uses that usage body and does not post `QueryStepPlanRateLimit` again. The order stays: refresh, then usage validation succeeds, then `secret_set`. On a failed validation, KWallet keeps its previous value and the result is still `auth_unavailable`. Update the FakeHTTP sequences in `tests/test_stepfun_oasis_refresh.py`.
- **Acceptance.**
  1. The refresh-success test records exactly `usage(401) → refresh → usage(200) → set → plan`, with one `QueryStepPlanRateLimit` after the refresh.
  2. The rotated-token path makes one validating usage call and no second one.
  3. A refresh followed by a failed validation gives `auth_unavailable` and no `secret_set`.
  4. All existing StepFun refresh tests pass.

### W-03 — Refresh button key handling (Medium)

- **Double-activation claim: false positive (Architect probe, 2026-11-27).** Qt Quick `Keys` accepts an event by default when a key-specific handler such as `onSpacePressed` is connected. The button's own Space press is then consumed, and `AbstractButton` emits no `clicked()` on release. An offscreen `qmltestrunner6` probe was run in the session scratchpad, not the repo. It used a `PlasmaComponents.ToolButton` with the exact `main.qml` handlers, and Space, Return and Enter each activated **once**. A second variant removed `onSpacePressed` and set `event.accepted = true` on Return. Each key still activated once. The real gap is test coverage: `tests/test_refresh_keys.qml` never presses Space or an enabled Return/Enter.
- **Task (still in scope as the report's smallest fix).** Remove `Keys.onSpacePressed` from `refreshButton` (`plasmoid/contents/ui/main.qml:537`), because native `AbstractButton` Space activation covers it. Make `Keys.onReturnPressed` / `Keys.onEnterPressed` set `event.accepted = true` explicitly. Update `tests/test_refresh_keys.qml` so its button mirrors the production handlers, and use `PlasmaComponents.ToolButton` if the test environment loads it.
- **Acceptance.**
  1. The tests show Space, Return and Enter each give exactly 1 activation when enabled, and 0 when disabled.
  2. F5 still gives 1 activation.
  3. On the real desktop, Space, Return and F5 each refresh once. Check the collector invocation count, or confirm no overlapping request starts.

### W-04 — StepFun auth status conflates offline with rejection (Medium)

- **Confirmed.** `verify_token()` (`collector/stepfun_auth_helper.py:107-112`) returns `auth_failed` for every `ProviderError` and every exception. `ai-usage auth stepfun set|status` (`collector/ai-usage:75-90`) catches `Exception` and prints `auth_failed`. `configGeneral.qml:40-42` then tells the user to replace the token.
- **Task.**
  1. Map only `ProviderError.code == "auth_unavailable"` to `auth_failed`.
  2. Map other `ProviderError` codes and unexpected exceptions to one new status token, `unavailable`. Its message says StepFun could not be reached or verified and that the stored token was kept. It is non-destructive.
  3. Apply this mapping in both the helper and `ai-usage auth stepfun set|status`. Exit codes: `set` returns non-zero for both failures; `status` keeps returning 0.
  4. `cmd_clipboard()` clears the clipboard for `unavailable` too, because the token is already stored.
  5. Add an `unavailable` branch in `configGeneral.qml` `applyHelperResult()`.
  6. Remove the unused `token` parameter from `verify_token()` and update its callers.
  7. Update the helper docstring status list.
- **Acceptance.** Unit tests with a patched `StepFunProvider.fetch_usage`:
  1. `auth_unavailable` gives `auth_failed`.
  2. `upstream_error` and a generic `Exception` (for example `URLError`) give `unavailable`.
  3. Success gives `working`.
  4. No status line contains token material.
  5. A diff review shows the `auth_unavailable` mapping is unchanged and that no new path writes a token KWallet did not already receive.

### W-05 — Settings helper path and silent failure (Medium)

- **Confirmed.** `configGeneral.qml:31` hard-codes `~/.local/share/horizon/collector/stepfun_auth_helper.py`, while `scripts/install.sh:6` honors `XDG_DATA_HOME`. The comment on line 30 claims a repo fallback that does not exist. When stdout is empty, `applyHelperResult("")` changes nothing, so the status stays `…` or `Saving…`.
- **Task.**
  1. Resolve the helper from `StandardPaths.writableLocation(StandardPaths.GenericDataLocation)`, which honors `XDG_DATA_HOME`, plus `/horizon/collector/stepfun_auth_helper.py`. Keep it shell-quoted.
  2. In `onNewData`, an empty stdout or a non-zero `exit code` with no recognized status line sets an explicit error state, for example "Helper failed to run — reinstall with scripts/install.sh". The busy state always clears.
  3. Delete the stale fallback comment.
- **Acceptance.**
  1. A diff shows the XDG-derived path, the quoting and the error branch.
  2. On the real desktop, with the helper temporarily renamed, the settings page shows the error state instead of `…` or `Saving…`. Restore the helper afterwards.
  3. With the helper present, the status reads `Configured · working` as before.

### W-06 — Numeric and I/O edge cases in provider parsers (Low)

- **Partly confirmed.**
  - `bool` is accepted by `float()` in `claude.py` `_utilization()` / `_expired()`, `codex.py` `_meter_from_window()` and `cursor.py` `_remaining_from_used_percent()`. Confirmed.
  - `inf` raises an uncaught `OverflowError` in `round()`. Confirmed.
  - `NaN`: `round(nan)` raises `ValueError`, which `codex.py` and `cursor.py` already catch. **The NaN part is a false positive for Codex and Cursor only.** Claude's `_remaining_from_used()` has no try, so NaN and inf both escape there. Confirmed for Claude.
  - Codex `_load_auth()` does not catch `OSError`, and `_refresh_tokens()` does not catch `JSONDecodeError`. Confirmed.
- **Task.**
  1. Treat `bool` and non-finite values (`math.isfinite`) as invalid in those parsers. They give the same result as the parser's existing invalid-value path: meter omitted, or `None`.
  2. In `_load_auth()`, map `OSError` to `ProviderError("auth_unavailable", …)`. Check first how `fetch_usage()` handles a missing file, and keep that message where it exists.
  3. In `_refresh_tokens()`, map `JSONDecodeError` to `ProviderError("upstream_error", …)`. Never map it to `auth_unavailable`.
  4. Codex refresh and write-back logic otherwise stays unchanged.
- **Acceptance.**
  1. Unit tests give `True`, `float("inf")` and `float("nan")` to each cited parser, and none raises.
  2. Codex/Cursor/Claude normalize still gives the same meters for the existing fixtures.
  3. An unreadable auth file (`OSError`) gives `auth_unavailable`.
  4. A refresh response body that is not JSON gives `upstream_error`.
  5. No test leaves an auth file modified.

### W-07 — Unquoted collector path (Low)

- **Confirmed.** `main.qml:75-77` builds `<home>/.local/bin/ai-usage status <id> --json` without quoting. The executable engine runs it through `/bin/sh -c`.
- **Task.** Single-quote the path in `collectorCommand()` and escape embedded `'` as `'\''`. `providerIdFromCommand()` must still find the provider id, because DataSource keys are the command string.
- **Acceptance.**
  1. A QML unit test, or a pure-JS helper test, shows a home path with a space and one with `'` produce a correctly quoted command.
  2. `providerIdFromCommand()` returns the right id for both.
  3. On the real desktop, all four providers still load.

### W-08 — Relative reset and cache-age text freezes (Low)

- **Confirmed.** `resetText` (`popupMetersJson`, `main.qml:225-236`) and `fetchedAtText` (`:272`) are formatted once per payload.
- **Task.** Keep the raw `resetAt` / `fetchedAt` in the model. Recompute the displayed relative strings when the popup opens (`expanded` becomes true), and on a lightweight Timer (for example 60 s) only while the popup is expanded. The Timer triggers no collector call. Text formats and layout stay as they are.
- **Acceptance.**
  1. A test, or a pure-function test with an injected "now", shows the same stored timestamp formats differently at two times.
  2. A diff shows the timer calls no refresh or collector.
  3. On the real desktop, the cache age and reset text move forward without a Refresh.

### W-09 — `grep -q` under `pipefail` (Low)

- **Confirmed** as a latent risk: `scripts/install.sh:3,43` and `scripts/uninstall.sh:4,23`.
- **Task.** Capture `kpackagetool6 --type Plasma/Applet --list 2>/dev/null || true` in a variable, then match with `grep -Fq` on a here-string. Keep the install/upgrade/remove decision logic as it is.
- **Acceptance.**
  1. `bash -n` passes on both scripts.
  2. A diff shows no `| grep -q` remains in any `pipefail` script.
  3. `scripts/install.sh` on this machine takes the `--upgrade` branch for the installed applet. Record the output.

### W-10 — Shallow cache secret-key check (Low)

- **Confirmed.** `collector/cache.py:31-34` checks only top-level keys, and is case-sensitive.
- **Task.** Walk `data` recursively through dicts and lists. Compare each **key** with `str(key).lower()` against the **existing** forbidden set: `access_token`, `refresh_token`, `id_token`, `authorization`, `cookie`. Match whole keys, not substrings, and never inspect values. Keep raising `ValueError`. The persisted field list (`cache.py:42-55`) does not change.
- **Acceptance.** Unit tests:
  1. `meters[0]["Access_Token"]` is rejected.
  2. `breakdown[0]["cookie"]` is rejected.
  3. A top-level `Authorization` is rejected.
  4. A normal four-provider payload with labels such as `Credits` still caches.
  5. The cached envelope's keys are identical to the baseline.

### W-11 — qmllint warnings (Low)

- **Confirmed** at the baseline. See the counts above.
- **Task.** Fix only the cited warnings:
  - In `configGeneral.qml`, remove the unused `import org.kde.plasma.plasmoid` (line 6) and qualify `page.stepfunBusy` (line 91).
  - In `main.qml`, add `pragma ComponentBehavior: Bound`, add explicit `required property` declarations to the `Repeater` delegates (including `model` / `index` or the specific roles they use), and qualify `plasmoid.configuration` accesses through the root id.

  Make no layout, visual or behavior change. Do not chase uncited warnings such as unqualified `i18n`.
- **Acceptance.**
  1. A `qmllint6` rerun on the same three files shows none of the cited diagnostics, and a total warning count of at most 71.
  2. All QML tests pass.
  3. On the real desktop, the popup still renders every provider and meter, and the settings checkboxes still read and write configuration. This guards against Bound-scope regressions.

### W-12 — Test env leak and coverage gaps (Low)

- **Confirmed.** `tests/test_usage_contract.py:311-317` pops `XDG_CACHE_HOME` without restoring a previous value.
- **Task.** Save and restore `XDG_CACHE_HOME`, or use `mock.patch.dict(os.environ, …)`. The coverage gaps are filled by the W-01, W-02, W-04 and W-06 tests above. Add no unrelated tests.
- **Acceptance.**
  1. `XDG_CACHE_HOME=/some/value python3 -m unittest tests.test_usage_contract` leaves the value unchanged after the test. Show this with a small assertion or test.
  2. The new tests for W-01, W-02, W-04 and W-06 exist and pass.

### W-13 — `docs/providers/codex.md` drift (Low)

- **Confirmed.** Line 185 says "symlink" but the installer writes a wrapper script. Line 102 omits `{n}-day limit` / `{n}-hour limit`.
- **Task.** Replace the symlink line with the wrapper-script install (`scripts/install.sh`). Make the label row match `codex.py` `_window_label()`, or point to `docs/usage-schema.md:67`.
- **Acceptance.** A diff, plus a manual comparison against `codex.py:233-250` and `scripts/install.sh:36-41`.

### W-14 — Minor doc drift (Low)

- **Confirmed.**
  - `docs/providers/cursor.md:145` says `GetPlanInfo.planName`.
  - The `docs/cache.md` example omits the optional `breakdown` / `secondaryRemainingPercent`.
  - `docs/release.md:49` passes the whole `CHANGELOG.md`.
  - ADR-0010:31 says "process lock", but the code uses an in-process `threading.Lock`.
- **Task.**
  1. Fix the cursor path to `GetPlanInfo.planInfo.planName`.
  2. In `docs/cache.md`, list the persisted keys exactly as `cache.py` writes them (present only when the payload has them). Optionally add them to the example.
  3. Make `docs/release.md` extract the version section, for example into a temp notes file, before `gh release create --notes-file`. This is doc text only. Do not run it.
  4. In `docs/providers/stepfun.md`, state that refresh recovery is serialized by an in-process `threading.Lock` only, so separate `ai-usage` processes are not serialized.
  5. **Do not edit ADR-0010. Do not add a cross-process lock.**
- **Acceptance.**
  1. A diff of the four doc files only. `git diff eadcfb3 -- decisions/` is empty.
  2. `stepfun.py` `_REFRESH_LOCK` is unchanged.

## False positives

- **W-03 (double activation):** false positive. The Architect's offscreen probe shows exactly one activation per key with the shipped handlers. The fix remains in scope as cleanup plus missing tests, as the report asks. The Coder must re-prove single activation in the repo test, and must not claim the shipped widget was double-firing.
- **W-06 (NaN in Codex and Cursor):** false positive for NaN only. `round(nan)` raises the `ValueError` they already catch. `bool`, `inf` and every Claude case are real.
- All other findings (W-01, W-02, W-04, W-05, W-07..W-14) were confirmed against `eadcfb3` source.

## Overlapping fixes

- **W-01, W-02, W-06 and W-12** all add tests. The W-12 coverage gap is satisfied by those tests, not by separate work.
- **W-04 and W-05** both edit `configGeneral.qml` `applyHelperResult()` / `onNewData`. Do them in one pass so the new `unavailable` status and the helper-failure state don't collide. `unavailable` comes from the helper. The helper-failure state is for an empty stdout or a non-zero exit with no status line.
- **W-05 and W-11** both touch `configGeneral.qml`. The `page.stepfunBusy` qualification is in the `onNewData` block that W-05 rewrites.
- **W-03, W-07, W-08 and W-11** all edit `main.qml`. Apply the W-11 `ComponentBehavior: Bound` / `required property` change **last**, or re-verify every delegate role W-08 adds (raw `resetAt` / `fetchedAt`) under Bound scoping.
- **W-02 and W-04** both depend on `StepFunProvider.fetch_usage()`. W-04's status mapping must hold with W-02's new return shape. Recovery still raises `auth_unavailable` on a rejected refresh.
- **W-10 and W-14 (`docs/cache.md`)**: the documented persisted-key list must match `cache.py` after W-10. W-10 must not change that list.

## Architectural risks — lines the Coder must not cross

1. **StepFun KWallet write order (ADR-0010).** `secret_set` is called only after a refreshed token's `QueryStepPlanRateLimit` returned 200 with a usable body. Reusing that body (W-02) must not move `secret_set` earlier, skip validation, or write on a failed validation.
2. **`auth_unavailable` semantics.** W-04 adds a status. It does not reclassify any real rejection as `unavailable`, and does not change provider `ProviderError` codes. W-06's new mappings use `upstream_error` for malformed upstream data and `auth_unavailable` only for a local auth file that is unreadable.
3. **User-pasted StepFun token.** The settings and CLI `set` flow already stores the pasted token before verifying, because `fetch_usage()` reloads from KWallet. W-04 does not change that order and adds no other write path. Changing it is Deferred Work.
4. **No cross-process lock, no ADR edits.** `_REFRESH_LOCK` stays a `threading.Lock`. ADR-0010, ADR-0012 and every accepted decision stay byte-identical.
5. **ADR-0012 meters contract.** Meter labels, order, remaining-percent semantics, the `meters` → `breakdown` → primary/secondary intake, and the cached field set do not change. The one exception is W-01: the documented `Subscription Credits` / `Top-up Credits` labels become reachable again. W-01 must not create a meter that sums independent rates.
6. **Secret handling.** No token in argv, logs, stdout, test fixtures, docs or evidence. W-07/W-05 quoting must not move secrets into commands, which only carry paths and action words. W-10 inspects keys, never values, and never prints values in its error.
7. **QML scoping (W-11).** `ComponentBehavior: Bound` makes delegates lose implicit outer-scope and model access. Every delegate must declare what it uses, and the real-desktop check is mandatory. No redesign, no new settings, no new config keys.
8. **Codex credentials.** W-06 only adds exception mapping. Refresh, the `_save_auth` atomic write and the `0600` mode are unchanged.
9. **Plasma environment.** `GenericDataLocation` follows plasmashell's own `XDG_DATA_HOME`. If that differs from the installer's shell, W-05's error state is the intended visible outcome. Do not add path guessing or repo fallbacks.
10. **Release boundary.** No change to `VERSION`, `plasmoid/metadata.json` `KPlugin.Version` or the README version line. No tag, no release. A `CHANGELOG.md` "Unreleased" entry is allowed only if the Driver asks; it is not required by the contract.

## Execution Tasks

- [x] Re-record the baseline (tests, qmllint counts, `ai-usage status <id> --json` safe fields for all four providers) in Evidence.
- [x] W-01 StepFun credit breakdown, tests, `docs/providers/stepfun.md`.
- [x] W-02 StepFun refresh usage reuse, updated refresh tests.
- [x] W-04 + W-05 StepFun auth status and settings helper (one `configGeneral.qml` pass), tests.
- [x] W-06 provider parser edge cases, tests.
- [x] W-10 recursive cache key check, tests.
- [x] W-12 env restore in `test_cache_refuses_secret_fields`.
- [x] W-03 Refresh keys, expanded `tests/test_refresh_keys.qml`.
- [x] W-07 command quoting, test.
- [x] W-08 live relative times.
- [x] W-11 cited qmllint fixes (last `main.qml` change), qmllint rerun.
- [x] W-09 installer/uninstaller pipefail fix, run `scripts/install.sh`.
- [x] W-13 and W-14 docs.
- [x] Full test run, secret audit (`git grep -Ei 'bearer[[:space:]]+[A-Za-z0-9._-]+' -- ':!docs/' ':!tests/'` plus a diff review), `git diff eadcfb3 -- decisions/ VERSION plasmoid/metadata.json` empty.
- [x] Real-desktop verification: popup, Refresh keys (F5, Space, Return), settings status (working / helper-missing) & checkbox config read/write/restore, live 65s relative-time progression.
- [ ] Independent Watcher evaluation against PHASES.md Phase 10 criteria 1–11 (`reports/stage-3-phase-10-watcher-<n>.md`).

## Acceptance Criteria (summary; PHASES.md is authoritative)

1. Every W-ID resolved per its acceptance check above, or recorded with evidence as a false positive where this file allows.
2. StepFun credit labels and single-validation refresh, with KWallet write only after success.
3. Offline or upstream failure is never reported as a rejected token.
4. No regression across the four providers. All old and new tests pass.
5. ADR-0012 contract unchanged except the W-01 labels becoming reachable again.
6. Cited qmllint warnings gone. Total at most 71.
7. Real-desktop check after install.
8. Secret audit passes.
9. No version or release change.
10. Deferred Work recorded.
11. Watcher PASS, then owner acceptance.

## Exclusions

As in `PHASES.md` Phase 10: no providers, billing, login flows or features; no auth-boundary or ADR-0012 change; no cross-process lock; no ADR edits; no QML redesign; no uncited qmllint work; no version, tag or release; no rewriting of accepted Phase 0–9 records.

## Evidence

### Baseline (Coder re-recorded at `eadcfb3`, 2026-11-27)

```text
python3 -m unittest discover -s tests -v
Ran 31 tests in 0.071s -> OK

QT_QPA_PLATFORM=offscreen qmltestrunner6:
  tests/test_compact_summary.qml: 14 passed, 0 failed
  tests/test_meter_intake.qml:     6 passed, 0 failed
  tests/test_refresh_keys.qml:     4 passed, 0 failed

qmllint6:
  plasmoid/contents/ui/main.qml: 45 warnings
  plasmoid/contents/ui/configGeneral.qml: 25 warnings
  plasmoid/contents/config/config.qml: 1 warnings
  Total: 71 warnings

./collector/ai-usage status <id> --json (safe fields):
  codex:   status=ok, plan="ChatGPT Plus", meters=[5-hour limit 99%, Weekly limit 99%]
  cursor:  status=ok, plan="Pro", meters=[Cursor Models 60%, Other Models 86%]
  stepfun: status=ok, plan="Plus", meters=[5-Hour Usage 97%, Weekly Usage 98%]
  claude:  status=ok, plan="Pro", meters=[Current session 95%, Current week (all models) 92%]
```

### Post-implementation verification (2026-11-27)

#### Python unit tests (W-01, W-02, W-04, W-06, W-10, W-12)

```text
$ python3 -m unittest discover -s tests
................................................
----------------------------------------------------------------------
Ran 48 tests in 0.082s

OK
```

`XDG_CACHE_HOME` preservation check (W-12):

```text
$ XDG_CACHE_HOME=/some/value python3 -c '...'
Ran 23 tests in 0.018s
OK
XDG_CACHE_HOME preserved: /some/value
```

#### QML tests (W-03, W-07, W-08, plus Phase 8/9 regression)

```text
$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_compact_summary.qml
Totals: 14 passed, 0 failed, 0 skipped, 0 blacklisted, 3ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_meter_intake.qml
Totals: 6 passed, 0 failed, 0 skipped, 0 blacklisted, 2ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_refresh_keys.qml
Totals: 7 passed, 0 failed, 0 skipped, 0 blacklisted, 8ms
(Uses PlasmaComponents.ToolButton mirroring main.qml: F5, Space, Return, Enter each activate once when enabled, 0 when disabled.)

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_command_and_times.qml
Totals: 6 passed, 0 failed, 0 skipped, 0 blacklisted, 2ms
(Covers W-07 spaces/single-quote/status-word quoting + providerIdFromCommand, and W-08 formatRelative/formatFetchedAt advancing with injected nowMs.)
```

#### `qmllint6` (W-11)

```text
qmllint6 plasmoid/contents/ui/main.qml: 3 warnings  (down from 45)
qmllint6 plasmoid/contents/ui/configGeneral.qml: 24 warnings  (down from 25)
qmllint6 plasmoid/contents/config/config.qml: 1 warnings  (unchanged)
Total: 28 warnings (baseline: 71)
```

`main.qml` remaining 3 warnings are KConfigPropertyMap binding/missing-property notes on `root.plasmoid.configuration`; zero `ComponentBehavior: Bound`, zero implicit `model`/`index`/`modelData`, zero `[unqualified]` warnings. `configGeneral.qml` has zero `unused-imports` and zero `stepfunBusy` warnings.

#### Installer scripts & live install (W-09)

```text
$ bash -n scripts/install.sh scripts/upgrade.sh scripts/uninstall.sh
(exit 0)

$ grep -n '| grep -q' scripts/*.sh
(no matches)

$ ./scripts/install.sh
Upgrading package from file: /home/naorw/.t3/worktrees/horizon/phase-10-post-0.2.0-remediation/plasmoid
Successfully upgraded /home/naorw/.local/share/plasma/plasmoids/com.radilabs.horizon/
Horizon installed.
  collector: /home/naorw/.local/share/horizon/collector
  launcher:  /home/naorw/.local/bin/ai-usage
  plasmoid:  com.radilabs.horizon
```

#### Installed collector & StepFun auth status (all 4 providers)

```text
$ ~/.local/bin/ai-usage status codex --json
{"provider":"codex","displayName":"Codex","plan":"ChatGPT Plus","remainingPercent":99,"resetAt":"2026-11-27T22:54:17+01:00","status":"ok","meters":[{"label":"5-hour limit","remainingPercent":99,"resetAt":"2026-11-27T22:54:17+01:00"},{"label":"Weekly limit","remainingPercent":99,"resetAt":"2026-12-03T11:42:03+01:00"}],"breakdown":[{"label":"5-hour limit","remainingPercent":99,"resetAt":"2026-11-27T22:54:17+01:00"},{"label":"Weekly limit","remainingPercent":99,"resetAt":"2026-12-03T11:42:03+01:00"}],"secondaryRemainingPercent":99}

$ ~/.local/bin/ai-usage status cursor --json
{"provider":"cursor","displayName":"Cursor","plan":"Pro","remainingPercent":59,"resetAt":"2026-11-28T09:57:44+01:00","status":"ok","meters":[{"label":"Cursor Models","remainingPercent":59,"resetAt":"2026-11-28T09:57:44+01:00"},{"label":"Other Models","remainingPercent":71,"resetAt":"2026-11-28T09:57:44+01:00"}],"breakdown":[{"label":"Cursor Models","remainingPercent":59,"resetAt":"2026-11-28T09:57:44+01:00"},{"label":"Other Models","remainingPercent":71,"resetAt":"2026-11-28T09:57:44+01:00"}],"secondaryRemainingPercent":71}

$ ~/.local/bin/ai-usage status stepfun --json
{"provider":"stepfun","displayName":"StepFun","plan":"Plus","remainingPercent":97,"resetAt":"2026-11-27T22:00:00+01:00","status":"ok","meters":[{"label":"5-Hour Usage","remainingPercent":97,"resetAt":"2026-11-27T22:00:00+01:00"},{"label":"Weekly Usage","remainingPercent":98,"resetAt":"2026-12-02T21:00:00+01:00"}],"breakdown":[{"label":"5-Hour Usage","remainingPercent":97,"resetAt":"2026-11-27T22:00:00+01:00"},{"label":"Weekly Usage","remainingPercent":98,"resetAt":"2026-12-02T21:00:00+01:00"}],"secondaryRemainingPercent":98}

$ ~/.local/bin/ai-usage status claude --json
{"provider":"claude","displayName":"Claude","plan":"Pro","remainingPercent":95,"resetAt":"2026-11-27T22:40:00.096104+00:00","status":"ok","meters":[{"label":"Current session","remainingPercent":95,"resetAt":"2026-11-27T22:40:00.096104+00:00"},{"label":"Current week (all models)","remainingPercent":92,"resetAt":"2026-11-30T02:00:00.096127+00:00"}],"breakdown":[{"label":"Current session","remainingPercent":95,"resetAt":"2026-11-27T22:40:00.096104+00:00"},{"label":"Current week (all models)","remainingPercent":92,"resetAt":"2026-11-30T02:00:00.096127+00:00"}],"secondaryRemainingPercent":92}

$ ~/.local/bin/ai-usage auth stepfun status
working

$ python3 ~/.local/share/horizon/collector/stepfun_auth_helper.py status
working
```

#### Protected-file diff & secret audit

```text
$ git diff eadcfb3 -- decisions/ VERSION plasmoid/metadata.json README.md | wc -l
0

$ git grep -Ei 'bearer[[:space:]]+[A-Za-z0-9._-]+' -- ':!docs/' ':!tests/'
tasks/phase-1-codex.md:* Log secret check: no bearer tokens in journal for Horizon
tasks/phase-6-stepfun-auth-resilience.md:- `git grep` only hits documented field names / Cursor Bearer description.
```

#### Real-desktop verification (`WAYLAND_DISPLAY=wayland-1 DISPLAY=:0`)

1. **Popup (`plasmawindowed com.radilabs.horizon`):** Launched cleanly with zero stderr / zero QML Bound-scope errors. Screenshot saved at `reports/phase-10-popup.png` (gitignored) and visually verified: all 4 providers (Codex, Cursor, StepFun, Claude), all 8 meters, plans, progress bars, reset labels, separators, and header Refresh button render as expected.
2. **Settings page helper status (`configGeneral.qml` loaded via `qml6` against installed plasmoid):**
   - Helper present: `STATUS=Configured · working`, `DETAIL=Token accepted by StepFun.`, `BUSY=false`, `CMD=python3 '/home/naorw/.local/share/horizon/collector/stepfun_auth_helper.py' status`.
   - Helper temporarily renamed: `STATUS=Helper error`, `DETAIL=Helper failed to run — reinstall with scripts/install.sh.`, `BUSY=false`. Helper restored immediately after.
3. **W-03 live Refresh keys (F5, Space, Return) on installed popup (`QT_QPA_PLATFORM=xcb DISPLAY=:0 plasmawindowed com.radilabs.horizon` under `strace -f -tt -e trace=execve`, keys delivered via X11 `XSendEvent` — no Remote Control dialog):**
   - Counted `execve("/home/naorw/.local/bin/ai-usage", ["...", "status", "<id>", "--json"])` calls per wave:
     - Initial load (`19:26:43.078`–`19:26:43.083`): **4 calls** (`codex`, `cursor`, `stepfun`, `claude`).
     - `F5` (`19:26:49.256`–`19:26:49.262`, +6.2s): **4 calls** (`codex`, `cursor`, `stepfun`, `claude`).
     - `Tab` (focus `refreshButton`) + `Space` (`19:26:55.818`–`19:26:55.827`, +6.5s): **4 calls** (`codex`, `cursor`, `stepfun`, `claude`).
     - `Return` (`19:27:01.861`–`19:27:01.868`, +6.0s): **4 calls** (`codex`, `cursor`, `stepfun`, `claude`).
   - Total: **16 calls** across 4 waves (exactly 1 refresh = 4 provider calls per key; zero duplicate or overlapping invocations).
4. **W-08 live relative-time progression without Refresh (`plasmawindowed com.radilabs.horizon` on `WAYLAND_DISPLAY=wayland-1` under `strace -f -tt -e trace=execve`):**
   - **Live reset countdowns (65s wait):**
     - Initial load at `19:24:57` (4 `ai-usage` execs).
     - `T0=19:25:03` (`reports/phase-10-w08-t0.png`): Codex 5-hour `Resets in 3h 29m`, Cursor Models/Other Models `Resets in 14h 32m`, StepFun 5-Hour `Resets in 2h 35m`, Claude Current session `Resets in 4h 15m`.
     - Waited 65 seconds without pressing Refresh (past the 60s `relativeTimeTimer`). `strace` recorded **0** new `ai-usage` executions between `T0` and `T1`.
     - `T1=19:26:09` (`reports/phase-10-w08-t1.png`): Codex 5-hour `Resets in 3h 28m`, Cursor Models/Other Models `Resets in 14h 31m`, StepFun 5-Hour `Resets in 2h 34m`, Claude Current session `Resets in 4h 14m`.
   - **Live stale cache age (72s wait via temporary fake collector in throwaway `$TMPHOME/.local/bin/ai-usage` with `XDG_DATA_HOME=/home/naorw/.local/share`, real `~/.local/bin/ai-usage` untouched):**
     - Fake collector emitted stale payload with `fetchedAt="2026-11-27T19:41:55+01:00"` (no tokens).
     - `T0=19:44:05` (`reports/phase-10-w08-cache-t0.png`, `exec_lines=4`): **`Cached · 2m ago`** on all 4 providers.
     - Waited 72 seconds without Refresh. `strace` recorded **0** new `ai-usage` executions (`exec_lines=4` unchanged).
     - `T1=19:45:18` (`reports/phase-10-w08-cache-t1.png`, `exec_lines=4`): **`Cached · 3m ago`** on all 4 providers.
     - Temporary directory removed; `~/.local/bin/ai-usage status codex --json` confirmed running the real collector (`status: "ok"`, `plan: "ChatGPT Plus"`).
5. **W-11 live settings checkbox config read/write/restore (`configGeneral.qml` from `/home/naorw/.local/share/plasma/plasmoids/com.radilabs.horizon/contents/ui/configGeneral.qml` + live `plasmashell` panel applet):**
   - Installed `configGeneral.qml` loaded via `qml6` (`reports/phase-10-w11-settings.png`):
     ```text
     READ_INIT: Codex=true Cursor=true StepFun=true Claude=false
     CFG_INIT:  enableCodex=true enableCursor=true enableStepfun=true enableClaude=false
     AFTER_TOGGLE_CODEX_OFF: checkbox=false cfg.enableCodex=false
     AFTER_TOGGLE_CLAUDE_ON: checkbox=true cfg.enableClaude=true
     AFTER_RESTORE_CODEX:    checkbox=true cfg.enableCodex=true
     STEPFUN_STATUS: Configured · working
     ```
   - Live `plasmashell` panel applet (`com.radilabs.horizon`, `[General]`): `BEFORE=true`, `AFTER_WRITE_FALSE=false`, `AFTER_RESTORE=true` (original config restored).

## Deferred Work

- **StepFun set-then-verify order.** A pasted token is written to KWallet before verification (see Risk 3). Whether to verify before storing is a separate decision that would touch ADR-0009/0010.
- **Cross-process StepFun refresh lock** (`fcntl.flock`). Explicitly excluded by the owner. ADR-0010's "process lock" wording stays as historical record.
- **Uncited qmllint warnings**, such as unqualified `i18n` and `plasmoid` in `configGeneral.qml`, and the one in `config.qml`.
- **Showing both `Subscription Credits` and `Top-up Credits` at once** when a payload has both rates and no buckets. The current rule shows only the subscription rate in that case. Changing it would be new display behavior.
- **Expanding the cache forbidden-key list** (for example `oasis-token`, `api_key`). W-10 keeps the existing set.

## Handoff

- Watcher PASS, then explicit owner acceptance.
- Only after acceptance: `docs/handoffs/phase-10.md` and the checkpoint commit. The Coder does not create the handoff.
- Any release is a separate owner action.
- STOP. Do not start another phase.
