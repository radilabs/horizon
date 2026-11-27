# Stage 4 / Phase 12 — Xiaomi MiMo Token Plan

**Status: ACCEPTED** (2026-11-27). Historical. **Not executable.** Snapshot: `docs/handoffs/phase-12.md`.

**Authority:** `PHASES.md` Stage 4 / Phase 12 (the immutable contract, including **Owner Decisions**), `TASKS.md`
**Discovery record:** `docs/research/xiaomi-mimo-coding-plan.md` (research only; not a contract)
**Credential decision:** ADR-0009 items 2 and 7 (a user-supplied secret in the OS credential store, reused `secret_store`). No new ADR. ADR-0009 text is not edited.
**Contracts to preserve:** ADR-0012 (`decisions/0012-ordered-usage-meters.md`), `docs/usage-schema.md`, ADR-0004/0007/0010/0011/0013, and the accepted behavior of Codex, Cursor, StepFun and Claude
**Previous accepted snapshot:** `docs/handoffs/phase-11.md`
**Branch:** `phase-12-xiaomi-mimo-token-plan` (from `220563f`, Horizon `0.2.1`)
**Worktree:** `/home/naorw/.t3/worktrees/horizon/phase-12-xiaomi-mimo-token-plan`

## Goal

Add provider `mimo` (`Xiaomi MiMo`). It shows the remaining Token Plan credits as one ADR-0012 meter, `Credits`. The data comes from Xiaomi's official `GET https://token-plan-{region}.xiaomimimo.com/v1/platform/token_plan`. The `tp-` key is user-supplied and stored only in KWallet. Requests go only to the explicitly configured region, and MiMo is fetched only on a manual refresh.

## Baseline (`220563f`, recorded by the Architect on 2026-11-27)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests` | 61 tests, OK |

Before the first change, the Coder re-records this baseline and the QML suites (`QT_QPA_PLATFORM=offscreen qmltestrunner6 -input` for `tests/test_compact_summary.qml`, `tests/test_meter_intake.qml`, `tests/test_refresh_keys.qml`, `tests/test_command_and_times.qml`).

## Architectural lines the Coder must not cross

- **One host, one request.** `fetch_usage()` sends exactly one `GET` to `https://token-plan-{region}.xiaomimimo.com/v1/platform/token_plan`. `{region}` is the configured value from `{sgp, cn, ams}`, and the default is `sgp`. Region probing, fallback to another region, retries on another host after a 401, any other Xiaomi host, console/cookie/SSO paths, inference calls and Finance endpoints are all forbidden. The test-only `MIMO_API_BASE` override replaces the whole origin and must not add any extra request.
- **Key source: KWallet only.** Read the key from `secret_store.get("mimo", "token-plan-key")`. Never read `XIAOMI_API_KEY`, `MIMO_API_KEY` or any other environment variable for the key. Never open `~/.bashrc`, a shell profile, any plaintext key file, or anything under `~/.local/share/mimocode/` or `~/.config/mimocode/`. Add no CLI flag that carries the key.
- **No secret leakage.** The key is never placed in argv (collector, helper, or the QML `exec` string), stdout, stderr, exception messages, cache, logs, docs or evidence. `ProviderError` messages contain no key text, length or prefix beyond the literal word `tp-` used in user-facing instructions.
- **Manual refresh only for MiMo.** The automatic triggers in `main.qml` never spawn `ai-usage status mimo`: `refreshTimer.onTriggered`, `Component.onCompleted`, `onExpandedChanged` and `onConfigChanged()` / the configuration `Connections`. Only the Refresh button (click, Space, Return, Enter) and the F5 `Shortcut` may.
- **Schema fixed.** Add no new status code, meter field, payload field or cached field. Make no change to ADR-0012 or `docs/usage-schema.md`.
- **No behavior change for other providers.** The only shared change is the refresh split in `main.qml`, which leaves the other four providers on exactly the same triggers as before. Do not modify `stepfun_auth_helper.py`. In `cmd_auth`, the StepFun branch is unchanged.
- **No framework.** Make no generic auth layer, no polling scheduler and no per-provider interval.

## Execution Tasks

Each task is complete only when its acceptance check has direct evidence in the Evidence section.

### T1 — Provider module: request and status mapping

