# Horizon

KDE Plasma widget that shows remaining limits / quotas for AI coding tools.

**Phase 4 status:** Codex, Cursor, and StepFun appear together through a shared provider model, XDG last-successful usage cache, and stale UI fallback.

Architecture docs: [provider-contract](docs/provider-contract.md), [usage-schema](docs/usage-schema.md), [cache](docs/cache.md), [security](docs/security.md).

Provider notes: [Codex](docs/providers/codex.md), [Cursor](docs/providers/cursor.md), [StepFun](docs/providers/stepfun.md).

## Quick start

See [docs/development.md](docs/development.md).

```bash
mkdir -p ~/.local/bin
ln -sfn "$PWD/collector/ai-usage" ~/.local/bin/ai-usage

ai-usage status codex --json | jq .
ai-usage status cursor --json | jq .

# StepFun has no local credential store — paste an existing Oasis token into KWallet:
ai-usage auth stepfun set
ai-usage status stepfun --json | jq .

kpackagetool6 --type Plasma/Applet --install plasmoid
# after edits:
kpackagetool6 --type Plasma/Applet --upgrade plasmoid
```

Plugin Id: `com.radilabs.horizon`

## Credentials

Horizon does **not** implement provider login flows.

* **Codex** — reuses `~/.codex/auth.json` (provider-owned).
* **Cursor** — reads Cursor `state.vscdb` transiently (provider-owned; never modified).
* **StepFun** — stores a user-supplied Oasis token in the OS credential store (KWallet) only. Never in config, cache, env files, or the repo. See ADR-0009.

Manage StepFun token: `ai-usage auth stepfun {set,status,clear}` (no `--token` flag).
