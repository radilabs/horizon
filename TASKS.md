# Horizon — Tasks

Detailed implementation tasks live under `tasks/`.

Only an explicitly authorized phase may be executed.

## Current Execution

- **Current stage:** Stage 1 — Reliability & Provider Resilience
- **Current phase:** Phase 6 — StepFun Auth Resilience
- **Status:** authorized

Executable task file:

- `tasks/phase-6-stepfun-auth-resilience.md`

## Historical Task Files

```text
tasks/
├── README.md
├── phase-0-plasma-skeleton.md
├── phase-1-codex.md
├── phase-2-provider-architecture.md
├── phase-3-cursor.md
├── phase-4-stepfun.md
├── phase-5-polish.md
└── phase-6-stepfun-auth-resilience.md   # CURRENT / AUTHORIZED
```

Phases 0–5 are retained as historical execution evidence. Their presence does not authorize further work.

## History

Last completed phase: **Phase 5 — Operational Polish**.

Phases 0–5 predate adoption of the current Stage-aware Factory shell. Their accepted history is preserved as-is and must not be rewritten retrospectively.

Stage 1 / Phase 6 is the first work authorized under the current Stage-aware Factory lifecycle.

## Current Boundary

Phase 6 may improve resilience of the existing StepFun Oasis authentication path only.

It must not:

- add Groq or any other provider;
- implement StepFun username/password login;
- import browser credentials;
- create a general Oasis/authentication framework;
- expand into account or subscription management.

Out-of-scope findings go to Deferred Work.

## Authority

- Product definition and Factory rules: `PROJECT.md`
- Stage/phase contracts: `PHASES.md`
- Current executable work: `tasks/phase-6-stepfun-auth-resilience.md`
- Accepted historical snapshots: `docs/handoffs/`

After Watcher PASS and explicit owner acceptance, update execution state, write the accepted Phase 6 handoff, checkpoint the phase, and STOP.
