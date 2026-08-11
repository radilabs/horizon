# StepFun provider notes (Phase 4)

## Why Horizon stores a token

StepFun has **no** local desktop credential store Horizon can reuse.

Phase 4 stores a **user-supplied existing Oasis token** in the OS credential store (KWallet). Horizon does **not** implement username/password login and does **not** store passwords. See ADR-0009.

Browser cookies (e.g. Zen) are **not** the primary credential source and must not be copied into Horizon as an implementation path. Users paste an existing Oasis token via the auth CLI.

## Credential CLI

```bash
ai-usage auth stepfun set      # secure prompt (no --token); verifies live
ai-usage auth stepfun status   # working | auth_failed | missing
ai-usage auth stepfun clear
```

Widget settings uses the same meanings: **Configured · working** only after StepFun accepts the token (not merely that KWallet has an entry).

Storage: KWallet wallet `kdewallet`, folder `Horizon`, entry `stepfun/oasis-token`.

## Token form and Oasis-Webid

Observed Oasis token shapes:

* bare JWT, or
* `access...refresh` pair joined by literal `...`

`Oasis-Webid` must match the token’s `device_id` claim. Horizon derives it by base64url-decoding JWT payloads **in memory** and reading `device_id`, preferring the **refresh** half when a pair is present (same approach as the CodexBar reference).

`oasis-appid` is derived from the refresh JWT `app_id` claim when present (observed **20700** for current `platform.stepfun.ai` web sessions). Fallback: `20700`.

## Endpoints (observed)

Base URL used by Horizon:

```text
https://platform.stepfun.ai
```

(CodexBar’s older `platform.stepfun.com` + app id `10300` does **not** accept current `.ai` web tokens; wrong host/app id yields signature/embezzled errors.)

Usage:

```http
POST /api/step.openapi.devcenter.Dashboard/QueryStepPlanRateLimit HTTP/1.1
Host: platform.stepfun.ai
Content-Type: application/json
oasis-appid: <from refresh JWT app_id>
oasis-platform: web
oasis-webid: <device_id>
Cookie: Oasis-Token=<secret>; Oasis-Webid=<device_id>
Origin: https://platform.stepfun.ai
Referer: https://platform.stepfun.ai/

{}
```

Plan name:

```text
POST /api/step.openapi.devcenter.Dashboard/GetStepPlanStatus
```

Uses `subscription.name` when available (observed: **Plus**); usage still succeeds if plan lookup fails.

## Account shape observed (Phase 4)

**Rolling-window / Coding Plan** (`plan_family: 1`):

* Live `five_hour_usage_reset_time` / `weekly_usage_reset_time` (positive epochs)
* `five_hour_usage_left_rate` / `weekly_usage_left_rate` as remaining fractions
* Not a credit plan (do not treat zero windows as exhausted on credit-shaped payloads)

## Usage shapes

Classify by **payload shape** (not `plan_family` alone):

### Rolling-window (Coding Plan)

Live when `five_hour_usage_reset_time` or `weekly_usage_reset_time` is a positive epoch.

Meters (remaining % = `round(left_rate × 100)`):

* **5-Hour Usage** ← `five_hour_usage_left_rate` + `five_hour_usage_reset_time`
* **Weekly Usage** ← `weekly_usage_left_rate` + `weekly_usage_reset_time`

Zero window rates with reset `"0"` on a credit plan mean “no window”, **not** exhausted.

### Credit (Token Plan)

No live window resets, plus `plan_credit_rate_limit` credit material.

Meters:

* Prefer weighted **Credits** from `credit_buckets` residual/total when all buckets are valid
* Else `subscription_credit_left_rate` (or `topup_credit_left_rate` if no subscription rate)
* Do **not** add independent credit rates together
* Do **not** show fake 5-Hour/Weekly 0% bars

## Sanitized rate-limit example (this account)

```json
{
  "status": 1,
  "plan_family": 1,
  "five_hour_usage_left_rate": 1,
  "weekly_usage_left_rate": 0.9994,
  "five_hour_usage_reset_time": "1786399200",
  "weekly_usage_reset_time": "1786564800"
}
```

## Normalized mapping

Uses existing schema + `breakdown[]` (ADR-0008). No shared-schema redesign.

| Field | Meaning for StepFun |
|-------|---------------------|
| `remainingPercent` | First breakdown meter (5-Hour or Credits) |
| `secondaryRemainingPercent` | Second meter when present (Weekly) |
| `breakdown[].label` | `5-Hour Usage` / `Weekly Usage` or credit labels |
| `breakdown[].remainingPercent` | Remaining % |
| `breakdown[].resetAt` | Per-meter reset when known |
| `plan` | `GetStepPlanStatus.subscription.name` or `"Step Plan"` |

## Cache

`~/.cache/horizon/usage-stepfun.json` — normalized fields only. Never Oasis token / WebID / raw upstream.

## Security

* Token only in KWallet
* No browser cookie extraction as the primary path
* No token in CLI args, cache, docs, or evidence
* Reference: CodexBar StepFun docs (login automation **not** copied; host/app id updated for current web)

## Upstream fragility

Unofficial Dashboard endpoints, host (`.ai` vs `.com`), and JWT `app_id` / `device_id` association can change. Expired or wrong-app tokens fail auth; user must paste a fresh Oasis token.
