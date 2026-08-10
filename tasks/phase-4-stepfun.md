# Phase 4 Tasks — StepFun Step Plan

Phase contract: `PHASES.md` → **Phase 4 — StepFun Step Plan**

Phase 3 handoff must be PASS before this file is executed.

The purpose of this phase is to add real StepFun Step Plan usage/credit information through the existing provider architecture.

StepFun is the first Horizon provider without a local provider-owned desktop credential store. Phase 4 may therefore introduce minimal secure OS credential storage where required.

Do not turn that requirement into a general account/settings framework.

---

# Execution Rules

1. Read `PROJECT.md`.
2. Read the Phase 4 contract in `PHASES.md`.
3. Read `docs/handoffs/phase-3.md`.
4. Read:

   * `docs/provider-contract.md`
   * `docs/usage-schema.md`
   * `docs/cache.md`
   * `docs/security.md`
   * `docs/providers/cursor.md`
5. Read relevant ADRs, especially credential and breakdown decisions.
6. Review the CodexBar StepFun implementation/documentation as a reference:

   * `https://github.com/steipete/CodexBar/blob/main/docs/stepfun.md`
7. Inspect current provider registry, cache, CLI, QML, and security boundaries.
8. Work through tasks in order.
9. Preserve working Codex and Cursor behavior.
10. Use the existing provider model wherever possible.
11. Do not implement StepFun username/password login.
12. Do not store StepFun username/password.
13. Do not implement general billing management.
14. Do not purchase/change subscriptions.
15. Do not add notifications.
16. Do not add settings UI.
17. Do not add periodic/background refresh.
18. Do not redesign Horizon around StepFun concepts.
19. Create shared abstractions only when StepFun requires them now.
20. Record out-of-scope discoveries under **Deferred Work**.
21. Every task requires deliverable, test, and evidence.
22. Phase completion requires the handoff validation task.
23. After successful handoff, STOP.

---

# Authentication Boundary

StepFun has no local desktop installation whose credential store Horizon can reuse.

For Phase 4, Horizon may securely store a **user-supplied existing Oasis token**.

This is the first Horizon-owned provider secret.

Rules:

* store the Oasis token only in the OS credential store
* on KDE/openSUSE, prefer KWallet / Secret Service integration supported by the system
* never store the token in Horizon config files
* never store it in the XDG usage cache
* never store it in environment files
* never print it
* never log it
* never pass it as a CLI argument
* never commit it
* never store StepFun username/password
* never implement StepFun login

The durable rule introduced by this phase is:

> Reuse provider-owned credentials when a suitable local source exists.
> If no provider-owned local credential source exists, Horizon may securely store a user-supplied credential in the OS credential store.

Record this as an ADR because future providers may depend on it.

---

# Oasis Mechanism

Known reference behavior from CodexBar:

StepFun Step Plan usage is authenticated with an **Oasis-Token**.

Usage endpoint:

```text
POST https://platform.stepfun.com/api/step.openapi.devcenter.Dashboard/QueryStepPlanRateLimit
```

Plan endpoint:

```text
POST https://platform.stepfun.com/api/step.openapi.devcenter.Dashboard/GetStepPlanStatus
```

Relevant auth material includes:

```text
Cookie: Oasis-Token=<secret>
Oasis-Webid: <device_id associated with token>
```

The `Oasis-Webid` must match the token's associated `device_id`.

CodexBar derives the device identifier from the JWT material in the Oasis token.

Treat CodexBar as a reference implementation only.

Do not copy its username/password login automation into Horizon.

---

# P4-T0 — Revalidate Phase 4 Security Boundary

## Objective

Establish the credential rules before handling a real Oasis token.

## Instructions

Review:

* `.gitignore`
* `docs/security.md`
* current secret-audit procedure
* cache whitelist
* CLI stdout/stderr behavior

Determine what protection is required for:

* Oasis token
* temporary test fixtures
* local credential-store metadata
* possible KWallet helper state

No secret value may enter the repository during discovery.

## Deliverable

Updated security documentation/rules if required.

## Test

Run:

```bash
git status
git diff
git diff --cached
```

Run repository secret audit.

