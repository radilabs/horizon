# External Watcher Audit Report — Horizon v0.2.0 Baseline

- **Role:** External Watcher / Verifier
- **Baseline audited:** `main` @ `cbc2c93` (`v0.2.0`, clean working tree)
- **Active Factory phase:** None (`TASKS.md` is idle; Stage 2 closed 2026-10-09)
- **Attempt:** 1
- **Date:** 2026-11-27
- **Overall result:** FAIL (open code, quality, and doc-drift findings on `v0.2.0` baseline)

This is an independent external Watcher audit requested by the project owner against the accepted `v0.2.0` repository state. Per `WATCHER.md`, Watcher did not modify code, docs, `TASKS.md`, or `PHASES.md`, and did not authorize a new Stage/Phase. This file is a gitignored runtime report under `reports/`; durable changes require explicit owner authorization before the Driver delegates fixes.

---

## Direct Verification Evidence

Commands executed against `/home/naorw/dev/radilabs/horizon` at `cbc2c93`:

| Check | Result |
|-------|--------|
| `git status` / `git pull --ff-only` | Clean tree, up to date with `origin/main` (`cbc2c93`, tag `v0.2.0`) |
| `python3 -m unittest discover -s tests -v` | 31 tests, OK (0.102s) |
| `QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_compact_summary.qml` | 14 passed, 0 failed |
| `QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_refresh_keys.qml` | 4 passed, 0 failed |
| `QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_meter_intake.qml` | 6 passed, 0 failed |
| `python3 -m py_compile collector/ai-usage collector/*.py collector/providers/*.py tests/*.py` | Exit 0 |
| `bash -n scripts/install.sh scripts/upgrade.sh scripts/uninstall.sh` | Exit 0 |
| `qmllint6 plasmoid/contents/ui/main.qml plasmoid/contents/ui/configGeneral.qml plasmoid/contents/config/config.qml` | Non-fatal warnings (unused import, unqualified access, missing `ComponentBehavior: Bound` / `required property`) |
| `git grep -Ei 'bearer[[:space:]]+[A-Za-z0-9._-]+' -- ':!docs/' ':!tests/'` | No secrets; doc/task prose only |

**Secret audit:** PASS — no live tokens, JWTs, or credential files tracked in Git.

---

## Findings

### Functional & Behavioral Findings

#### W-01 — Unreachable dead code in StepFun credit-plan breakdown
- **Severity:** Medium
- **Reference:** `collector/providers/stepfun.py:403-464`, `docs/usage-schema.md:69`, `docs/providers/stepfun.md:128-130`
- **Finding:** `credit_breakdown()` calls `_combined_credit_left_rate(credit)` and immediately returns `[{"label": "Credits", ...}]` whenever it is non-`None`. Because `_combined_credit_left_rate()` already falls back to `subscription_credit_left_rate` and `topup_credit_left_rate`, lines `422-441` (`"Subscription Credits"` and `"Top-up Credits"`) are unreachable dead code.
- **Evidence:** `collector/providers/stepfun.py:409-441` vs. `445-464`.
- **Required correction:** Either restrict `_combined_credit_left_rate()` to `credit_buckets` so the `"Subscription Credits"` / `"Top-up Credits"` fallback is reachable and tested, or remove the dead branch and update `docs/usage-schema.md` / `docs/providers/stepfun.md` to document `"Credits"` only.

#### W-02 — Redundant `QueryStepPlanRateLimit` HTTP call on StepFun token refresh
- **Severity:** Medium
- **Reference:** `collector/providers/stepfun.py:64-74, 103-116`, ADR-0010 (`decisions/0010-bounded-stepfun-oasis-refresh.md`)
- **Finding:** `_recover_after_auth_rejection()` validates the refreshed token by calling `POST .../QueryStepPlanRateLimit` and discards the returned usage dict. `fetch_usage()` then immediately issues a second identical `POST .../QueryStepPlanRateLimit`.
- **Evidence:** `collector/providers/stepfun.py:69-72` and `104`; reflected in `tests/test_stepfun_oasis_refresh.py:149-150`.
- **Required correction:** Return `(refreshed_token, usage)` from `_recover_after_auth_rejection()` (and from the already-rotated early-return branch on line 89-90) so `fetch_usage()` reuses the validated usage response without a duplicate live request, and update `tests/test_stepfun_oasis_refresh.py`.

