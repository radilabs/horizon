# Stage 2 / Phase 8 — Plasma UI/UX Refresh

**Status: ACCEPTED** (2026-10-09). This file is historical execution evidence. It is **not** executable.

Accepted snapshot: `docs/handoffs/phase-8.md`. Horizon release remains **0.1.1**.

Horizon release remains **0.1.1**.

**Authority:** `PHASES.md` Stage 2 / Phase 8, `TASKS.md`  
**Previous accepted snapshot:** `docs/handoffs/phase-7.md`  
**Information contract:** ADR-0012 (`decisions/0012-ordered-usage-meters.md`), `docs/usage-schema.md`  
**Branch:** `phase-8-plasma-ui-refresh` (from `0ca66c4`, not `main`)  
**Worktree:** `/home/naorw/.t3/worktrees/horizon/phase-6.5-claude-usage`

## Goal

Redesign Horizon's expanded Plasma popup (`fullRepresentation`) around the Phase 7 ordered `meters` contract. The result is an original, information-dense, Plasma-native view built from KDE/Kirigami components and theme values. It shows all four existing providers (Codex, Cursor, StepFun and Claude) with 1..N labeled meters each, a reset per meter, and clear status, error, stale and auth states.

## Current state (baseline, `0ca66c4`)

`plasmoid/contents/ui/main.qml`:

- `fullRepresentation` is a fixed `gridUnit * 18` × `gridUnit * 48` `Item`. Content that does not fit is clipped and cannot be scrolled.
- Header: "Horizon" / "AI Agent Usage". Each provider block shows the bold provider name, the plan line, one row per `breakdown` line (label, bold percent, `ProgressBar`, "Reset: …"), a provider-level "Reset: …" fallback, a status label and a separator. A Refresh button and an "Updating…" label sit at the bottom.
- `applyPayload` reads `breakdown`. If there is none, it builds rows from `remainingPercent`/`secondaryRemainingPercent`, with an empty first label and a second row labeled "Secondary". Each row's reset is `line.resetAt || obj.resetAt`, so a meter with no reset of its own shows the first meter's reset. That is wrong under ADR-0012 and was deferred from Phase 7.
- `applyPayload` hard-codes `errorText` to `""`, so the payload's user-safe `error` text is never shown.
- `compactRepresentation`, `compactText` (`lowestQuotaPercent`) and `tooltipSummary` derive from the same model rows.

## Design direction

The owner's reference image (`/home/naorw/Pictures/ui-screen-1.jpg`) is **inspiration only**. Take the information pattern: provider sections, a plan line, several labeled quota bars, and the time until reset on the meter row. Do not reproduce its chrome, layout or colors. These are explicitly out because Horizon has no data for them: an "Agents" title, a busiest-day line, add/terminal buttons, an orange theme, Primary/Secondary account groups, "Max 20x", an ACTIVE badge, "Use" buttons, "2 free resets", and a Theme/Plugin/App footer.

Use Plasma/Kirigami components and theme values only: `Kirigami.Theme` colors, `Kirigami.Units` spacing and sizes, and the system font. Do not hard-code colors or pixel sizes. Do not add a custom palette.

## Scope

- **Data intake.** Read `meters` when present. Otherwise fall back to `breakdown`, then to the primary/secondary compatibility fields (for pre-Phase-7 cache or an older collector). Treat percent as **remaining**, 0–100. Never compute or show percent used as if it were remaining.
- **Per-meter reset.** A meter shows a reset only when that meter has its own `resetAt`. Do not fill it from the top-level `resetAt`. In the primary/secondary fallback, only the first row may use the top-level `resetAt`, as ADR-0012 §9 defines for the rebuilt first meter.
- **Provider hierarchy.** One section per enabled provider, in the existing order (Codex, Cursor, StepFun, Claude). The section header shows the provider name and the plan when the plan is known. Show no plan when it is null. Never invent one.
- **1..N meters.** Render meters in payload order with provider-native labels. There is no Primary/Secondary wording and no fixed two-row assumption. Duplicate labels are allowed, and order distinguishes them. Each meter row shows label, remaining percent, a bar and the relative reset when known.
- **States.** Make `ok`, `stale`, `auth_unavailable`, `provider_unavailable`, `upstream_error`, `collector_error`, loading and disabled/no-providers distinguishable in text, not by color alone. Stale shows the cached meters plus their age (`fetchedAt`). Auth unavailable carries actionable guidance. The payload's user-safe `error` text may be shown. Failure states show no bars and no 0% placeholders.
- **Fit.** The popup must stay usable with four providers that each have several meters, for example Claude with three or more windows. Replace the fixed clip with scrolling or a layout that adapts to its content within sensible Plasma popup bounds.
- **Native integration.** The popup should be readable in Breeze Light and Breeze Dark, at standard Plasma scaling, and use theme contrast for secondary text. Keep the existing Refresh action and its in-flight state.
- **Verification support.** Add deterministic QML-side checks for meter intake and the reset rule if a lightweight mechanism exists or can be added without new runtime dependencies. Otherwise, use fixture payloads that can be fed to the popup for manual verification. Fixtures contain no credential material.
- **Documentation.** Update user-facing popup descriptions in `README.md`/`docs/` only where they would otherwise be inaccurate. Record durable UI-contract decisions only if Phase 9 must respect them.