Confirm no StepFun credential artifacts are tracked.

## Completion Evidence

Record:

* protections reviewed
* changes made
* secret audit result

Never record secret values.

## Status

* [x] Complete

---

# P4-T1 — Introduce Minimal OS Secret Store

## Objective

Provide Horizon with the smallest secure credential storage capability required by StepFun.

## Instructions

Determine the practical credential-store mechanism available on the target KDE/openSUSE system.

Prefer the native OS desktop secret store.

The abstraction must remain tiny.

Conceptual interface:

```text
secret_store.get(provider, name)
secret_store.set(provider, name, value)
secret_store.delete(provider, name)
```

Immediate Phase 4 use:

```text
provider = stepfun
name = oasis-token
```

Do not add:

* provider account objects
* arbitrary settings
* credential synchronization
* browser imports
* login automation
* encryption implemented by Horizon
* a generic secrets database
* configuration UI

The actual secret must be stored by the OS credential service.

Horizon may store non-secret identifiers necessary to find the entry.

## Deliverable

Minimal secret-store implementation usable by the collector.

Create an ADR documenting:

* why StepFun requires Horizon-owned secure secret storage
* provider-owned credentials remain preferred
* OS credential store is used rather than plaintext files
* StepFun stores token only, not username/password
* future providers may reuse the same minimal mechanism where justified

## Test

Using a disposable non-secret test value:

1. set entry
2. retrieve entry
3. delete entry
4. confirm retrieval reports missing
5. confirm value does not appear in:

   * repo
   * Horizon config
   * Horizon cache
   * stdout/stderr
6. confirm secret store survives a new collector process

## Completion Evidence

Record:

* backend selected
* API implemented
* storage location conceptually
* lifecycle test
* ADR

Never include stored values.

## Status

* [x] Complete

---

# P4-T2 — Add Safe StepFun Credential CLI

## Objective

Allow the user to configure the StepFun Oasis token without exposing it through command history or process arguments.

## Instructions

Add:

```bash
ai-usage auth stepfun set
ai-usage auth stepfun status
ai-usage auth stepfun clear
```

### `set`

Prompt interactively for the Oasis token.

Requirements:

* token must not be accepted through `--token`
* token must not appear in shell history
* token must not appear in process arguments
* suppress terminal echo where practical
* store directly in OS secret store
* success output contains no secret material

### `status`

Return only something equivalent to:

```text
configured
```

or:

```text
missing
```

Never output:

* token
* token prefix
* token length if unnecessary
* JWT contents
* device id unless needed diagnostically and proven non-sensitive

### `clear`

Delete the OS secret-store entry.

Do not implement login.

## Deliverable

Safe StepFun credential-management CLI.

## Test

1. set disposable token
2. status → configured
3. inspect process history/output
4. clear
5. status → missing
6. configure actual token
7. rerun secret audit

## Completion Evidence

Record command behavior and PASS/FAIL only.

## Status

* [x] Complete

---

# P4-T3 — Validate Oasis Token Structure and WebID Derivation

## Objective

Determine exactly how the supplied Oasis token must be used without leaking it.

## Instructions

Using the user-supplied token in memory only:

* determine token structure
* determine where `device_id` is encoded
* derive `Oasis-Webid`
* compare behavior with CodexBar reference implementation
* do not verify semantics merely by copying assumptions

JWT payload decoding for extraction is acceptable where required.

Do not:

* print decoded JWT payload
* persist decoded JWT material
* expose token claims in normal output
* modify the token
* refresh the token

If the token is an access/refresh pair, determine which portion carries the authoritative `device_id`.

## Deliverable

Document the sanitized mechanism in:

`docs/providers/stepfun.md`

Include:

* token form
* device-id derivation method
* required request headers
* security constraints

## Test

1. retrieve token from secret store
2. derive WebID
3. make authenticated request
4. verify valid auth
5. test deliberately incorrect WebID safely if useful
6. confirm no secret appears in output/logs

## Completion Evidence

Record:

* token form understood
* WebID derivation confirmed
* request authentication PASS/FAIL

No claims or token values.

## Status

* [x] Complete

---