#### W-03 — Double activation on Spacebar for Refresh button
- **Severity:** Medium
- **Reference:** `plasmoid/contents/ui/main.qml:525-537`, `tests/test_refresh_keys.qml`
- **Finding:** `refreshButton` (`PlasmaComponents.ToolButton` / `QQC2.AbstractButton`) connects `onClicked: root.refreshUsage()` and also adds `Keys.onSpacePressed: if (enabled) root.refreshUsage()` without setting `event.accepted = true`. `AbstractButton` natively emits `clicked()` on Space release, causing duplicate `refreshUsage()` calls. `Keys.onReturnPressed` / `Keys.onEnterPressed` also omit `event.accepted = true`.
- **Evidence:** `plasmoid/contents/ui/main.qml:534-537`. `tests/test_refresh_keys.qml` mocks a separate button and never tests `Key_Space` or enabled `Key_Return`.
- **Required correction:** Remove `Keys.onSpacePressed` (relying on native `AbstractButton` Space activation), set `event.accepted = true` in `Keys.onReturnPressed` / `Keys.onEnterPressed`, and expand `tests/test_refresh_keys.qml` to verify single activation for Space and Return.

#### W-04 — StepFun auth verification conflates network/upstream errors with rejected tokens
- **Severity:** Medium
- **Reference:** `collector/stepfun_auth_helper.py:91-113`, `collector/ai-usage:75-90`, `plasmoid/contents/ui/configGeneral.qml:40-42`
- **Finding:** `verify_token()` returns `"auth_failed"` for all `ProviderError` codes (lines `108-110` have an `if exc.code == "auth_unavailable": return "auth_failed"` followed immediately by `return "auth_failed"`) and all generic exceptions. `ai-usage auth stepfun set|status` does the same. An offline machine or StepFun 5xx therefore tells the user that their stored token was rejected and must be replaced.
- **Evidence:** `collector/stepfun_auth_helper.py:107-112`, `collector/ai-usage:78-79, 88-89`, `plasmoid/contents/ui/configGeneral.qml:40-42`.
- **Required correction:** Distinguish `upstream_error` (e.g., `"unavailable"` / `"network_error"`) from `auth_unavailable` (`"auth_failed"`), display an accurate non-destructive message in `configGeneral.qml`, and remove the unused `token` parameter in `verify_token()`.

#### W-05 — Settings helper ignores `XDG_DATA_HOME` and fails silently on launch error
- **Severity:** Medium
- **Reference:** `plasmoid/contents/ui/configGeneral.qml:29-58, 84-97`, `scripts/install.sh:6`
- **Finding:** `scripts/install.sh` installs `stepfun_auth_helper.py` to `${XDG_DATA_HOME:-$HOME/.local/share}/horizon/collector/`, while `configGeneral.qml:31` hardcodes `~/.local/share/horizon/collector/stepfun_auth_helper.py` (despite a stale comment on line 30 claiming a repo fallback). If the helper is missing or fails to execute, `stdout` is empty and `applyHelperResult("")` is a no-op, leaving `stepfunStatus` stuck on `"…"` or `stepfunDetail` stuck on `"Saving…"`.
- **Evidence:** `plasmoid/contents/ui/configGeneral.qml:30-32, 35-58, 89-92` vs. `scripts/install.sh:6`.
- **Required correction:** Resolve the helper via `XDG_DATA_HOME` (or invoke through `~/.local/bin/ai-usage` / a wrapper installed alongside `ai-usage`), handle empty stdout / non-zero exit in `configGeneral.qml` with a clear error state, and remove the stale fallback comment.

