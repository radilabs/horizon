# Horizon

KDE Plasma widget that shows remaining quotas for the AI coding tools you already use.

Compact panel: one meaningful remaining % (the lowest among enabled providers).  
Popup: per-provider plan, meters, reset times, and clear stale/auth/error labels.

## Supported providers

| Provider | Auth |
|----------|------|
| **OpenAI Codex** (ChatGPT Plus) | Reuses `~/.codex/auth.json` |
| **Cursor** | Reads local Cursor session (`state.vscdb`) read-only |
| **StepFun Step Plan** | User-supplied Oasis token stored only in **KWallet** |

Horizon does **not** implement provider login/OAuth, browser cookie import, or password storage.

## Install

Dependencies: Plasma 6, Python 3, Python D-Bus (`python3-dbus`) for KWallet, `kdialog` for optional settings token entry.

```bash
git clone https://github.com/radilabs/horizon.git
cd horizon
./scripts/install.sh
```

This installs:

* collector to `~/.local/share/horizon/collector/`
* launcher to `~/.local/bin/ai-usage` (not a symlink into the git checkout)
* plasmoid `com.radilabs.horizon`

Add **Horizon** from the Plasma widget picker.

Upgrade / uninstall:

```bash
./scripts/upgrade.sh
./scripts/uninstall.sh          # keeps KWallet token + usage cache
./scripts/uninstall.sh --purge  # also removes usage cache; still keeps KWallet token
```

## Authentication

### Codex

Sign in with the Codex/ChatGPT tooling so `~/.codex/auth.json` exists. Horizon reuses it.

```bash
ai-usage status codex --json
```

### Cursor

Stay signed in to the Cursor app. Horizon reads session state transiently and never modifies it.

```bash
ai-usage status cursor --json
```

### StepFun

Paste an existing Oasis token (from a StepFun web session). Stored only in KWallet. If the stored pair is still accepted by StepFun’s unofficial refresh endpoint, Horizon performs **one** automatic refresh and writes KWallet only after a live usage check succeeds.

```bash
ai-usage auth stepfun set      # secure prompt; no --token flag
ai-usage auth stepfun status   # working | auth_failed | missing
ai-usage auth stepfun clear
ai-usage status stepfun --json
```

Or use **Widget settings → StepFun credential**:

1. Copy the `Oasis-Token` cookie from `platform.stepfun.ai`
2. Click **Save token** (optional: paste into the field first as a visual check)
3. Confirm status is `Configured · working`

Status is `Configured · working` only after StepFun accepts the token — not merely that something is stored. The token is never written to Plasma config or the usage cache.

## Configuration

Widget settings (right-click → Configure Horizon):

* Enable/disable **Codex**, **Cursor**, **StepFun**
* Refresh interval: 5 / 10 / **15** / 30 / 60 minutes (default 15)
* StepFun token management

Disabled providers are not queried, refreshed, shown, or included in the compact summary. Disabling does **not** delete credentials.

## Security

* Prefer provider-owned credentials (Codex, Cursor)
* StepFun token: OS credential store only (ADR-0009); bounded Oasis refresh write-back (ADR-0010)
* Usage cache (`~/.cache/horizon/usage-*.json`): normalized non-secret data only
* No telemetry / analytics / cloud sync

See [docs/security.md](docs/security.md).

## Known limitations

Quota APIs for these tools are **unofficial** and can break when providers change endpoints or auth. Details:

* [docs/providers/codex.md](docs/providers/codex.md)
* [docs/providers/cursor.md](docs/providers/cursor.md)
* [docs/providers/stepfun.md](docs/providers/stepfun.md)

Architecture: [provider-contract](docs/provider-contract.md), [usage-schema](docs/usage-schema.md), [cache](docs/cache.md).  
Development notes: [docs/development.md](docs/development.md).  
Release process: [docs/release.md](docs/release.md).

Version: **0.1.1**
