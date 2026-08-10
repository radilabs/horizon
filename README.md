# Horizon

KDE Plasma widget that shows remaining limits / quotas for AI coding tools.

**Phase 1 status:** real Codex usage via local collector `ai-usage status codex --json`.

## Quick start

See [docs/development.md](docs/development.md) and [docs/providers/codex.md](docs/providers/codex.md).

```bash
mkdir -p ~/.local/bin
ln -sfn "$PWD/collector/ai-usage" ~/.local/bin/ai-usage
ai-usage status codex --json | jq .

kpackagetool6 --type Plasma/Applet --install plasmoid
# after edits:
kpackagetool6 --type Plasma/Applet --upgrade plasmoid
```

Plugin Id: `com.radilabs.horizon`

Requires an existing Codex ChatGPT login (`~/.codex/auth.json`). Horizon does not implement login and does not store credentials.