#### W-06 — Unhandled `NaN`/`inf`/`bool` and I/O edge cases in provider parsers
- **Severity:** Low
- **Reference:** `collector/providers/claude.py:198-225`, `collector/providers/codex.py:79-86, 120-129, 214-264`, `collector/providers/cursor.py:134-141`
- **Finding:**
  - `claude.py` `_utilization()` / `_expired()`, `codex.py` `_meter_from_window()`, and `cursor.py` `_remaining_from_used_percent()` do not reject `bool` values (`float(True) == 1.0`).
  - `claude.py` `_remaining_from_used()` has no `try/except` around `int(round(100.0 - used))`; `codex.py` and `cursor.py` catch `(TypeError, ValueError)` but not `OverflowError` on `float('inf')`. Non-finite floats escape as unhandled exceptions (`collector_error` instead of `upstream_error`).
  - `codex.py` `_load_auth()` does not catch `OSError` on `read_text()`, and `_refresh_tokens()` does not catch `json.JSONDecodeError` on `json.loads(resp.read())`.
- **Evidence:** Direct code inspection of lines cited above.
- **Required correction:** Reject `bool` and non-finite floats (`math.isfinite`) across provider numeric parsers; catch `OSError` in `codex.py._load_auth()` and `json.JSONDecodeError` in `codex.py._refresh_tokens()` as `ProviderError`.

#### W-07 — Unquoted `$HOME` path in `main.qml` shell command
- **Severity:** Low
- **Reference:** `plasmoid/contents/ui/main.qml:70-77`
- **Finding:** `collectorCommand()` builds an unquoted shell string passed to `P5Support.DataSource` (`executable` engine, executed via `/bin/sh -c`). A `$HOME` path containing spaces will break execution.
- **Evidence:** `plasmoid/contents/ui/main.qml:75-77` (compare quoted path in `configGeneral.qml:32`).
- **Required correction:** Shell-quote `collectorBin()` in `collectorCommand()`.

#### W-08 — Relative reset and cache-age strings freeze between refreshes
- **Severity:** Low
- **Reference:** `plasmoid/contents/ui/main.qml:225-236, 272`
- **Finding:** `resetText` and `fetchedAtText` are formatted once in `applyPayload()` and stored as static strings in `providersModel`. With a 15–60 minute refresh interval, stale ages (`Cached · just now`) and reset countdowns become stale between refreshes.
- **Evidence:** `plasmoid/contents/ui/main.qml:232, 272`.
- **Required correction:** Store raw ISO timestamps (`resetAt`, `fetchedAt`) or recompute formatted strings on popup open / a lightweight periodic tick.

#### W-09 — `grep -q` under `set -o pipefail` in install/uninstall scripts
- **Severity:** Low
- **Reference:** `scripts/install.sh:43`, `scripts/uninstall.sh:23`
- **Finding:** `kpackagetool6 --type Plasma/Applet --list 2>/dev/null | grep -q 'com.radilabs.horizon'` can fail with SIGPIPE (`141`) under `set -o pipefail` if output exceeds the pipe buffer, causing `install.sh` to fall through to `--install` on an already-installed applet.
- **Evidence:** `scripts/install.sh:3, 43`, `scripts/uninstall.sh:4, 23`.
- **Required correction:** Capture `kpackagetool6 --list` output in a variable before matching with `grep -Fq` (or avoid `grep -q` in a `pipefail` pipeline).

---

### Code Quality & Test Hygiene Findings

#### W-10 — Shallow top-level-only secret key check in cache writer
- **Severity:** Low
- **Reference:** `collector/cache.py:30-35`
- **Finding:** `write_success()` checks `forbidden` secret keys only at the top level of `data` (case-sensitive), not recursively inside `meters` / `breakdown` objects.
- **Evidence:** `collector/cache.py:31-34`.
- **Required correction:** Recursively inspect nested dicts/lists case-insensitively before writing the cache file.

