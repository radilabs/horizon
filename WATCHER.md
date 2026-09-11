# Watcher / Verifier

The Watcher independently verifies whether an active Horizon phase satisfies its immutable contract.

The Watcher does not implement features, redefine scope, or accept phases.

## Inputs

For an authorized future phase, inspect:

1. `PROJECT.md`
2. the active Stage/Phase contract in `PHASES.md`
3. `TASKS.md`
4. the active phase task file
5. actual repository state and diffs
6. build, test, runtime, log, or UI evidence needed by the contract

Do not rely on implementer summaries as proof.

## Verification

Check every acceptance criterion and handoff requirement, including scope/exclusions, required behavior, tests, limitations, Deferred Work, and any durable documentation or decisions the phase requires.

If a required criterion cannot be verified, the result is FAIL.

Each run ends in exactly one overall result:

- **PASS** — all required criteria and handoff conditions are supported by evidence.
- **FAIL** — one or more required conditions are unmet, unverifiable, or materially violated.

No conditional PASS.

## Findings

Each blocking finding should identify:

- ID
- severity
- contract reference
- finding
- evidence
- required correction

Out-of-scope discoveries become Deferred Work unless the existing contract already requires them.

## Reports

Store temporary verification output under `reports/` using:

`stage-<S>-phase-<N>-watcher-<attempt>.md`

Raw reports are runtime artifacts and are ignored by Git. Promote durable facts or decisions into the proper task, docs, or decisions artifact.

## Historical Note

Horizon phases 0–5 predate this mandatory Watcher contract. Do not fabricate retrospective Watcher reports or PASS results for them.

For future Factory-managed phases, Watcher PASS is required before owner acceptance, but it does not replace explicit owner acceptance.
