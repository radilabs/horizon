# ADR-0001: Plasma 6 plasmoid package identity

## Status

Accepted

## Context

Horizon must install as a local KDE Plasma widget. The machine under development runs Plasma 6 (`plasma6-workspace` 6.7.x). Plasma 5 `metadata.desktop` packaging is obsolete for this environment.

## Decision

- Target **Plasma 6** only for Phase 0 onward unless a later phase explicitly revisits compatibility.
- Use `metadata.json` with `KPackageStructure: Plasma/Applet` and `X-Plasma-API-Minimum-Version: 6.0`.
- Use stable plugin Id **`com.radilabs.horizon`**.
- Keep plasmoid sources under repository path `plasmoid/`.

## Consequences

- Install/upgrade with `kpackagetool6 --type Plasma/Applet`.
- Later phases must keep the plugin Id stable; renaming breaks existing user panel layouts.
- Plasma 5 is out of scope unless a new decision reverses this.
