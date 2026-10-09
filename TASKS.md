# Horizon — Tasks

Detailed implementation tasks live under `tasks/`.

Only an explicitly authorized phase may be executed.

## Current Execution

- **Current stage:** none authorized
- **Current phase:** none authorized
- **Status:** idle

No executable task file.

Stage 1 is closed. Phase 6 and Phase 6.5 are accepted. Stage 1 exit conditions were checked on 2026-10-09 (`docs/handoffs/phase-6.5.md`). Stage 2 is not opened. Do not begin Phase 7 until it is explicitly authorized.


## Planned Next Phases — Not Authorized

Owner planning (amended 2026-10-08) records the following in `PHASES.md`:

**Stage 2 — Provider Contract & UX (not opened; Stage 1 is closed, and Stage 2 still requires explicit authorization):**

- Phase 7 — Provider Information Contract (Claude is a required design input)
- Phase 8 — Plasma UI/UX Refresh
- Phase 9 — Compact UX and Release Polish

These are planning anchors only. **No executable task files exist for these phases, and none of them is authorized.** Detailed design, acceptance criteria, and task decomposition are intentionally deferred until the relevant phase is explicitly authorized through the existing Factory lifecycle.

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
├── phase-6-stepfun-auth-resilience.md   # ACCEPTED (historical)
└── phase-6.5-claude-usage.md             # ACCEPTED (historical)
```

Historical task files are execution evidence only. Their presence does not authorize further work.

## History

Last completed phase: **Phase 6.5 — Claude Usage** (accepted 2026-10-09; release remains Horizon **0.1.1**).

Phase 6 — StepFun Auth Resilience was accepted 2026-09-11 (Horizon **0.1.1**).

Phases 0–5 predate adoption of the current Stage-aware Factory shell. Their accepted history is preserved as-is and must not be rewritten retrospectively.

Stage 1 / Phase 6 was the first work completed under the current Stage-aware Factory lifecycle (Watcher PASS + owner acceptance). Stage 1 / Phase 6.5 is the second, and it closes Stage 1.

## Authority

- Product definition and Factory rules: `PROJECT.md`
- Stage/phase contracts: `PHASES.md`
- Current executable work: **none**
- Accepted snapshots: `docs/handoffs/`

Do not create or execute a later phase (including Groq) until it is explicitly authorized.
