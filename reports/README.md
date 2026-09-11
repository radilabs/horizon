# Runtime Reports

`reports/` stores temporary execution reports produced by independent reviewers and verifiers during active Factory work.

Report contents are not permanent project truth and are ignored by Git by default.

If a report contains information future work must respect, deliberately promote it into the appropriate durable artifact:

- the active `tasks/phase-N-*.md` for phase evidence and temporary findings needed for handoff;
- `docs/` for durable technical knowledge;
- `decisions/` for durable architectural or product decisions.

Do not commit raw Watcher or Dr Watson reports merely because they exist.

## Watcher Reports

Use:

`stage-<S>-phase-<N>-watcher-<attempt>.md`

## Dr Watson Reports

Use:

`stage-<S>-phase-<N>-watson-<attempt>.md`

## Historical Note

Horizon phases 0–5 were completed before this runtime-report convention was adopted. Do not manufacture retrospective reports for those phases.
