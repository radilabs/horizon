# Horizon development workflow

Plasma version tested: **Plasma 6** on openSUSE Tumbleweed.

Plugin Id: `com.radilabs.horizon` · Version: see `plasmoid/metadata.json`

## Preferred install (matches users)

From the repository root:

```bash
./scripts/install.sh
```

Collector lives under `~/.local/share/horizon/collector/`; `~/.local/bin/ai-usage` launches it. Do **not** rely on a symlink into the git checkout for normal use.

After QML edits:

```bash
./scripts/upgrade.sh
# reload: remove/re-add the widget, or plasmashell --replace
plasmawindowed com.radilabs.horizon   # quick preview
```

## Development layout

```text
plasmoid/
├── metadata.json
└── contents/
    ├── config/
    │   ├── config.qml
    │   └── main.xml
    └── ui/
        ├── main.qml
        └── configGeneral.qml
collector/
scripts/
  install.sh | upgrade.sh | uninstall.sh
```

## Debugging

```bash
journalctl --user -f
journalctl --user --since "5 min ago" --no-pager | grep -E 'horizon|com.radilabs|main.qml|QQml'
ai-usage status codex --json | jq .
```

## Credentials (dev)

Same rules as production: never commit tokens; StepFun only via `ai-usage auth stepfun set` / settings → KWallet.
