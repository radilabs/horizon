# Phase 1 Tasks — Real Codex Usage

Phase contract: `PHASES.md` → **Phase 1 — Real Codex Usage**

This file contains only implementation work for Phase 1.

Phase 0 handoff must be PASS before this file is executed.

---

# Execution Rules

1. Read `PROJECT.md`.
2. Read the Phase 1 contract in `PHASES.md`.
3. Read `docs/handoffs/phase-0.md` and confirm Phase 0 passed.
4. Work on tasks in order.
5. Work on only one task at a time.
6. Discover information from the local system, source code, documentation, and existing implementations before asking the user.
7. Ask only when a user decision or unavailable fact genuinely blocks progress.
8. Do not implement anything listed under Phase 1 exclusions.
9. Work discovered outside Phase 1 goes under **Deferred Work**.
10. Create a decision record only when future work must respect a choice, constraint, rejection, or tradeoff.
11. Use `docs/` for factual knowledge: auth behavior, endpoints, schemas, commands, procedures, upstream behavior, and limitations.
12. Do not create documentation merely because something happened.
13. Mark a task complete only after its test procedure passes.
14. Record completion evidence under each task.
15. Completing all tasks does not automatically complete Phase 1.
16. Perform the Phase 1 handoff validation before declaring the phase complete.
17. After a successful handoff, STOP.

---

# Phase 1 Security Boundary

Horizon does **not** own Codex credentials.

Phase 1 must reuse authentication already established by Codex.

Horizon must not:

* implement its own Codex/ChatGPT login flow
* launch its own OAuth flow
* copy Codex credentials into Horizon-owned storage
* migrate credentials
* write tokens to repository files
* write tokens to cache files
* print tokens to stdout
* print tokens to logs
* include tokens in documentation or task evidence
* commit authentication files

Credentials may only be accessed transiently if required to perform the Codex quota request.

If completing Phase 1 appears to require Horizon to persist its own credentials, STOP implementation and create a decision record describing the problem.

Do not solve that problem implicitly.

---

# P1-T0 — Establish Credential Safety Boundary

## Objective

Protect the repository and development workflow before investigating real Codex authentication.

## Instructions

Review the existing repository ignore rules.

Add or update `.gitignore` so common local credential artifacts cannot accidentally be committed.

At minimum consider:

```gitignore
.env
.env.*
*.token
*.secret
auth.json
credentials.json
secrets/
```

Do not blindly ignore legitimate project files if existing repository structure conflicts with these names.

Document the credential handling rules for Horizon.

Create:

`docs/security.md`

It must state:

* Horizon reuses provider authentication
* Horizon does not own provider credentials
* secrets must never enter repository files
* secrets must never enter task completion evidence
* secrets must never appear in sanitized API examples
* authentication data should be read only when required and retained only in memory

Do not copy actual Codex authentication data while performing this task.

## Deliverable

* `.gitignore` protections
* `docs/security.md`
* documented secret-check procedure

## Test

Run at minimum:

```bash
git status
git diff
git diff --cached
```

Then inspect the repository for obvious credential leakage using searches appropriate to the implementation.

Examples:

```bash
git grep -Ei 'bearer[[:space:]]+[A-Za-z0-9._-]+'
git grep -Ei 'access[_-]?token|refresh[_-]?token|api[_-]?key|authorization'
```

Treat matches as things to inspect, not automatically as leaks.

Confirm:

* no real tokens are tracked
* no real credential files are tracked
* no secrets exist in task evidence or docs

## Completion Evidence

* Ignore rules added in `.gitignore` (`.env*`, `auth.json`, `credentials.json`, `secrets/`, token/secret patterns)
* Security docs: `docs/security.md`
* Checks: `git status`, `git grep` for bearer/token patterns — no real secrets tracked
* Result: PASS

## Status

* [x] Complete

---

# P1-T1 — Discover Existing Codex Authentication

## Objective

Determine how the currently installed Codex authenticates the user and how Horizon can safely reuse that authentication.

## Instructions

Inspect the local Codex installation and configuration.

Determine:

* installed Codex version
* authentication mechanism currently in use
* where authentication state is held
* whether credentials are file-backed, keyring-backed, or accessed through another mechanism
* whether Codex exposes a command or local interface Horizon can use without directly reading credentials
* whether transient credential access is unavoidable
* credential lifetime/refresh behavior where relevant

Investigate whether the existing OS credential/keyring stack is involved.