# P4-T4 — Discover Real StepFun Usage Shape

## Objective

Inspect the live account response and determine whether this account is a rolling-window plan or credit plan.

## Instructions

Call:

```text
QueryStepPlanRateLimit
```

Inspect only the fields needed to understand quota semantics.

Known reference fields include:

```text
five_hour_usage_left_rate
weekly_usage_left_rate
five_hour_usage_reset_time
weekly_usage_reset_time
plan_family
plan_credit_rate_limit
```

Possible credit fields include:

```text
subscription_credit_left_rate
subscription_credit_reset_time
topup_credit_left_rate
credit_buckets
```

Important:

Do not treat zero 5-hour/weekly values as exhausted usage without checking whether the account is a credit-plan shape.

Determine plan type based primarily on actual payload semantics:

### Rolling-window shape

Real/resettable:

* 5-hour usage
* weekly usage

### Credit shape

No live rolling windows plus meaningful credit information.

Do not rely blindly on `plan_family`.

Document the actual account shape observed.

## Deliverable

Extend `docs/providers/stepfun.md` with:

* sanitized response structure
* actual plan shape
* available quota fields
* reset behavior
* limitations
* upstream fragility

## Test

1. real usage request succeeds
2. repeat request succeeds
3. values correspond to StepFun dashboard where observable
4. classify account shape
5. no credentials persisted/logged

## Completion Evidence

Record sanitized quota values and semantics only.

## Status

* [x] Complete

---

# P4-T5 — Discover StepFun Plan Name

## Objective

Retrieve the user-facing Step Plan name where available.

## Instructions

Investigate:

```text
POST /api/step.openapi.devcenter.Dashboard/GetStepPlanStatus
```

Expected useful material:

```text
subscription.name
```

Usage retrieval must not fail solely because plan-name retrieval fails.

## Deliverable

Document plan-name behavior in `docs/providers/stepfun.md`.

## Test

* successful plan lookup
* controlled plan-status failure while usage still succeeds

## Completion Evidence

Record plan label and fallback behavior.

## Status

* [x] Complete

---

# P4-T6 — Map StepFun Into Existing Usage Model

## Objective

Represent actual StepFun usage honestly through Horizon's existing normalized schema.

## Instructions

Use `breakdown[]`.

### Rolling-window plan

Preferred normalized meters:

```text
5-Hour Usage
Weekly Usage
```

Each contains:

* remaining percentage
* its own reset timestamp

Example concept:

```json
{
  "provider": "stepfun",
  "displayName": "StepFun",
  "plan": "Plus",
  "remainingPercent": 84,
  "resetAt": "...",
  "status": "ok",
  "breakdown": [
    {
      "label": "5-Hour Usage",
      "remainingPercent": 84,
      "resetAt": "..."
    },
    {
      "label": "Weekly Usage",
      "remainingPercent": 62,
      "resetAt": "..."
    }
  ]
}
```

Use StepFun's returned **remaining fraction** directly:

```text
remainingPercent = left_rate × 100
```

Do not invert twice.

### Credit-plan shape

If actual account data is credit-based:

Do not show fake:

```text
5-Hour Usage 0%
Weekly Usage 0%
```

Instead map the meaningful credit allowance into labeled `breakdown[]`.

Use actual proven semantics.

If credit buckets provide absolute totals/residuals, calculate a weighted remaining ratio only when mathematically valid.

Do not add unrelated rates together.

### Shared model

Do not redesign the schema unless actual StepFun data cannot be represented honestly.

If a shared model extension becomes necessary:

* prove the need using live StepFun data
* preserve Codex/Cursor compatibility
* document it
* create an ADR

## Deliverable

Documented StepFun → normalized mapping.

## Test

Produce normalized payload from real data and verify:

* labels honest
* percentages correct
* resets correct
* no raw StepFun schema leaks into QML
* no secret fields

## Completion Evidence

Record mapping and any justified compromises.

## Status

* [x] Complete

---

# P4-T7 — Implement StepFun Provider

## Objective

Implement StepFun behind the existing provider architecture.

## Instructions

Expected structure:

```text
collector/providers/stepfun.py
```

Provider owns:

