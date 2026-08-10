# Horizon

KDE Plasma widget that shows remaining limits / quotas for AI coding tools.

**Phase 2 status:** Codex runs through a small provider registry with last-successful usage cache and stale UI fallback.

Architecture docs: [provider-contract](docs/provider-contract.md), [usage-schema](docs/usage-schema.md), [cache](docs/cache.md).

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
