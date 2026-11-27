# Task Execution

Current stage: **Stage 3 — Maintenance & Hardening**  
Current phase: **Phase 10 — Post-0.2.0 Remediation**  
Status: **implemented; Watcher PASS; awaiting owner acceptance**  
Task file: `tasks/phase-10-post-0.2.0-remediation.md`

Phase 10 is the only executable work. Its scope is findings W-01..W-14 of `reports/post-v0.2.0-external-watcher-1.md`, as bounded by `PHASES.md` Phase 10. Horizon stays at **0.2.0**.

Stage 2 is closed history. Phase 9 was accepted on 2026-10-09. Snapshot: `docs/handoffs/phase-9.md`.

All other phase task files under `tasks/` are historical execution evidence only. Their presence does not authorize additional work.

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