* secret retrieval
* Oasis token handling
* WebID derivation
* StepFun HTTP requests
* upstream parsing
* plan-shape detection
* normalization

Generic collector must not understand:

* Oasis tokens
* StepFun endpoints
* WebID
* StepFun response fields

Provider contract remains:

* `id`
* `display_name`
* `detect()`
* `fetch_usage()`
* normalized output
* `ProviderError`

## Deliverable

Working StepFun provider.

## Test

* configured credential detection
* missing credential
* live usage
* upstream failure
* malformed response
* expired/invalid token
* no secret output

## Completion Evidence

Record results without credential material.

## Status

* [x] Complete

---

# P4-T8 — Register StepFun in Collector

## Objective

Expose StepFun through existing generic CLI dispatch.

## Instructions

Register:

```text
stepfun → StepFunProvider
```

Expected:

```bash
ai-usage status stepfun --json
```

No StepFun-specific logic should spread through the generic dispatcher beyond necessary provider construction.

## Test

Run:

```bash
ai-usage status stepfun --json
ai-usage status codex --json
ai-usage status cursor --json
```

All must operate independently.

## Completion Evidence

Record all three results.

## Status

* [x] Complete

---

# P4-T9 — Validate StepFun Cache and Stale Fallback

## Objective

Make StepFun use the existing XDG last-success cache.

## Instructions

Expected cache:

```text
~/.cache/horizon/usage-stepfun.json
```

Cache only normalized fields.

Never cache:

* Oasis token
* Cookie header
* WebID if unnecessary
* decoded JWT
* raw StepFun payload

Ensure `breakdown[]` persists through cache if required by existing cache whitelist.

## Test

1. successful live request writes cache
2. inspect cache
3. force live failure
4. verify stale StepFun data returned
5. remove cache and repeat failure
6. verify actual error returned
7. verify Codex/Cursor unaffected

## Completion Evidence

Record cache/stale/security results.

## Status

* [x] Complete

---

# P4-T10 — Display StepFun Alongside Codex and Cursor

## Objective

Display all three providers using the existing multi-provider UI.

## Instructions

Extend explicit Phase 4 provider list to:

```text
codex
cursor
stepfun
```

Do not add provider settings/discovery UI.

Use generic normalized `breakdown[]`.

For rolling-window StepFun plans display:

```text
StepFun
<plan>

5-Hour Usage
XX%
Reset: ...

Weekly Usage
YY%
Reset: ...
```

For credit-plan accounts display only meaningful credit meters.

Do not hard-code StepFun upstream field names in QML.

## Deliverable

Three-provider popup.

## Test

Verify:

1. all three succeed
2. StepFun fails, Codex/Cursor succeed
3. Cursor fails, StepFun/Codex succeed
4. Codex fails, Cursor/StepFun succeed
5. stale StepFun with live other providers

## Completion Evidence

Record isolation results.

## Status

* [x] Complete

---

# P4-T11 — Manual Refresh Independence

## Objective

Ensure Refresh handles all three providers independently.

## Instructions

Use existing common refresh path.

Do not add scheduler/background refresh.

Failure of StepFun must not block responses from Codex or Cursor.

## Test

* all success
* StepFun auth failure
* StepFun upstream failure
* stale StepFun
* repeated refresh
* recovery after failure

## Completion Evidence

Record results.

## Status

* [x] Complete

---

# P4-T12 — Security and Credential Lifecycle Validation

## Objective

Prove Horizon's first stored secret is handled correctly.

## Instructions

Test the complete lifecycle:

```text
missing
→ set
→ retrieve internally
→ use
→ status
→ clear
→ missing
```

Inspect:

* shell history exposure
* process arguments
* stdout
* stderr
* Horizon config
* XDG cache
* repository
* docs
* task evidence

Run secret audit after using the real token.

Test invalid/expired token without exposing it.

## Deliverable

Document security behavior in `docs/security.md` and StepFun provider docs.

## Test

No actual Oasis token or credential material may appear outside the OS secret store and transient process memory.

## Completion Evidence

Record PASS/FAIL for each location checked.

## Status

* [x] Complete

---