## Explicit Exclusions

- New providers, including Groq, OpenRouter, Anthropic API billing and SendGrid.
- Billing, spend, balances, credits beyond existing StepFun meter labels, multi-account or account hierarchy.
- Any change to the collector, providers, authentication, cache, cache schema, or the ADR-0012 meter contract. `git diff -- collector` must be empty.
- Visible changes to the compact panel representation, `compactText`, or the tooltip (`tooltipSummary`). Those are Phase 9. If shared model plumbing changes, compact text and tooltip output must stay identical for the same payloads.
- Widget settings/config UI changes, new configuration keys, and notifications.
- Release polish: version bump, screenshots for release, changelog or release notes (Phase 9).
- Copying the reference image's chrome, theme or any element listed under Design direction.
- New runtime dependencies or a custom visual system outside Plasma/Kirigami.
- Commits or pushes, unless the owners separately ask for them.

## Acceptance Criteria

Each criterion is checked on a real Plasma 6 session with the widget installed from this branch (and in `plasmawindowed com.radilabs.horizon` where useful), plus fixture payloads where live data cannot produce the case.

1. **Four providers visible.** With Codex, Cursor, StepFun and Claude enabled, the expanded popup shows a section for each, with name and known plan. All four can be read without anything being clipped.
2. **Arbitrary meter counts.** Every meter is rendered in payload order with its provider-native label: 1 meter (for example a single-window Codex or one Cursor pool), 2 meters, and 3+ meters (a Claude fixture with a third window). The popup scrolls or fits; nothing is cut off. No Primary/Secondary label appears for any provider.
3. **Correct direction.** Each percent and bar shows percent **remaining** and matches the payload's `remainingPercent` (for example 95 remaining shows as 95% with a mostly full bar). Live values match `ai-usage status <id> --json` for all four providers at the time of the check.
4. **Per-meter reset only when present.** A meter with `resetAt` shows its own relative reset. A meter without `resetAt` shows no reset, even when the top-level `resetAt` or another meter has one. This is checked with a fixture where meter 1 has a reset and meter 2 does not.
5. **Legacy fallback.** A payload with `breakdown` and no `meters`, and a payload with only `remainingPercent`/`secondaryRemainingPercent`, both render without errors and follow criteria 3–4.
6. **States understandable.** Each of `stale` (cached meters plus age), `auth_unavailable` (re-authentication guidance), `upstream_error`, `provider_unavailable`, `collector_error`, loading, and no-providers-enabled is identifiable from text alone. Failure states show no bars and no fabricated 0%. One provider's failure does not hide or disturb the others.
7. **Native look.** Only theme colors and `Kirigami.Units` are used. The popup is legible with adequate contrast in Breeze Light and Breeze Dark. Screenshots of both are recorded as evidence under `reports/`.
8. **No collector or contract change.** `git diff 0ca66c4 -- collector` is empty. Existing tests pass (`python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh`), and `ai-usage status <id> --json` output is unchanged in shape for all four providers.
9. **Compact and tooltip unchanged.** For the same payloads, the panel compact text and tooltip text match their baseline `0ca66c4` behavior.
10. **No secrets.** No token, credential, account id or email appears in QML, fixtures, logs, screenshots or task evidence. The secret audit passes.
11. **Scope held.** Out-of-scope discoveries are recorded under Deferred Work, not implemented.
12. **Watcher PASS.** Independent Watcher verification against criteria 1–11 returns PASS. Then STOP for explicit owner acceptance.

