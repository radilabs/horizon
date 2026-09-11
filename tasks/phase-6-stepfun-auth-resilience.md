# Phase 6 Tasks — StepFun Auth Resilience

Phase contract: `PHASES.md` → Stage 1 / **Phase 6 — StepFun Auth Resilience**.

Phase 6 is authorized only after the Stage 1 / Phase 6 contract and execution state are merged.

## Goal

Determine whether Horizon can safely recover from StepFun Oasis token expiry using only credential material it already owns, and implement that recovery if it is proven safe and supported.

If automatic renewal is not safely supportable without username/password, browser import, or login automation, prove that limitation, preserve manual replacement, and improve the expiry path honestly.

This phase is about resilience of the existing StepFun provider. It does not add providers or create a general authentication framework.

## Read First

- `PROJECT.md`
- Stage 1 / Phase 6 in `PHASES.md`
- `docs/handoffs/phase-5.md`
- `docs/providers/stepfun.md`
- `docs/security.md`
- `decisions/0009-os-credential-store.md`
- current `collector/providers/stepfun.py`
- current StepFun auth helper / KWallet path

## P6-T0 — Baseline

Verify before changing code:

- Codex live usage
- Cursor live usage
- StepFun behavior with a currently valid token
- current StepFun expiry/auth-unavailable behavior
- KWallet storage path
- repository secret audit

Record exact commands/results without secret material.

## P6-T1 — Characterize Existing Oasis Credential

Using only the token already stored in KWallet and sanitized observations:

- determine token shape (including whether it contains access/refresh material)
- identify expiry claims/timestamps if present
- identify `device_id` and `app_id` handling
- determine which token half is used for current dashboard requests
- determine whether a refresh credential is actually present and distinct

Do not print or persist token/JWT contents.

Update `docs/providers/stepfun.md` only with durable sanitized facts.

## P6-T2 — Discover Current Refresh Mechanism

Investigate the current StepFun web/Oasis refresh behavior.

May use:

- official/public StepFun behavior where available
- sanitized network inspection initiated by the owner
- existing open-source implementations as references
- controlled requests using the existing KWallet token

Determine:

- refresh endpoint
- required headers/cookies
- required `oasis-appid` / `oasis-webid`
- whether refresh requires only the existing refresh token
- returned token shape
- rotation semantics
- failure semantics

Do not implement username/password login.
Do not import browser cookies.
Do not add browser-profile dependencies.

If safe refresh cannot be proven, record that result and proceed to the manual-expiry hardening path.

## P6-T3 — Decide Supported Recovery Path

Choose exactly one based on evidence:

### Path A — Automatic refresh supported

Only if a valid expired/near-expired Oasis credential can be renewed using the existing stored token material alone.

Requirements:

- StepFun-local implementation only
- no general Oasis framework
- no username/password
- no browser import
- no token in argv/logs/config/cache/docs
- new token must be validated before replacing the KWallet entry
- KWallet update must not destroy the last known credential before successful validation
- bounded retry only; no refresh loop

### Path B — Automatic refresh not safely supported

Keep manual Replace Token as the supported mechanism.

Improve only what is needed so expiry is clearly identified and the user is directed to Replace Token.

Do not build an unsupported workaround merely to make the phase look successful.

If Path A introduces a durable architectural/security decision, add an ADR. Do not create an ADR just to narrate implementation.

## P6-T4 — Implement Bounded Auth Recovery

If Path A:

- on StepFun auth rejection attributable to expiry, attempt one refresh
- validate the refreshed credential with a StepFun request
- atomically replace the KWallet value only after validation
- retry the original usage fetch once
- if refresh fails, return `auth_unavailable`
- never retry indefinitely

If Path B:

- preserve current manual token replacement flow
- ensure expired/rejected token maps cleanly to `auth_unavailable`
- ensure settings/CLI guidance clearly points to Replace/Set Token

No changes to Codex/Cursor auth behavior.

## P6-T5 — Security Validation

Test the complete path without exposing secrets.

Inspect:

- repo/diff
- stdout/stderr
- logs
- Plasma config
- usage cache
- shell/process arguments
- temporary files
- KWallet lifecycle

Run the existing secret audit.

For Path A, verify old/new token material exists only transiently in process memory and in KWallet as appropriate.

## P6-T6 — Failure and Isolation Tests

Verify:

- valid StepFun credential
- expired/rejected StepFun credential
- refresh success if Path A
- refresh failure if Path A
- malformed refresh response if Path A
- upstream StepFun failure
- stale cache behavior
- Codex unaffected
- Cursor unaffected
- no overlapping refresh/recovery loop

## P6-T7 — Documentation

Update durable docs with the proven current mechanism and limitations.

Document:

- whether automatic refresh is supported
- exact sanitized refresh/auth flow if supported
- token rotation behavior if supported
- manual replacement behavior if not
- upstream fragility
- security boundary

Do not include raw tokens, JWT payloads, cookies, or credentials.

## P6-T8 — Independent Verification and Handoff

Mandatory Watcher verification against the Phase 6 contract.

After Watcher PASS, present evidence to the project owners for acceptance.

Create `docs/handoffs/phase-6.md` only after owner acceptance.

Handoff must state which path was proven:

- `AUTOMATIC REFRESH SUPPORTED`, or
- `MANUAL REPLACEMENT REMAINS REQUIRED`

Record acceptance criteria results, security audit, provider isolation, limitations, and deferred work.

Then STOP.

Do not begin Groq discovery or any other provider/capability phase.

## Deferred Work

Record, but do not implement:

- StepFun username/password login
- browser/session import
- generic Oasis framework
- additional providers including Groq
- account/subscription management