- **Task.** Create `collector/providers/mimo.py` with `MiMoProvider`:
  1. `id = "mimo"`, `display_name = "Xiaomi MiMo"`, and `REGIONS = ("sgp", "cn", "ams")`.
  2. The constructor takes `region: str = "sgp"`. An invalid region raises `ProviderError("provider_unavailable", …)` with no request.
  3. The base URL is `MIMO_API_BASE` (test-only, whole origin) when set, else `https://token-plan-{region}.xiaomimimo.com`. The path is `/v1/platform/token_plan`.
  4. `detect()` raises `auth_unavailable` when `secret_store.get("mimo", "token-plan-key")` returns nothing. A `SecretStoreError` raises `auth_unavailable` with the message `Credential store unavailable: <reason>`, matching StepFun's `_load_token` (`collector/providers/stepfun.py:133-134`).
  5. `fetch_usage(**_opts)` makes one `GET` with `Authorization: Bearer <key>`, `Accept: application/json`, and the same timeout as the StepFun or Cursor providers. `force_refresh` is ignored.
  6. Status mapping:
     - HTTP 401 → `auth_unavailable`. Message: `Xiaomi MiMo rejected the Token Plan key for region <region> (HTTP 401). Check the key and the configured region.`
     - `URLError`, timeout, any other non-200 status including 403, invalid JSON, or a non-object body → `upstream_error`.
  7. The key shape check: a non-empty `str`, `startswith("tp-")`, no whitespace, and `8 <= len <= 256`. Use it in `detect()`/`fetch_usage()` so a malformed stored value gives `auth_unavailable` with no request.
- **Acceptance.** Tests use a fake HTTP server through `MIMO_API_BASE`, a stubbed `secret_store`, and a request log of method, path and the `Authorization` value compared in memory only:
  1. A 200 response gives one request: `GET /v1/platform/token_plan` with the fixture bearer.
  2. A 401 response gives `auth_unavailable`, the message names the region, and exactly one request is logged.
  3. Each of these gives `upstream_error`: 403, 500, `URLError` from a closed port, a timeout, invalid JSON, and a JSON array.
  4. Each of these gives `auth_unavailable` with **zero** requests: a missing key, an empty key, the key `sk-wrong-prefix`, and a key containing whitespace.
  5. An invalid region (for example `us`) gives `provider_unavailable` with zero requests.
  6. Without `MIMO_API_BASE`, a unit test of the URL builder gives `https://token-plan-sgp.xiaomimimo.com/v1/platform/token_plan` for the default, and the `cn` and `ams` variants when configured. No live request is made.

### T2 — Normalization: meter, period and plan

- **Task.** In `mimo.py`, build the payload with `providers.contract.project_ok`:
  1. Validate `quota`. It must be an object. `total_credits` must be an `int`, not a `bool`, and greater than 0, or the result is `upstream_error` with no meter. `remaining_credits` must be an int. If it is absent, compute `max(0, total − used)` when `used_credits` is an int, else return `upstream_error`. Clamp `remaining` to `0..total`.
  2. `remainingPercent = max(0, min(100, int(round(remaining / total * 100))))`.
  3. Meter: `{"label": "Credits", "remainingPercent": …, "resetAt": …}`. Omit `resetAt` when it is unknown.
  4. `resetAt`: parse `period.end_at` with `"%Y-%m-%d %H:%M:%S"` as UTC and emit `YYYY-MM-DDTHH:MM:SS+00:00`. If it is missing, not a string, or unparseable, omit `resetAt` and keep the meter. Never synthesize a monthly reset.
  5. `plan` uses `normalize_plan(plan_code)`:
     - The tier map is `lite→Lite`, `standard→Standard`, `pro→Pro`, `max→Max`, matched case-insensitively on the part before the first `:`.
     - The suffix map is `year→Annual`, `month→Monthly`. The output is `"<Tier> · <Period>"`.
     - A bare known tier gives `"<Tier>"`.
     - An unknown tier, or a known tier with an unknown suffix, gives the raw code: stripped, non-printable characters removed, truncated to 64 characters.
     - Empty, missing, or non-string gives `None`.
  6. Do not emit `auto_renew`, `claw_enabled`, absolute credit counts, or any extra field.
