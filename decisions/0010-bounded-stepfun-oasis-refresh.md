# ADR-0010 — Bounded StepFun Oasis refresh using stored KWallet material

## Status

Accepted (Phase 6)

## Context

ADR-0009 stores a user-supplied Oasis token in KWallet and forbids username/password login and browser import. Its original consequence was that token expiry required a manual paste and Horizon would not refresh or write back Oasis credentials.

Phase 6 investigated whether the **already stored** Oasis value (observed as an `access...refresh` JWT pair) is sufficient to renew an expired session against the current StepFun platform.

Live evidence (2026-09-11, `platform.stepfun.ai`, `oasis-appid` 20700): the stored pair was rejected by the usage endpoint (HTTP 401). The access JWT `exp` and refresh JWT `exp` were both in the past. A `POST` to `/passport/proto.api.passport.v1.PassportService/RefreshToken` with that stored pair (Cookie `Oasis-Token` + `Oasis-Webid`, headers `oasis-appid` / `oasis-webid` / `Oasis-Token`) returned HTTP 200 with new `accessToken.raw` and `refreshToken.raw` and no username/password or browser cookies.

Wrong `oasis-appid` (10300 on `.ai`) returned HTTP 400 `oasis header is invalid`. CodexBar’s `.com` + `10300` host/app pairing is not used for this account.

## Decision

1. Horizon **may** attempt **at most one** Oasis `RefreshToken` call per usage fetch when StepFun returns `auth_unavailable`.
2. Refresh uses only the KWallet `stepfun/oasis-token` value (and derived `device_id` / `app_id`). No login, no browser import, no generic Oasis framework.
3. The new pair is **validated** with `QueryStepPlanRateLimit` **before** `secret_set`.
4. If refresh or validation fails, the previous KWallet value is left unchanged and the provider returns `auth_unavailable` with manual Replace/Set Token guidance.
5. Codex and Cursor authentication are unchanged.
6. ADR-0009 remains in force except the sentence that Horizon does not implement StepFun refresh write-back; that consequence is superseded by this record.

## Consequences

* Expired Oasis access tokens can recover without a paste when the stored pair is still accepted by `RefreshToken`.
* Refresh is unofficial and can stop working if StepFun rotates protocol, host, or app id.
* A refresh JWT that `RefreshToken` rejects still requires manual token replacement.
* Concurrent StepFun fetches share a process lock so recovery is not an unbounded loop.
