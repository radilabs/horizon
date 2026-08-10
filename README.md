# Horizon

KDE Plasma widget that shows remaining limits / quotas for AI coding tools.

**Phase 0 status:** local Plasma 6 plasmoid with fake Codex usage UI.

## Quick start

See [docs/development.md](docs/development.md).

```bash
kpackagetool6 --type Plasma/Applet --install plasmoid
# after edits:
kpackagetool6 --type Plasma/Applet --upgrade plasmoid
plasmawindowed com.radilabs.horizon
```

Plugin Id: `com.radilabs.horizon`

Displayed Codex data in Phase 0 is **fake**. Real Codex integration is Phase 1.