- **Acceptance.** Table-driven unit tests:
  1. **Plan.**
     - `lite`→`Lite`, `lite:year`→`Lite · Annual`, `standard:year`→`Standard · Annual`, `pro:month`→`Pro · Monthly`, `MAX`→`Max`.
     - `ultra:quarter`→`ultra:quarter`, `lite:weird`→`lite:weird`, and a 100-character code → its first 64 characters.
     - `""`, `None` and `123` → `None`.
  2. **Percent.**
     - total 4.1e9 with remaining 2.7e9 gives 66.
     - remaining 0 gives 0, and remaining = total gives 100.
     - remaining > total is clamped to 100, and a negative remaining is clamped to 0.
     - remaining absent with used = 1.4e9 gives 66.
     - Rounding cases: total 1000 with remaining 5 (0.5%) → `round(0.5)` = 0, and remaining 995 → 100 (99.5 rounds to 100). Both match the StepFun `round` behavior.
  3. **Period.**
     - The monthly fixture (`2026-11-11 21:05:27` → `2026-12-11 23:59:59`) gives `resetAt` `2026-12-11T23:59:59+00:00`.
     - The annual fixture (`2026-11-12 12:30:18` → `2027-11-12 23:59:59`) gives `resetAt` `2027-11-12T23:59:59+00:00`. No other reset value appears anywhere in the payload.
     - A malformed `end_at` such as `2026/12/11` gives a meter with no `resetAt`, and top-level `resetAt` null.
  4. **Failure.** `total_credits` 0, `-1` or `true`, a missing `quota`, and a `quota` that is a list each give `upstream_error`, and the CLI's cold-cache `error_payload` has no `meters` key.
  5. **Compatibility.** `remainingPercent` and `resetAt` copy the meter, `breakdown` equals `meters`, and `secondaryRemainingPercent` is absent.

### T3 — CLI wiring and auth commands

- **Task.** In `collector/ai-usage`:
  1. Import `MiMoProvider` and add `"mimo": MiMoProvider` to `PROVIDERS`.
  2. Add `--region` with `choices=["sgp", "cn", "ams"]` and default `sgp` to both the `status` and `auth` subparsers. The help text says it is used by `mimo` only.
  3. `build_provider()` passes `region=args.region` for `mimo`. Thread `region` through without changing other providers' construction.
  4. `cmd_auth` accepts `stepfun` (unchanged branch) and `mimo`. For `mimo`:
     - `set` reads the key from `getpass` on a TTY, else one stdin line, and validates the shape. A malformed key prints `invalid` to stdout, writes nothing, and exits 1, without echoing the value.
     - `set` then stores the key with `secret_set("mimo", "token-plan-key", key)` and verifies it with one `MiMoProvider(region).fetch_usage()`. It prints `working` on success, `auth_failed` on `auth_unavailable`, and `unavailable` on anything else.
     - `status` prints `missing` when no key is stored. Otherwise it does the same verify as `set` and prints the same words.
     - `clear` calls `secret_delete("mimo", "token-plan-key")` and prints `cleared`.
     - The error text for an unsupported provider becomes `Only ai-usage auth stepfun|mimo … is supported`.
- **Acceptance.** Subprocess tests run `collector/ai-usage` with a stub `secret_store` (through a test-only module path, or `HORIZON_KWALLET_NAME` with a fake D-Bus-free shim; use whichever is cleaner and document the choice), `MIMO_API_BASE` and `XDG_CACHE_HOME` set to a temporary directory:
  1. `status mimo --json --no-cache` gives an `ok` payload. `--region cn` reaches the fake server with the same path, and the region appears in the 401 message.
  2. `status mimo --json --region us` exits 2 through argparse and makes no request.
  3. `auth mimo set` with the fixture key on stdin prints `working`. With a 401 server it prints `auth_failed`. With a 500 server it prints `unavailable`. With `not-a-key` on stdin it prints `invalid` and stores nothing.
  4. `auth mimo status` prints `missing` when the store is empty. `auth mimo clear` prints `cleared`.
  5. The existing `auth stepfun …` tests still pass unchanged.
  6. A warm cache in `XDG_CACHE_HOME` plus a 500 server gives `status=stale` with the cached `Credits` meter.

### T4 — Key-source and environment isolation

