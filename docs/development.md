# Horizon development workflow

Plasma version tested: **Plasma 6** (`plasma6-workspace-6.7.3` on openSUSE Tumbleweed).

Plugin Id: `com.radilabs.horizon`

Source tree:

```text
plasmoid/
├── metadata.json
└── contents/
    └── ui/
        └── main.qml
```

## Install (first time)

From the repository root:

```bash
kpackagetool6 --type Plasma/Applet --install plasmoid
```

Package install location:

`~/.local/share/plasma/plasmoids/com.radilabs.horizon/`

Confirm:

```bash
kpackagetool6 --type Plasma/Applet --list | grep horizon
kpackagetool6 --type Plasma/Applet --show com.radilabs.horizon
```

Add **Horizon** from Plasma's widget picker, or:

```bash
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
  panelById(panelIds[0]).addWidget("com.radilabs.horizon");
'
```

## Update after editing QML

```bash
kpackagetool6 --type Plasma/Applet --upgrade plasmoid
```

Plasma keeps running applet instances in memory. After upgrade, **reloading is required** or you will still see the old UI:

1. Remove Horizon from the panel and add it again, **or**
2. Restart Plasma Shell: `plasmashell --replace`
3. For quick UI checks without the panel: `plasmawindowed com.radilabs.horizon`

Panel popups are expected: clicking `AI` opens the full representation as a **popup above the panel**, not as a separate desktop window. `plasmawindowed` is only a development preview window.

## Quick preview (recommended while iterating)

```bash
plasmawindowed com.radilabs.horizon
```

Shows the full representation in a standalone window.

## Logs / debugging

User journal (QML load errors appear here):

```bash
journalctl --user -f
```

Filter:

```bash
journalctl --user --since "5 min ago" --no-pager | grep -E 'horizon|com.radilabs|main.qml|QQml'
```

Example error when QML is invalid:

```text
error when loading applet "com.radilabs.horizon" ... main.qml:7:1: PlasmoidItemBroken is not a type
```

## Phase 0 note

Displayed Codex usage is **fake hardcoded data** in `main.qml`.
Real Codex integration belongs to Phase 1.
