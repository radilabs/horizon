# Horizon release process (v0.1.0)

## Version source

* Plasmoid: `plasmoid/metadata.json` → `KPlugin.Version`
* Release tag: `v0.1.0`
* Changelog: `CHANGELOG.md`

Keep these in sync for each release.

## Produce / install from a clean tree

```bash
git checkout v0.1.0   # or a release tarball
./scripts/install.sh
ai-usage status codex --json
ai-usage status cursor --json
# optional:
ai-usage auth stepfun set
ai-usage status stepfun --json
```

Confirm metadata:

```bash
kpackagetool6 --type Plasma/Applet --show com.radilabs.horizon | grep -i version
```

## Validation checklist

1. Collector reports ok/stale JSON for enabled providers
2. Widget installs and appears in the picker
3. Compact shows `AI <n>%` (or neutral state)
4. Popup shows only enabled providers
5. Settings persist provider toggles + refresh interval
6. StepFun token set/replace/remove via settings or CLI (KWallet only)
7. Secret audit: no tokens in repo/cache/docs

## Tagging

```bash
git tag -a v0.1.0 -m "Horizon 0.1.0"
git push origin v0.1.0
```

## Notes

No automated CI release pipeline in v0.1.0. Manual install from git tag/tarball is the supported path.