- **Task.** Prove that the key comes only from KWallet.
- **Acceptance.**
  1. With `XIAOMI_API_KEY=tp-env-should-not-be-used` and `MIMO_API_KEY=tp-env-should-not-be-used` set, and the store empty, `status mimo` gives `auth_unavailable` and makes zero requests.
  2. With both env variables set and a different fixture key in the store, the fake server receives only the stored key.
  3. The test suite removes `XIAOMI_API_KEY` and `MIMO_API_KEY` from `os.environ`, or overrides them, at setup. No test reads the real values. Show this with `grep -n "XIAOMI_API_KEY\|MIMO_API_KEY" tests/`: they may be referenced only to delete or override them.
  4. `git grep -nE 'bashrc|\.profile|mimocode|XIAOMI_API_KEY|MIMO_API_KEY' collector/` has no hits in code. A comment that states the prohibition is allowed.
  5. A test that patches `builtins.open` and `pathlib.Path.open`/`read_text` records every path opened during a `fetch_usage()` run, and none is under `~/.bashrc`, a shell profile, or `mimocode`.

### T5 — Settings helper and install

- **Task.**
  1. Create `collector/mimo_auth_helper.py <status|clipboard|stdin|clear> <region>`, modeled on `stepfun_auth_helper.py`:
     - It uses the same clipboard read and clear approach.
     - It validates the key shape, and the region against `sgp|cn|ams`.
     - It stores the key with `secret_store`, then verifies with `MiMoProvider(region)`.
     - It prints one fixed word: `working`, `auth_failed`, `unavailable`, `missing`, `empty`, `invalid`, `cleared` or `store_error`.
  2. `scripts/install.sh` installs `providers/mimo.py` and `mimo_auth_helper.py` alongside the existing explicit list. Nothing else in the installer changes.
- **Acceptance.**
  1. Unit tests in the style of `tests/test_stepfun_auth_helper.py` cover:
     - an empty clipboard → `empty`;
     - a non-`tp-` value → `invalid`, with nothing stored;
     - a valid value with a 200 server → `working`, and the clipboard is cleared;
     - a 401 → `auth_failed`;
     - a 500 or network failure → `unavailable`;
     - an empty store with `status` → `missing`;
     - a store failure → `store_error`;
     - `clear` → `cleared`.
  2. The helper's argv in every test contains no key text.
  3. `scripts/install.sh` run into a temporary `XDG_DATA_HOME`, or a diff review, shows both files installed. `stepfun_auth_helper.py` has no diff.

### T6 — Plasmoid: config, settings and manual-only refresh

- **Task.**
  1. `plasmoid/contents/config/main.xml`: add `enableMimo` (Bool, default `false`) and `mimoRegion` (String, default `sgp`).
  2. `configGeneral.qml`:
     - Add a `Xiaomi MiMo` provider checkbox and a region `ComboBox` with `sgp`, `cn` and `ams`.
     - Add a MiMo credential block with Save key (clipboard), Check status and Clear. It calls `mimo_auth_helper.py <action> <region>` through the same `exec` pattern as StepFun, and maps the fixed words to messages.
     - The instructions tell the user to copy the `tp-` key from the Xiaomi MiMo Token Plan console. The key is never stored in Plasma config.
     - The StepFun block is unchanged.
  3. `MeterIntake.js`: add a pure `refreshIds(enabledIds, manual)` that returns `enabledIds` without `"mimo"` when `manual` is false, and unchanged when it is true. Optionally add a `MANUAL_ONLY_PROVIDERS = ["mimo"]` constant. Extend `collectorCommandForBin(binPath, providerId, region)` to append `--region '<region>'`, shell-quoted, for `mimo` only, after validating it against `sgp|cn|ams`, with a fallback to `sgp`.
  4. `main.qml`:
     - Add `"mimo"` to `allProviderIds`, `enabledProviderIds()` (when `enableMimo` is set) and `providerEnabled()`.
     - Change `refreshUsage()` to `refreshUsage(manual)`, which uses `MeterIntake.refreshIds(ids, manual === true)`.
     - The automatic callers keep calling `refreshUsage()` or pass `false`: `refreshTimer.onTriggered`, `Component.onCompleted`, `onExpandedChanged`, and `onConfigChanged()`. Add `onEnableMimoChanged` and `onMimoRegionChanged` handlers that call `onConfigChanged()`, so a MiMo row appears or is removed without fetching.
     - The manual callers pass `true`: the Refresh button `onClicked`, `Keys.onReturnPressed`, `Keys.onEnterPressed`, and the F5 `Shortcut.onActivated`.
     - A MiMo row in the `idle` state shows the label `Press Refresh to check` (or similar). The existing compact and tooltip code already skips `idle`.
     - Update the empty-providers text to mention Xiaomi MiMo.