## Execution Tasks

- [x] Re-read ADR-0012, `docs/usage-schema.md` and the current `fullRepresentation`; record a sanitized baseline (screenshot plus live `--json` safe fields for all four providers, and the baseline compact/tooltip text).
- [x] Prepare sanitized fixture payloads: 1, 2 and 3+ meters; a meter without reset; legacy `breakdown`-only; legacy primary/secondary-only; each failure status; stale.
- [x] Change popup data intake to `meters` → `breakdown` → primary/secondary, with the per-meter reset rule. Keep compact/tooltip output unchanged.
- [x] Implement the redesigned expanded popup: provider hierarchy, meter rows, state treatment, fit or scrolling, Kirigami theming.
- [x] Verify on a real Plasma session (Breeze Light and Dark), with live data and fixtures; capture evidence against each acceptance criterion.
- [x] Run tests, check that the collector diff is empty, and run the secret audit; record direct evidence.
- [x] Independent Watcher evaluation against the Phase 8 acceptance criteria; fix in-scope findings and rerun if needed.
- [x] Present the evidence and Deferred Work for owner review. **STOP pending owner acceptance.**

## Evidence

2026-10-09, branch `phase-8-plasma-ui-refresh`.

* Popup reads `meters` via `plasmoid/contents/ui/MeterIntake.js`. A meter reset is shown only when that meter has `resetAt`. The primary/secondary fallback uses `Usage limit` and puts the payload reset on the first row only.
* `breakdownJson` is still built the old way so compact percent and tooltip text stay on the previous path. The popup does not render that JSON, so it does not show a "Secondary" label.
* `git diff 0ca66c4 -- collector` is empty.
* `QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_meter_intake.qml` — 4 tests passed (meters preferred, missing reset not borrowed, breakdown fallback, primary/secondary fallback, failure payload).
* `python3 -m unittest tests.test_usage_contract tests.test_claude_usage tests.test_stepfun_oasis_refresh` — 31 OK.
* Live CLI safe fields matched the popup: Codex Plus 5-hour 99 and Weekly 99; Cursor Pro Cursor Models 75 and Other Models 0; StepFun Plus 5-Hour 97 and Weekly 86; Claude Pro Current session 100 (no `resetAt`) and Current week 78. No secret markers. `meters` equaled `breakdown`.
* Panel compact text stayed `AI 0%` while Cursor Other Models was 0.
* Installed with `scripts/install.sh`. `plasmawindowed com.radilabs.horizon` showed all four providers, plans, `% remaining`, per-meter resets, and Refresh. Color scheme was restored to BreezeClassic afterward.
* Screenshots (gitignored): `reports/phase-8-breeze-light.png`, `reports/phase-8-breeze-dark.png`, `reports/phase-8-breeze-classic.png`.
* Watcher attempt 1: **PASS**. Report: `reports/stage-2-phase-8-watcher-1.md`. No blocking findings.
* Writer documentation review updated the popup description in `README.md`, `docs/usage-schema.md`, and ADR-0012 so they match the accepted popup.
* Owner decision: **accepted** Phase 8 on 2026-10-09. Snapshot: `docs/handoffs/phase-8.md`.

STOP. Do not start Phase 9.

## Deferred Work

- Compact panel, tooltip, and release screenshots remain Phase 9.
- Failure states (`auth_unavailable`, `upstream_error`, `provider_unavailable`, `collector_error`) are covered by the intake test and existing status labels. A live account did not produce those states during this run.
- The three-window Claude case is fixture-tested in `tests/test_meter_intake.qml`. This Pro account returned two windows.

## Handoff Contract

- Every acceptance criterion is supported by direct evidence (screenshots, command output, diffs) recorded in this file or under `reports/`.
- Watcher report at `reports/stage-2-phase-8-watcher-<n>.md` with verdict PASS.
- Explicit owner acceptance after reviewing the evidence.
- Only after acceptance: write `docs/handoffs/phase-8.md` as the accepted-state snapshot and mark this file historical.

STOP. Do not start Phase 9.