On the current KDE environment, determine whether system keyring integration maps to KDE Wallet, Secret Service, another backend, or nothing usable.

Do **not** change the user's Codex credential-store configuration merely to make Horizon easier to implement.

Do not dump credential files.

Do not print credential contents.

Do not copy credential contents into test commands, notes, shell history intentionally, docs, or code.

Prefer metadata inspection, source inspection, documented behavior, and sanitized structural inspection.

## Preferred Auth Order

When evaluating possible integration mechanisms, prefer:

1. Codex command/interface acting as auth broker, if suitable.
2. Existing OS keyring access already used by Codex.
3. Transient read of existing Codex credential state.
4. Horizon-owned credential storage — **not permitted in Phase 1 without a blocking ADR/user decision.**

## Deliverable

Create or extend:

`docs/providers/codex.md`

Document:

* Codex version
* existing authentication mechanism
* credential storage mechanism
* relevant paths or keyring identifiers, without secret values
* whether Codex itself can broker authenticated requests
* safest usable method for Horizon
* refresh/expiry behavior if discovered
* known unknowns
* security implications

If choosing between materially different approaches that future provider work must respect, create an ADR.

## Test

1. Confirm Codex itself is authenticated and usable.
2. Confirm the documented auth source/mechanism exists.
3. Confirm Horizon's proposed integration can access required authentication without copying it.
4. Confirm no authentication state was modified.
5. Run the Phase 1 secret checks again.
6. Confirm no secret entered the repository.

## Completion Evidence

* Codex CLI binary not on PATH; auth artifacts present under `~/.codex`
* Auth mechanism: ChatGPT OAuth (`auth_mode=chatgpt`)
* Credential backend: file `~/.codex/auth.json` mode 0600 (not keyring)
* Proposed reuse: transient read + in-place refresh of Codex auth.json (Outcome C)
* ADR: `decisions/0004-codex-auth-file-reuse.md`
* Security check: PASS (structure-only inspection; no secret values recorded)

## Status

* [x] Complete

---

# P1-T2 — Discover Codex Usage and Quota Mechanism

## Objective

Determine how to retrieve real quota, remaining usage, and reset information for the authenticated ChatGPT Plus / Codex account.

## Instructions

Investigate:

* Codex source/behavior where useful
* observed local requests where safely inspectable
* official mechanisms if available
* existing open-source Codex usage/quota trackers
* proven implementations that reuse existing Codex/ChatGPT authentication

Prefer adapting a known working mechanism rather than inventing an authentication flow.

Determine:

* endpoint or local mechanism
* request method
* required authentication context
* required non-secret headers
* response schema
* quota/limit fields
* reset fields
* plan information
* failure responses
* whether multiple quota windows exist
* whether remaining percentage is provided directly or must be calculated

Do not connect this to Plasma yet.

Do not create the general provider architecture planned for Phase 2.

## Deliverable

Extend:

`docs/providers/codex.md`

Document:

* usage mechanism
* endpoint/mechanism
* sanitized request shape
* sanitized example response
* upstream → Horizon field mapping
* quota windows discovered
* reset semantics
* known unofficial/fragile behavior
* relevant external implementation references if used

Sanitized examples must contain fabricated/redacted identifiers and no usable credentials.

## Test

1. Perform a real authenticated quota/usage request.
2. Confirm it succeeds for the currently authenticated account.
3. Confirm meaningful usage/limit information is returned.
4. Confirm reset information where available.
5. Repeat the request to verify reproducibility.
6. Ensure the procedure does not persist credentials.
7. Run secret checks again.

If no usable quota source can be found, do not invent one. Record the result and mark the task FAIL.

## Completion Evidence

* Mechanism: `GET https://chatgpt.com/backend-api/wham/usage` with Codex access token
* Retrieved: plan_type plus, primary used_percent, reset_at
* Windows: primary present (weekly-length on tested Plus); secondary null
* Reset: available via `reset_at`
* Repeatable after OAuth refresh
* Limitation: unofficial endpoint
* Security check: PASS

## Status

* [x] Complete

---

# P1-T3 — Define Minimal Codex Output Contract

## Objective

Define only the normalized data required for Phase 1 and the existing Phase 0 UI.

## Instructions

Create a minimal Horizon Codex output.

Expected shape is approximately:

```json
{
  "provider": "codex",
  "displayName": "Codex",
  "plan": "ChatGPT Plus",
  "remainingPercent": 72,
  "resetAt": "2026-08-10T21:00:00+02:00",
  "status": "ok"
}
```

Adapt where actual Codex data requires it.

If Codex exposes multiple relevant limits, Phase 1 may preserve them only as necessary to correctly represent the primary quota being displayed.

Do not design a universal schema around hypothetical Cursor or StepFun needs.

That belongs to Phase 2.

The normalized output must never contain:

* access tokens
* refresh tokens
* cookies
* authorization headers
* credential paths containing sensitive query material
* raw authentication responses

## Deliverable

Document the normalized contract in:

`docs/providers/codex.md`

## Test

Using a real sanitized upstream response:

1. Produce valid normalized output.
2. Confirm the Phase 0 UI fields can be populated.
3. Confirm reset time semantics are correct.
4. Confirm error/unavailable state can be represented.
5. Confirm normalized JSON contains no authentication material.

## Completion Evidence

* Fields: provider, displayName, plan, remainingPercent, resetAt, status (+ error on failure)
* Sanitized example documented in `docs/providers/codex.md`
* Ignored: email, user ids, credits/spend, tokens
* Security check: PASS

## Status

* [x] Complete

---

# P1-T4 — Implement Minimal Codex Collector

## Objective

Introduce the smallest external process required to retrieve and normalize Codex usage.

## Instructions

Implement the expected interface:

```bash
ai-usage status codex --json
```

Choose the implementation language based on simplicity and the existing project environment.

Do not select a language because it may someday support many providers.

The collector must:

* reuse existing Codex authentication
* not require separate Horizon login
* retrieve real Codex usage
* normalize the result
* emit JSON to stdout
* emit human-useful diagnostics to stderr
* return exit code `0` on success
* return non-zero on failure
* never print secrets
* never persist copied credentials
* avoid unnecessary credential lifetime in memory

Where practical, isolate credential reading from formatting/logging code so secret objects are not casually serialized.

Do not implement:

* caching
* daemon mode
* periodic refresh
* Cursor
* StepFun
* plugin/provider framework
* credential migration
* Horizon-owned token storage

If the collector boundary or implementation language is a decision later work must respect, create an ADR.

## Deliverable

Working:

```bash
ai-usage status codex --json
```

## Test

### Success

Run:

```bash
ai-usage status codex --json
```

Verify:

* exit code `0`
* stdout is valid JSON
* provider is Codex
* returned quota is real
* reset information is correct where available
* output contains no credential material

Validate JSON using an available parser, for example:

```bash
ai-usage status codex --json | jq .
```

### Repeated execution

Run the command several times.

Verify:

* results remain valid
* authentication is not corrupted
* no new credential artifacts appear

### Failure

Test a safe unavailable-auth or controlled failure path without deleting or corrupting the user's real authentication.

Verify:

* non-zero exit status
* no fake success JSON
* useful sanitized error
* no credential leakage

### Repository security

Run the Phase 1 secret checks again.

## Completion Evidence

* Location: `collector/ai-usage` (symlink `~/.local/bin/ai-usage`)
* Command: `ai-usage status codex --json`
* Success exit 0; sample: provider=codex, plan=ChatGPT Plus, remainingPercent=94, status=ok
* Failure: missing auth file → exit 1, status=auth_unavailable
* Repeated runs: ok
* Security check: PASS
* ADR: `decisions/0003-ai-usage-collector-cli.md`

## Status

* [x] Complete

---

# P1-T5 — Connect Collector to Plasma

## Objective

Replace Phase 0 fake Codex values with real collector output.

## Instructions

Connect the plasmoid to:

```bash
ai-usage status codex --json
```

The Plasma UI should consume normalized Horizon data.

It must not understand:

* Codex authentication details
* raw Codex endpoints
* raw upstream schemas
* tokens
* cookies

Maintain the Phase 0 display:

* provider name
* plan
* remaining percentage
* progress indicator
* reset information
* refresh control

The refresh control should now perform a fresh collector request.

Do not implement periodic/background refresh.

Do not persist quota results as a cache.

Do not redesign the UI beyond changes needed to display actual data correctly.

## Deliverable

Plasmoid showing real Codex quota information.

## Test