- **Acceptance.**
  1. In `tests/test_meter_intake.qml` (or a new QML test):
     - `refreshIds(["codex","cursor","stepfun","claude","mimo"], false)` gives the four ids without `mimo`, and with `true` gives all five;
     - with `mimo` disabled, both calls give the same list;
     - `collectorCommandForBin(bin, "mimo", "cn")` ends with `status 'mimo' --json --region 'cn'`, or the existing quoting form;
     - an invalid region falls back to `sgp`;
     - the other providers' commands are byte-identical to the baseline.
  2. In `tests/test_refresh_keys.qml` (extended): the click, Space, Return, Enter and F5 activations each call the refresh function exactly once with `manual === true`, and not at all when disabled.
  3. A diff review of `main.qml` shows:
     - every `refreshUsage(` call site is classified: the timer, completed, expanded and config paths pass no argument or `false`, and the button, keys and F5 pass `true`;
     - no other path executes the collector for `mimo`.
  4. `qmllint6` on the changed QML files shows no new warnings compared with the baseline count.
  5. **Runtime check** on the real Plasma desktop after `scripts/install.sh`:
     - with MiMo enabled, the widget starts and the popup opens without a MiMo fetch, as observed through `ps` or a temporary wrapper log that records argv only;
     - pressing Refresh fetches MiMo once;
     - changing the region in settings does not fetch.

### T7 — Secret audit

- **Acceptance.**
  1. With the fixture key `tp-fake-fixture-key-0001`, none of these contains the full key or its first 12 characters:
     - the subprocess stdout and stderr;
     - the `--json` payload;
     - every `ProviderError` message;
     - the cache file after success;
     - the helper output.
  2. The QML-built collector command and the helper argv contain no key.
  3. The `docs/security.md` secret-check procedure passes. Add `git grep -nE 'tp-[A-Za-z0-9]{16,}'`, and require that it finds no real-looking key (only fixtures with `fake` in them).
  4. `git diff 220563f --stat` shows no new file that stores MiMo credentials.

### T8 — Writer docs (after T1–T7)

- **Task.**
  - **`docs/providers/mimo.md` (new):**
    - the official endpoint and its sources;
    - the region configuration and the no-probe rule;
    - the KWallet entry `Horizon` / `mimo/token-plan-key`;
    - the auth CLI and helper status words;
    - the meter mapping, the plan normalization table and the annual-period note;
    - the failure table;
    - the manual-refresh rule, quoting Xiaomi's restriction;
    - the cache file;
    - the exclusions (console, cookies, env, `.bashrc`, MiMo-Code).
  - **`docs/provider-contract.md`:**
    - the registry block and the registered-providers list;
    - the `--region` note;
    - MiMo in the "StepFun uses `ai-usage auth …`" sentence.
  - **`docs/security.md`:**
    - a MiMo section mirroring StepFun's;
    - the never-commit list gains MiMo key material;
    - the `usage-mimo.json` cache inspection line;
    - the env/bashrc/MiMo-Code prohibition.
  - **`README.md`:**
    - a `Supported providers` row `Xiaomi MiMo Token Plan | User-supplied tp- key stored only in KWallet; manual refresh only`;
    - a provider-doc link.

    Do not touch the version line.
  - **`docs/research/xiaomi-mimo-coding-plan.md`:** no change beyond the existing authorization status line.
- **Acceptance.** A diff review shows each statement matches `PHASES.md` Phase 12 and the code. The research note's `[V]/[O]/[T]/[A]` sections show no diff after the status line.

### T9 — Regression and live check

- **Acceptance.**
  1. `python3 -m unittest discover -s tests` passes with more than 61 tests.
  2. All QML suites pass, and their counts are at or above the baseline.
  3. After `scripts/install.sh`, `~/.local/bin/ai-usage status <id> --json` for `codex`, `cursor`, `stepfun` and `claude` each match their accepted behavior.
  4. **Live MiMo check: only if the owner has stored a key in KWallet through `ai-usage auth mimo set`.** Run one `~/.local/bin/ai-usage status mimo --json --region <configured>`. Record only:
     - the status;
     - the meter label;
     - `remainingPercent` rounded to the nearest 10;
     - whether `resetAt` is present and has a `+00:00` offset;
     - the plan label.

     Do not record the key, an email, a user id or raw credit counts. If no key is configured, record `live check skipped: no KWallet key`.