#### W-11 — `qmllint6` warnings in `main.qml` and `configGeneral.qml`
- **Severity:** Low
- **Reference:** `plasmoid/contents/ui/configGeneral.qml:6, 91`, `plasmoid/contents/ui/main.qml`
- **Finding:** `configGeneral.qml` has an unused `import org.kde.plasma.plasmoid` (line 6) and an unqualified `stepfunBusy = false` (line 91). `main.qml` lacks `pragma ComponentBehavior: Bound`, explicit `required property` on `Repeater` delegates, and qualified `root.plasmoid.configuration` accesses.
- **Evidence:** `qmllint6` output captured during verification.
- **Required correction:** Remove unused import, qualify `page.stepfunBusy`, and modernize QML scoping/delegate properties in `main.qml`.

#### W-12 — Test environment leak and coverage gaps
- **Severity:** Low
- **Reference:** `tests/test_usage_contract.py:311-317`, `tests/test_refresh_keys.qml`
- **Finding:** `test_cache_refuses_secret_fields` overwrites `XDG_CACHE_HOME` and pops it in `finally:` without restoring any pre-existing env value. Unit test coverage is missing for StepFun credit-plan normalization, provider `NaN`/`inf`/`bool` handling, and `stepfun_auth_helper.py` error paths.
- **Evidence:** `tests/test_usage_contract.py:311-317` (compare lines `252-261` and `283-292`).
- **Required correction:** Save/restore `XDG_CACHE_HOME` in `test_cache_refuses_secret_fields`, and add targeted unit tests alongside the fixes for W-01 through W-06.

---

### Documentation vs. Actual Functionality Findings

#### W-13 — `docs/providers/codex.md` contradicts installer and omits duration labels
- **Severity:** Low
- **Reference:** `docs/providers/codex.md:102, 185`, `scripts/install.sh:36-41`, `collector/providers/codex.py:241-246`
- **Finding:**
  - Line 185 states *"Recommended install: symlink to `~/.local/bin/ai-usage`"*, contradicting `scripts/install.sh`, `README.md:61`, and `docs/development.md:14` (which install a wrapper script and explicitly advise against symlinking into the git checkout).
  - Line 102 omits `{n}-day limit` and `{n}-hour limit` labels implemented in `codex.py:241-246` and documented in `docs/usage-schema.md:67`.
- **Required correction:** Update `docs/providers/codex.md` to match the installed wrapper script and the full duration-label mapping.

#### W-14 — Minor doc drift in `cursor.md`, `cache.md`, `release.md`, and ADR-0010 note
- **Severity:** Low
- **Reference:** `docs/providers/cursor.md:145`, `docs/cache.md:38-56`, `docs/release.md:49-52`, `decisions/0010-bounded-stepfun-oasis-refresh.md:31`
- **Finding:**
  - `docs/providers/cursor.md:145` writes `GetPlanInfo.planName` instead of `GetPlanInfo.planInfo.planName` (line 115 is correct).
  - `docs/cache.md:38-56` cache example omits `breakdown` and `secondaryRemainingPercent`, even though `collector/cache.py:42-55` persists them.
  - `docs/release.md:49` uses `gh release create ... --notes-file CHANGELOG.md` (uploading all versions) while line 52 states to use only the section for that version.
  - `decisions/0010-bounded-stepfun-oasis-refresh.md:31` mentions a "process lock", whereas `collector/providers/stepfun.py:31` uses an in-process `threading.Lock` (already noted as non-blocking observation #4 in `reports/stage-1-phase-6-watcher-1.md`).
- **Required correction:** Align `cursor.md`, `cache.md`, and `release.md` with actual behavior; either upgrade `_REFRESH_LOCK` to a cross-process file lock (`fcntl.flock`) or leave ADR-0010 untouched as historical record and clarify in `docs/providers/stepfun.md`.

---

## Factory Gate Note

Per `TASKS.md` and `DRIVER.md`, **no Stage or Phase is currently authorized**. Before the Driver delegates any implementation from this report, the project owner must explicitly authorize the scope (e.g., a maintenance/hardening phase or selected finding IDs `W-01`..`W-14`).