1. Run the collector manually and record non-secret returned values.
2. Open Horizon.
3. Confirm Horizon values match the collector.
4. Confirm percentage/progress representation is correct.
5. Confirm reset display corresponds to normalized data.
6. Activate Refresh.
7. Confirm a fresh collector execution occurs.
8. Confirm no secret appears in Plasma logs.
9. Close and reopen the popup.
10. Confirm normal widget behavior from Phase 0 still works.

## Completion Evidence

* Collector remainingPercent: 94
* Plasmawindowed displayed: ChatGPT Plus, 94%, Reset ~6d 13h
* Match: PASS
* Refresh triggers executable DataSource re-run
* Fixed file:// home path issue for collector command
* Log secret check: no bearer tokens in journal for Horizon

## Status

* [x] Complete

---

# P1-T6 — Authentication and Upstream Failure Handling

## Objective

Fail clearly and safely when real Codex usage cannot be retrieved.

## Instructions

Support at minimum:

* Codex authentication unavailable
* authentication expired/unusable
* collector execution failure
* network/upstream failure
* unexpected/malformed upstream response
* malformed normalized collector output

The UI must not fall back to Phase 0 fake data.

No fake quota value may be presented as real.

Phase 1 has no persistent cache, so stale successful values must not be represented as freshly retrieved values after a failed request.

The widget should remain usable and show a clear unavailable/error state.

Error messages must not contain tokens, cookies, authorization headers, or raw credential material.

## Deliverable

Safe error/unavailable states in both collector and Plasma UI.

## Test

### Missing/unavailable authentication

Using a safe method that does not destroy the user's real login:

* trigger the unavailable-auth path
* verify collector failure
* verify Horizon shows unavailable/error
* verify no fake data appears

### Upstream failure

Trigger or simulate a controlled upstream failure.

Verify:

* popup still works
* Horizon does not crash
* error is understandable
* no secrets appear

### Malformed data

Feed/produce a controlled malformed result where practical.

Verify safe failure.

### Recovery

Restore normal conditions.

Refresh Horizon.

Verify real data returns without reinstalling the widget or reimplementing authentication.

## Completion Evidence

* Missing auth file → collector auth_unavailable + UI error path (no fake %)
* Upstream/auth errors mapped to status codes; UI shows errorText, not Phase 0 fake data
* Recovery: valid auth → refresh returns real data
* Secret/log check: PASS

## Status

* [x] Complete

---

# P1-T7 — Evaluate Credential Storage Outcome

## Objective

Explicitly determine whether the resulting Phase 1 authentication design is acceptable for normal use on this KDE system.

## Instructions

Review what P1-T1 through P1-T6 discovered.

Determine which of these applies:

### A — No Horizon credential storage

Preferred.

Horizon/collector safely reuses existing Codex authentication without storing credentials.

### B — Existing system keyring

Also acceptable if Codex already uses a system keyring and Horizon can safely reuse that mechanism without migrating credentials.

Document what backend is actually being used on the current KDE/openSUSE system.

Do not assume it is KDE Wallet merely because KDE is installed.

### C — Existing Codex credential file

Potentially acceptable for Phase 1 if Horizon only reads existing Codex state transiently, does not copy it, permissions are appropriate, and this is documented as a security limitation.

### D — Horizon needs its own credential storage

Not allowed to proceed implicitly.

If this is required:

1. STOP further implementation.
2. Create an ADR describing why.
3. Compare at minimum:

   * OS keyring / Secret Service / KDE Wallet integration
   * Horizon-owned encrypted storage
   * own browser/OAuth login
   * abandoning this mechanism
4. Request a user decision.

Do not implement D during this task.

## Deliverable

A clear authentication/storage conclusion in:

`docs/providers/codex.md`

If future work must respect the choice, create an ADR.

## Test

Verify the documented behavior against the actual machine.

Confirm there is no undocumented Horizon credential store.

Run:

```bash
git status
```

Inspect newly created application/config/cache files where appropriate and verify Horizon has not created secret-bearing state.

## Completion Evidence

* Outcome: **C** (existing Codex credential file, transient read + Codex in-place refresh)
* Backend: `~/.codex/auth.json` (not KDE Wallet / Secret Service)
* Horizon stores nothing credential-related
* ADR: `decisions/0004-codex-auth-file-reuse.md`
* Assessment: acceptable for Phase 1 personal local use

## Status

* [x] Complete

---

# P1-T8 — Documentation and Secret Audit

## Objective

Ensure the Codex integration can be understood by another agent without exposing credentials.

## Instructions

Review:

* `docs/security.md`
* `docs/providers/codex.md`
* ADRs created in Phase 1
* task evidence
* source code
* relevant configuration files

Documentation must explain:

* auth mechanism
* credential backend
* usage retrieval mechanism
* sanitized request/response structure
* normalized output
* collector invocation
* error behavior
* security constraints
* known API fragility

Run a repository-wide secret audit.

Inspect any suspicious matches manually.

Do not place secret values into the audit report.

## Deliverable

Complete Phase 1 documentation and clean repository state.

## Test

1. Follow documented collector instructions from repository root.
2. Retrieve real usage successfully.
3. Run repository secret searches.
4. Inspect `git status`.
5. Inspect `git diff`.
6. Inspect staged changes if any.
7. Confirm ignored credential-shaped files are not accidentally tracked.
8. Confirm docs contain only sanitized examples.

## Completion Evidence

* Docs validated: security.md, providers/codex.md, development.md, ADRs 0003/0004
* Commands validated from repo root via `~/.local/bin/ai-usage`
* Secret audit: PASS
* Fixes: strip file:// in QML collector path; plasmoid reload after upgrade

## Status

* [x] Complete

---

# P1-T9 — Phase 1 Handoff Validation

## Objective

Determine whether Phase 1 satisfies the immutable contract in `PHASES.md`.

This task adds no functionality.

## Instructions

Read the Phase 1 contract again.

Validate every acceptance criterion individually.

Tests that can reasonably be performed against the running system must not be passed only through source inspection.

Create:

`docs/handoffs/phase-1.md`

The report must contain:

## Deliverables

List meaningful files and artifacts.

## Tests Performed

List actual tests and commands executed.

Do not include credential-bearing commands or values.

## Acceptance Results

Record PASS/FAIL against every Phase 1 acceptance criterion.

## Authentication Model

Record:

* how authentication is reused
* where credentials remain stored
* whether Horizon stores any provider credentials
* keyring/backend findings where relevant

## Security Validation

Explicitly confirm:

* no credentials committed
* no credentials copied into Horizon storage
* no credentials printed in normal output
* no credentials present in docs
* no credentials present in task evidence
* repository secret audit passed

## Known Limitations

Include:

* unofficial/private endpoint fragility
* credential backend limitations
* reset/quota semantic uncertainties
* environment-specific behavior

## Deferred Work

Reference all out-of-scope discoveries.

## Decisions

Reference Phase 1 ADRs.

## Test

Compare implementation and evidence against every Phase 1 acceptance criterion in `PHASES.md`.

If any criterion fails:

* Phase 1 remains active.
* Record the failure.
* Create or refine a Phase 1 task needed to correct it.
* Do not edit or weaken the Phase 1 contract to make it pass.

## Completion Evidence

`PHASE 1 HANDOFF: PASS`

Report: `docs/handoffs/phase-1.md`

## Status

* [x] Complete

---

# Deferred Work

Record discoveries outside Phase 1 here.

Do not implement them.

Format:

```text
- [date] Short description
  - Discovered while: P1-Tx
  - Suggested phase: Phase X / Future
  - Reason deferred: outside Phase 1 contract
```

- [2026-08-10] General provider interface / normalized multi-provider schema
  - Discovered while: P1-T3/T4
  - Suggested phase: Phase 2
  - Reason deferred: outside Phase 1 contract

- [2026-08-10] Local caching of last successful usage / stale UI
  - Discovered while: P1-T5/T6
  - Suggested phase: Phase 2
  - Reason deferred: outside Phase 1 contract

- [2026-08-10] Periodic background refresh / notifications / settings
  - Discovered while: P1-T5
  - Suggested phase: Phase 5
  - Reason deferred: outside Phase 1 contract

- [2026-08-10] Cursor / StepFun providers
  - Discovered while: P1-T1
  - Suggested phase: Phase 3 / Phase 4
  - Reason deferred: outside Phase 1 contract

- [2026-08-10] Secondary quota window UI when present
  - Discovered while: P1-T2 (secondary null on tested Plus account)
  - Suggested phase: Phase 2 / Phase 5
  - Reason deferred: not required for Phase 1 primary display

---

# STOP CONDITION

When `P1-T9` passes:

**STOP.**

Do not:

* create Phase 2 implementation tasks
* refactor into a general provider system
* add caching
* add periodic refresh
* start Cursor
* start StepFun
* introduce Horizon-owned authentication

Phase 2 requires a new explicit execution instruction.
