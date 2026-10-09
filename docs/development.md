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

If an already added widget does not pick up the change, log out and back in,
then re-add Horizon from the widget picker if it is missing.

Run the plasmoid-side tests (no Plasma session needed):

```bash
QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_compact_summary.qml
QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_refresh_keys.qml
QT_QPA_PLATFORM=offscreen qmltestrunner6 -input tests/test_meter_intake.qml
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
        ├── configGeneral.qml
        └── MeterIntake.js      # meter rows, compact text, tooltip text
collector/
tests/
  test_*.py                    # collector / schema / provider tests (unittest)
  test_*.qml                   # plasmoid-side tests (qmltestrunner6)
scripts/
  install.sh | upgrade.sh | uninstall.sh
```

The plasmoid imports `MeterIntake.js` for meter intake and for the compact and
tooltip summaries. Change the collector output only through the contract in
`docs/usage-schema.md`.

## Debugging

```bash
journalctl --user -f
journalctl --user --since "5 min ago" --no-pager | grep -E 'horizon|com.radilabs|main.qml|QQml'
ai-usage status codex --json | jq .
ai-usage status claude --json | jq .
```

## Credentials (dev)

Same rules as production: never commit tokens; StepFun only via `ai-usage auth stepfun set` / settings → KWallet. Claude uses the existing Claude Code credentials file read-only (`ai-usage status claude --json`).
