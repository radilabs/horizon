# Phase 7 Handoff — Provider Information Contract

Date: 2026-10-09  
Environment: openSUSE, Plasma 6  
Release: remains **0.1.1** (`v0.1.1`). This acceptance is not a version bump or tag.

**PHASE 7 HANDOFF: ACCEPTED**

## Owner acceptance

The project owner explicitly accepted Stage 2 / Phase 7 on 2026-10-09 after Watcher PASS.

Acceptance is recorded here. This file is the accepted-state snapshot. Watcher PASS alone was not acceptance.

## Deliverables

* Canonical ordered `meters` on successful and stale usage payloads (`collector/providers/contract.py`, ADR-0012)
* Codex, Cursor, StepFun, and Claude normalize through `project_ok`
* Compatibility copies remain: `remainingPercent` and `resetAt` from the first meter, `secondaryRemainingPercent` from the second when it exists, `breakdown` as a copy of `meters`
* Cache allowlist includes `meters`. A stale read of a pre-Phase-7 cache rebuilds `meters` and does not invent `breakdown`
* `scripts/install.sh` installs `collector/providers/contract.py`
* Deterministic tests: `tests/test_usage_contract.py`
* Durable docs: `docs/usage-schema.md`, `docs/provider-contract.md`, `docs/cache.md`, provider notes, ADR-0012
* Independent Watcher report (runtime, gitignored): `reports/stage-2-phase-7-watcher-1.md` (PASS)
* Plasma QML was not changed

## Acceptance criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Sanitized inventory covers all four providers, including Claude's session and weekly windows and independent resets | PASS |
| 2 | The contract expresses multi-meter output, identity, unknown data, per-meter reset, and success, auth, upstream, and stale states without provider-specific QML | PASS |
| 3 | Meter values are percent remaining; missing windows and error quotas are not fabricated | PASS |
| 4 | CLI, cache, and QML compatibility is explicit; four providers still succeed; widget sources are unchanged | PASS |
| 5 | Deterministic contract tests pass, including multi-window and error/stale cases | PASS |
| 6 | No credential material in committed artifacts, logs, or test fixtures | PASS |
| 7 | Out-of-scope work is deferred | PASS |
| 8 | Watcher PASS, then explicit owner acceptance | PASS |

## Tests / owner evidence

Coder (2026-10-09, sanitized):

* `python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh` — 31 OK
* Live CLI, safe fields only: Codex `ok` ChatGPT Plus, `5-hour limit` 100 and `Weekly limit` 99; Cursor `ok` Pro, Cursor Models 77 and Other Models 0; StepFun `ok` Plus, 5-Hour Usage 99 and Weekly Usage 86; Claude `ok` Pro, Current session 95 and Current week (all models) 78
* Each live payload had `breakdown` equal to `meters`. Output had no secret markers
* `git diff 1bda0af -- plasmoid/` empty

Watcher attempt 1: **PASS**. Report: `reports/stage-2-phase-7-watcher-1.md`. No blocking findings. The Watcher re-ran the 31 tests and the four live CLI paths.

Architect review agreed with the meter contract; the recorded corrections are in the Phase 7 task file. Writer review corrected documentation contradictions before verification.

Owner: accepted Phase 7 on 2026-10-09.

## Contract

ADR-0012. `meters` is the list Phase 8 should render. Each meter has `label`, integer `remainingPercent` (percent **remaining**, 0–100), and optional `resetAt`. Percent-used upstream values are converted before emission. Claude `utilization` of `1.0` is 1% used and 99% remaining.

Codex labels come from `limit_window_seconds` (`5-hour limit`, `Weekly limit`, `{n}-day limit`, `{n}-hour limit`, otherwise `Usage limit`). They are not named Primary or Secondary. The one deliberate visible change is that new Codex payloads include `breakdown`, so the existing popup shows those labels and each window's own reset.

Cursor, StepFun, and Claude keep their existing labels and percents. Cursor may emit one pool when the other is absent. Claude keeps every present window, including windows after the second. `seven_day_breakdown`, disabled `spend`, and `limits[]` are not meters.

Failure payloads keep the existing `error_payload` keys and omit `meters`.

## Known limitations

* Current QML reads `breakdown` and the compatibility percents. It ignores `meters`
* When a breakdown row has no `resetAt`, current QML shows the top-level reset (`line.resetAt || obj.resetAt`)
* A stale pre-Phase-7 Codex cache is rebuilt into `meters` labeled `Usage limit` and does not gain `breakdown`, so that cached popup stays on the old unlabeled path until the next successful fetch
* Codex has no upstream display name; labels are derived from window length
* Tagged release remains 0.1.1

## Deferred work

```text
- Phase 8 Plasma UI refresh around meters
- Phase 8 must not fill a missing meter reset from the top-level resetAt
- Phase 9 compact UX and release polish
- Removing compatibility fields remainingPercent, resetAt, secondaryRemainingPercent, and breakdown
- Balances, spend, rate-limit policy objects, and multiple accounts
- Any other provider, including Groq
```

## Stop

Phase 7 accepted. Stage 2 stays open. Horizon release remains **0.1.1**.

**Do not begin Phase 8 or Phase 9** without an explicit new contract and `TASKS.md` authorization.