## Acceptance Criteria (summary; PHASES.md is authoritative)

| # | Criterion | Evidence |
|---|---|---|
| 1 | One `Credits` meter, percent formula, `+00:00` `resetAt`, `project_ok` projections | T2, T3.1 |
| 2 | Plan labels mapped; unknown codes preserved; null when missing | T2.1 |
| 3 | Monthly and annual period ends; no synthesized reset | T2.3 |
| 4 | KWallet-only key; env, bashrc and MiMo-Code never used | T1.4, T4 |
| 5 | Configured region only; 401 after one request; no probing | T1, T3.1–T3.2 |
| 6 | Failure states: `upstream_error` / `auth_unavailable` / `stale`; no fake meter | T1.3, T2.4, T3.6 |
| 7 | Manual-only MiMo refresh; other providers unchanged | T6 |
| 8 | Secret audit | T7 |
| 9 | Settings page and helper | T5, T6.5 |
| 10 | No regression | T9.1–T9.3 |
| 11 | Sanitized live check, or a recorded skip | T9.4 |
| 12 | Scope fence: `git diff 220563f --stat` touches only allowed paths; `VERSION`, `plasmoid/metadata.json`, `decisions/`, `docs/handoffs/`, `docs/usage-schema.md`, the other provider modules and `stepfun_auth_helper.py` have no diff | Watcher command output |
| 13 | Deferred Work recorded | below |
| 14 | Watcher PASS, then stop for owner acceptance | `reports/stage-4-phase-12-watcher-<n>.md` |

## Exclusions

See `PHASES.md` Phase 12 Explicit Exclusions. In brief:

- no console, cookie, SSO or login path;
- no region probing or other hosts;
- no inference or Finance calls;
- no key from env, `.bashrc`, plaintext files, MiMo-Code or CLI flags;
- no automatic MiMo polling and no polling framework;
- no team seats, multiple accounts or model pools;
- no new ADR, ADR edits or schema change;
- no behavior change for other providers;
- no `VERSION`, tag, release or push to `main`;
- no `docs/handoffs/phase-12.md` before acceptance.

## Deferred Work

Record out-of-scope discoveries here. Candidates already known at authorization:

- **Unattended or periodic MiMo polling.** This needs explicit Xiaomi confirmation that a background quota read is permitted, or an owner decision in a later phase.
- **Showing the MiMo XDG cache at widget startup without spawning the collector.** For example, a QML-side read of `usage-mimo.json`.
- **A `· Monthly` label for bare tier codes,** if Xiaomi documents that a bare code always means monthly.
- **Team-edition seats and multiple keys or regions.**

## Evidence

### Baseline (Coder re-recorded at `220563f`, 2026-11-27)

```text
$ python3 -m unittest discover -s tests
Ran 61 tests in 8.062s -> OK

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input <file>:
  tests/test_compact_summary.qml:    14 passed, 0 failed
  tests/test_meter_intake.qml:        6 passed, 0 failed
  tests/test_refresh_keys.qml:        7 passed, 0 failed
  tests/test_command_and_times.qml:   6 passed, 0 failed

$ qmllint6:
  plasmoid/contents/ui/main.qml: 3 warnings
  plasmoid/contents/ui/configGeneral.qml: 24 warnings
  plasmoid/contents/config/config.qml: 1 warnings
```

### T1–T9 (T8 Writer docs pending; independent Watcher pending)

#### Python unit tests (T1, T2, T3, T4, T5, T7, T9.1)

Subprocess CLI tests use a temporary D-Bus-free `secret_store.py` shim on `PYTHONPATH` so no live KWallet is touched.

```text
$ python3 -m unittest discover -s tests
Ran 78 tests in 17.933s

OK
```

#### QML tests & `qmllint6` (T6, T9.2)

```text
$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_compact_summary.qml
Totals: 14 passed, 0 failed, 0 skipped, 0 blacklisted, 3ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_meter_intake.qml
Totals: 6 passed, 0 failed, 0 skipped, 0 blacklisted, 2ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_refresh_keys.qml
Totals: 8 passed, 0 failed, 0 skipped, 0 blacklisted, 7ms

$ QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_command_and_times.qml
Totals: 8 passed, 0 failed, 0 skipped, 0 blacklisted, 3ms

$ qmllint6:
  plasmoid/contents/ui/main.qml: 3 warnings (baseline: 3)
  plasmoid/contents/ui/configGeneral.qml: 24 warnings (baseline: 24)
  plasmoid/contents/config/config.qml: 1 warnings (baseline: 1)
```

