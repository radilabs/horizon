# Factory Agent Entry Point

Horizon uses the Factory execution structure for future development.

Before doing implementation work, read:

1. `PROJECT.md`
2. `PHASES.md`
3. `TASKS.md`

`TASKS.md` is the current execution authority. If it says no Stage or Phase is authorized, do not begin implementation.

## Roles

- **Driver / Orchestrator** — follow `DRIVER.md`; coordinates authorized work and lifecycle gates.
- **Coder Team** — execute only the authorized phase task file.
- **Watcher / Verifier** — follow `WATCHER.md`; independently verify the active contract.
- **Reviewer / Dr Watson** — review risks and assumptions without expanding active scope.

## Boundaries

Future task files are created only after their Stage/Phase is explicitly authorized.

Out-of-scope discoveries become Deferred Work.

Model narration is not evidence. Use repository state, diffs, builds, tests, runtime observations, logs, UI observations where relevant, independent verification, and explicit owner acceptance.

Never begin the next phase automatically.

## Historical Note

Horizon phases 0–5 were accepted before the current Stage-aware Factory shell was adopted. Keep those records as history; do not manufacture retrospective stages, Watcher reports, or other lifecycle evidence.

**Model proposes actions; the harness owns truth.**
