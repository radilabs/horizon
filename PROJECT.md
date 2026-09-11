## General Information

**Project Horizon desired plan (ready to copy into tasks / issues):**

Build a **KDE Plasma widget (plasmoid)** that acts as an “AI agent usage panel”.

**Core goal**  
Show remaining limits / quotas for the AI coding tools and subscriptions I actually use, in a clean Plasma-native panel (progress bars, remaining %, reset timers, plan name, optional daily/model breakdowns). Inspired by the Omarchy Quattro agent panel, but made for KDE Plasma instead of Omarchy.

**Priority providers (start here)**  
1. **Codex** – ChatGPT Plus plan (individual, *not* organization). Use session/token or local auth method (same style existing trackers use).  
2. **Cursor** – individual account (unofficial / local + internal endpoints).  
3. **StepFun Step Plan** – credit-based subscription (unofficial dashboard endpoints).

**Later / nice-to-have**  
- Other LLM providers I use  
- Auto-detection of active subscriptions where possible  
- Local caching + background refresh  
- Notifications when limits are getting low

**Technical notes**  
- Plasma side: QML plasmoid (compact representation + full popup panel).  
- Data side: mostly unofficial/session-based for the three priority providers (no clean public org-style APIs for my Plus Codex / Cursor / Step Plan).  
- Prefer wrapping or adapting existing open-source trackers where they already work, rather than reinventing auth from scratch.

---

# Development Factory Rules

Horizon follows the Factory control model going forward.

The execution hierarchy is:

**Project → Stage → Phase → Task**

Phases 0–5 were completed before the current Stage-aware Factory shell was adopted. Their accepted contracts, task evidence, decisions, docs, and handoffs remain authoritative historical records. Do not rewrite them to simulate stages, Watcher runs, or other lifecycle steps that did not occur at the time.

## Stage Boundaries

Any future significant capability begins inside an explicitly authorized Stage/Phase contract.

A stage groups coherent phases into a product milestone or development state. Stage exit conditions must be checked explicitly before another stage begins.

## Phase Boundaries

A phase is an immutable execution boundary once authorized.

Tasks may be refined inside the active phase, but its:

- goal
- scope
- exclusions
- acceptance criteria
- handoff contract

must not be expanded during implementation.

Work discovered outside the active phase is recorded as Deferred Work rather than implemented opportunistically.

A completed task does not mean a completed phase.

No role may begin the next phase automatically.

## Task Availability

`PHASES.md` contains the historical roadmap and immutable contracts.

`TASKS.md` is the current execution authority.

Detailed future task files are created only after their Stage/Phase is explicitly authorized.

Historical task files remain in `tasks/` as execution evidence and are not executable merely because they exist.

## Evidence

Model narration, intent, or a worker saying "done" is not evidence.

Progress and verification use direct observations such as repository state, diffs, builds, tests, runtime behavior, logs, screenshots where relevant, independent verifier observations, and explicit owner acceptance.

**Model proposes actions; the harness owns truth.**

## Roles

### Owner / Roboticist

Defines intent, evaluates the actual product, and authorizes or accepts Stage/Phase transitions.

### Planner

Maintains project structure, Stage/Phase contracts, architecture boundaries, and acceptance criteria.

### Driver / Orchestrator

Coordinates the execution lifecycle, delegates work, routes corrections, assembles evidence, and stops at gates.

The Driver does not invent work, expand scope, or accept a phase on behalf of the owners.

### Reviewer / Dr Watson

Inspects implementation, challenges assumptions, identifies risks, and proposes Deferred Work.

Review findings do not automatically expand active scope.

### Coder Team

Implements only the active task scope and provides direct test/build/runtime evidence.

### Verifier / Watcher

Independently checks the active phase against its acceptance criteria and handoff contract.

Watcher PASS is required for future phases before owner acceptance, but it is not sufficient by itself: explicit owner acceptance is still required.

## Information Management

### Decision Records

Use `decisions/` only when future work must respect a choice, constraint, rejection, or tradeoff.

Do not create decisions merely to narrate implementation. Do not silently rewrite accepted historical decisions; supersede them when needed.

### Documentation

Use `docs/` for durable technical knowledge such as external API behavior, schemas, caching/staleness rules, credential/configuration storage, build/install procedures, and platform limitations.

### Task Notes

Use the current phase task file for implementation progress, tests/results, changed files, temporary findings, known limitations, Deferred Work, and handoff status.

### Runtime Reports

Use `reports/` for temporary Watcher and reviewer output. Runtime reports are not permanent project truth and are ignored by Git except for `reports/README.md`.

If a runtime report contains something future work must respect, deliberately promote it into the active task file, `docs/`, or `decisions/`.

### Deferred Work

Useful discoveries outside the active phase are recorded rather than implemented. They become executable only when explicitly included in a newly authorized contract.

## Acceptance and Transition

For future Factory-managed phases:

1. implementation and local checks complete;
2. independent Watcher verifies the actual repository/environment state;
3. in-scope findings are corrected and re-verified;
4. the Driver presents evidence to the project owners;
5. the owners explicitly accept or reject the phase;
6. only after acceptance are final handoff evidence and checkpoint commit/tag produced;
7. STOP;
8. the next Stage/Phase must be explicitly authorized before task creation or execution.

If no phase is authorized, the contract is ambiguous, required evidence is missing, or satisfying a requirement would expand scope: STOP rather than improvise across the boundary.

## Core Rule

If forgetting information could cause a future agent to make the wrong implementation choice, record it in the correct durable artifact. Otherwise, do not create documentation merely because something happened.
