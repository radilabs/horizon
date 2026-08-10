# Phase 0 Handoff — Plasma Skeleton

Date: 2026-08-10  
Environment: openSUSE Tumbleweed, Plasma 6 (`plasma6-workspace-6.7.3-2.1.x86_64`), Wayland  
Plugin Id: `com.radilabs.horizon`

## Deliverables

* `plasmoid/metadata.json` — Plasma 6 applet metadata
* `plasmoid/contents/ui/main.qml` — compact `AI` + full popup with fake Codex usage UI
* `docs/development.md` — install / upgrade / reload / logging workflow
* `docs/handoffs/phase-0.md` — this report
* `README.md` — Phase 0 project summary
* `decisions/0001-plasma6-plasmoid-identity.md`
* `decisions/0002-phase0-fake-data-in-qml.md`
* `tasks/phase-0-plasma-skeleton.md` — task evidence for P0-T1 … P0-T9

## Tests Performed

1. `kpackagetool6 --type Plasma/Applet --install plasmoid` / `--upgrade plasmoid`
2. Package listed and shown via `kpackagetool6 --list` / `--show com.radilabs.horizon`
3. Added widget to bottom horizontal Plasma panel; compact `AI` visible
4. `plasmawindowed com.radilabs.horizon` preview of full representation
5. Fake data change `remainingPercent` 72 → 25 → upgrade → visible 25% in plasmawindowed; restored to 72
6. Intentional QML type error logged via `journalctl --user` (`PlasmoidItemBroken is not a type`); reverted
7. After plasmashell reload, user confirmed panel click on `AI` opens popup with Codex / ChatGPT Plus / 72% / reset / Refresh
8. Documented workflow followed from repository root

## Results

Phase 0 acceptance criteria (`PHASES.md`):

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Horizon can be installed as a local Plasma widget | PASS |
| 2 | Horizon can be added to a Plasma panel | PASS |
| 3 | Compact representation renders correctly | PASS |
| 4 | Clicking the widget opens its full representation | PASS (user-confirmed panel popup) |
| 5 | Full representation displays fake Codex usage data | PASS (user-confirmed) |
| 6 | Editing the widget and reloading Plasma produces visible changes | PASS |
| 7 | Local development workflow is documented | PASS (`docs/development.md`) |
| 8 | No real provider credentials or network calls exist | PASS |

**PHASE 0 HANDOFF: PASS**

## Known Limitations

* Panel applets cache QML aggressively; after `kpackagetool6 --upgrade`, remove/re-add or `plasmashell --replace` is required or the panel may show a stale UI while `plasmawindowed` shows the new one.
* Panel full representation is a Plasma **popup**, not a separate window (`plasmawindowed` is only for development preview).
* Fake Codex data only; no auth, network, collector, caching, or settings.
* Wayland automated pointer injection (`ydotool`) was unreliable for panel click testing in this session.

## Deferred Work

See `tasks/phase-0-plasma-skeleton.md` → Deferred Work.

* Real Codex usage / collector / auth reuse → Phase 1
* Provider architecture / caching → Phase 2
* Cursor / StepFun → Phases 3–4
* Polish (periodic refresh, notifications, settings) → Phase 5

## Decisions

* `decisions/0001-plasma6-plasmoid-identity.md` — Plasma 6 + plugin Id `com.radilabs.horizon`
* `decisions/0002-phase0-fake-data-in-qml.md` — fake usage as QML properties; no Phase 0 collector/abstraction

## Stop

Phase 0 handoff satisfied. **Do not begin Phase 1** without a new explicit execution instruction.