# P4-T13 — Regression Validation

## Objective

Confirm Phase 4 did not regress existing providers.

## Instructions

Repeat meaningful Codex/Cursor tests:

### Codex

* live usage
* stale behavior
* UI

### Cursor

* both real meters
* stale behavior
* UI

### StepFun

* live usage
* failure
* stale behavior
* UI

## Deliverable

Three-provider regression evidence.

## Status

* [x] Complete

---

# P4-T14 — Documentation Review

## Objective

Make the StepFun mechanism reproducible without exposing secrets.

## Instructions

Ensure documentation answers:

1. What credential does Horizon require?
2. Where is it stored?
3. How is it configured?
4. How is it removed?
5. What is Oasis-Token?
6. How is Oasis-Webid derived?
7. What endpoint provides usage?
8. What endpoint provides plan name?
9. How are rolling-window plans detected?
10. How are credit plans detected?
11. How are percentages normalized?
12. How does caching work?
13. What happens when auth expires?
14. What upstream behavior is unofficial/fragile?

Review:

* `docs/providers/stepfun.md`
* `docs/security.md`
* `docs/usage-schema.md`
* `docs/cache.md`
* relevant ADRs
* task evidence

Use sanitized examples only.

## Completion Evidence

Record documentation review PASS/FAIL.

## Status

* [x] Complete

---

# P4-T15 — Phase 4 Handoff Validation

## Objective

Determine whether Phase 4 satisfies the immutable contract.

This task adds no functionality.

## Instructions

Read Phase 4 in `PHASES.md` again.

Create:

`docs/handoffs/phase-4.md`

Include:

## Deliverables

Meaningful implementation/docs files.

## StepFun Discovery

Document:

* Oasis auth mechanism
* secure storage mechanism
* WebID derivation
* rate-limit endpoint
* plan-status endpoint
* observed plan shape
* limitations

## Usage Mapping

Describe actual account behavior:

### If rolling-window plan

* 5-Hour Usage
* Weekly Usage
* independent reset timestamps

### If credit-plan

* meaningful credit meter(s)
* why zero/absent rolling-window values were not shown

## Credential Security

Confirm:

* token stored only in OS credential store
* no password stored
* no login flow
* token absent from cache/config/repo/logs/docs
* `auth stepfun status` exposes no material

## Multi-Provider Behavior

Confirm:

* Codex works independently
* Cursor works independently
* StepFun works independently
* one failure does not block others

## Acceptance Results

Record PASS/FAIL:

1. Real StepFun account usage or credit information can be retrieved.
2. StepFun data is normalized through the common model.
3. Existing credentials are reused without exposing secrets.
4. StepFun failure does not affect Codex or Cursor.
5. All three providers can appear together in Horizon.
6. StepFun discovery and limitations are documented.

## Decisions

Reference:

* secure OS credential storage ADR
* any shared-model ADR required by actual StepFun data

Do not create an ADR merely because implementation work occurred.

## Deferred Work

Record out-of-scope discoveries.

If any acceptance criterion fails:

* Phase 4 remains active
* fix/refine Phase 4
* do not weaken the phase contract

Record exactly one:

`PHASE 4 HANDOFF: PASS`

or

`PHASE 4 HANDOFF: FAIL`

## Status

* [x] Complete

---

# Deferred Work

Likely examples:

* StepFun username/password/OAuth login → outside current product scope
* settings UI for credentials → Phase 5
* provider enable/disable UI → Phase 5
* automatic refresh → Phase 5
* notifications → Phase 5
* credential import from other tools → Future if justified
* Oasis support for another provider → Future only when a real provider proves the need

Do not generalize Oasis itself into a framework merely because another service might use it someday.

The **secret-store seam** may be reused because it has immediate StepFun use.

The **Oasis implementation remains StepFun-owned** until another real provider proves otherwise.

---

# STOP CONDITION

When `P4-T15` passes:

**STOP.**

Do not:

* begin Phase 5
* build settings UI
* build login flows
* add username/password storage
* add notification logic
* add periodic refresh
* create a general Oasis framework
* create speculative provider credential abstractions

Phase 5 requires a new explicit execution instruction.