`main.qml` `refreshUsage` call-site audit (T6.3):

```text
$ grep -n 'refreshUsage' plasmoid/contents/ui/main.qml
386:    function refreshUsage(manual) {
400:        refreshUsage(false)
406:            refreshUsage(false)
429:        onTriggered: root.refreshUsage(false)
442:        refreshUsage(false)
537:            onActivated: root.refreshUsage(true)
573:                    onClicked: root.refreshUsage(true)
577:                            root.refreshUsage(true)
583:                            root.refreshUsage(true)
```

#### Environment isolation, secret audit & scope fence (T4, T7)

```text
$ git grep -nE 'bashrc|\.profile|mimocode|XIAOMI_API_KEY|MIMO_API_KEY' collector/
(0 hits)

$ grep -n "XIAOMI_API_KEY\|MIMO_API_KEY" tests/*.py
tests/test_mimo_auth_helper.py:28:        self._saved = {k: os.environ.pop(k, None) for k in ("XIAOMI_API_KEY", "MIMO_API_KEY")}
tests/test_mimo_provider.py:151:        for var in ("XIAOMI_API_KEY", "MIMO_API_KEY", "MIMO_API_BASE"):
tests/test_mimo_provider.py:342:        os.environ["XIAOMI_API_KEY"] = "tp-env-should-not-be-used"
tests/test_mimo_provider.py:343:        os.environ["MIMO_API_KEY"] = "tp-env-should-not-be-used"
tests/test_mimo_provider.py:407:        env.pop("XIAOMI_API_KEY", None)
tests/test_mimo_provider.py:408:        env.pop("MIMO_API_KEY", None)

$ git grep -nE 'tp-[A-Za-z0-9]{16,}'
(0 hits)

$ git diff 220563f -- decisions/ docs/handoffs/ VERSION plasmoid/metadata.json docs/usage-schema.md collector/stepfun_auth_helper.py collector/providers/codex.py collector/providers/cursor.py collector/providers/stepfun.py collector/providers/claude.py | wc -l
0

$ bash -n scripts/install.sh
(exit 0)
```

#### Install, settings runtime check & live provider check (T5, T6.5, T9.3, T9.4)

```text
$ ./scripts/install.sh
Upgrading package from file: /home/naorw/.t3/worktrees/horizon/phase-12-xiaomi-mimo-token-plan/plasmoid
Successfully upgraded /home/naorw/.local/share/plasma/plasmoids/com.radilabs.horizon/
Horizon installed.
  collector: /home/naorw/.local/share/horizon/collector
  launcher:  /home/naorw/.local/bin/ai-usage
  plasmoid:  com.radilabs.horizon

Installed MiMo files:
  ~/.local/share/horizon/collector/mimo_auth_helper.py
  ~/.local/share/horizon/collector/providers/mimo.py

$ ~/.local/bin/ai-usage status <id> --json --no-cache (sanitized):
{"provider": "codex", "rc": 0, "status": "ok", "plan": "ChatGPT Plus", "meterLabels": ["5-hour limit", "Weekly limit"]}
{"provider": "cursor", "rc": 0, "status": "ok", "plan": "Pro", "meterLabels": ["Cursor Models", "Other Models"]}
{"provider": "stepfun", "rc": 0, "status": "ok", "plan": "Plus", "meterLabels": ["5-Hour Usage", "Weekly Usage"]}
{"provider": "claude", "rc": 0, "status": "ok", "plan": "Pro", "meterLabels": ["Current session", "Current week (all models)"]}

MiMo live check: no KWallet key; live check skipped

Installed configGeneral.qml runtime check (qml6 on WAYLAND_DISPLAY=wayland-1):
  STEPFUN_STATUS=Configured · working
  MIMO_STATUS=Not configured
  MIMO_BUSY=false
  MIMO_ENABLE_DEFAULT=false
  MIMO_REGION_DEFAULT=sgp
  MIMO_REGION_AFTER_CHANGE=cn
  MIMO_BUSY_AFTER_REGION_CHANGE=false
```
