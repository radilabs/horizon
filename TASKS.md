# Horizon — Tasks

Detailed implementation tasks live under `tasks/`.

Only an explicitly authorized phase may be executed.

## Current Execution

- **Current stage:** Stage 3 — Maintenance & Hardening
- **Current phase:** Phase 10 — Post-0.2.0 Remediation
- **Status:** implemented; Watcher PASS (attempt 3); awaiting owner acceptance
- **Task file:** `tasks/phase-10-post-0.2.0-remediation.md`
- **Branch:** `phase-10-post-0.2.0-remediation` (from `eadcfb3`)
- **Input:** `reports/post-v0.2.0-external-watcher-1.md` (findings W-01..W-14)

Phase 10 is the only executable work. Scope is limited to W-01..W-14 as written in `PHASES.md` Phase 10. Horizon stays at **0.2.0**: no version bump, tag or release in this phase.

Stage 2 is closed. Phase 9 was accepted on 2026-10-09. Snapshot: `docs/handoffs/phase-9.md`.

## Stage 3 Roadmap

**Stage 3 — Maintenance & Hardening (opened 2026-11-27):**

- Phase 10 — Post-0.2.0 Remediation (authorized 2026-11-27; executable)

No other Stage 3 phase is authorized.


## Stage 2 Roadmap

**Stage 2 — Provider Contract & UX (closed 2026-10-09):**

- Phase 7 — Provider Information Contract (accepted 2026-10-09)
- Phase 8 — Plasma UI/UX Refresh (accepted 2026-10-09)
- Phase 9 — Compact UX and Release Polish (accepted 2026-10-09)

Stage 2 is closed history. None of its phases is executable.

## Task Files

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
├── phase-6.5-claude-usage.md             # ACCEPTED (historical)
├── phase-7-provider-information-contract.md  # ACCEPTED (historical)
├── phase-8-plasma-ui-refresh.md          # ACCEPTED (historical)
├── phase-9-compact-ux-release-polish.md  # ACCEPTED (historical)
└── phase-10-post-0.2.0-remediation.md    # AUTHORIZED 2026-11-27 (executable)
```

Historical task files are execution evidence only. Their presence does not authorize further work.

## History

Last completed phase: **Phase 9 — Compact UX and Release Polish** (accepted 2026-10-09; Horizon **0.2.0**).

Phase 8 — Plasma UI/UX Refresh was accepted 2026-10-09.

Phase 7 — Provider Information Contract was accepted 2026-10-09.

Phase 6.5 — Claude Usage was accepted 2026-10-09.

Phase 6 — StepFun Auth Resilience was accepted 2026-09-11 (Horizon **0.1.1**).

Phases 0–5 predate adoption of the current Stage-aware Factory shell. Their accepted history is preserved as-is and must not be rewritten retrospectively.

Stage 1 closed after Phase 6.5. Stage 2 closed after Phase 9. Stage 3 was opened on 2026-11-27 with Phase 10.

## Authority

- Product definition and Factory rules: `PROJECT.md`
- Stage/phase contracts: `PHASES.md`
- Accepted snapshots: `docs/handoffs/`

Do not add providers (including Groq). Do not start a phase after Phase 10 without explicit authorization.
