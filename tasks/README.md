# Task Execution

Current stage: **none authorized**  
Current phase: **none authorized**  
Status: **idle**

No executable task file.

Last accepted phase: **Phase 6 — StepFun Auth Resilience** (`docs/handoffs/phase-6.md`, Horizon 0.1.1).

Historical phase task files remain under `tasks/` as execution evidence only. Their presence does not authorize additional work.

## Execution Order (when a phase is authorized)

1. Read `PROJECT.md`.
2. Read `PHASES.md`.
3. Read `TASKS.md`.
4. Read the currently authorized phase task file.
5. Confirm that file is the only authorized work.
6. Execute the first incomplete task.
7. Do not work outside the active phase.
8. Discoveries outside scope go to Deferred Work.
9. A completed task does not imply a completed phase.
10. Phase completion requires mandatory independent Watcher verification and explicit owner acceptance.
11. Stop at phase handoff. Never start the next phase automatically.

Do not create future phase task files before authorization.

Phases 0–5 predate the current Stage-aware Factory shell. Do not rewrite their accepted history retrospectively.

If `TASKS.md` says no phase is authorized, STOP.
