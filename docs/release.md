# Horizon release process

## Version source

Keep these in sync for each release:

* `VERSION`
* Plasmoid: `plasmoid/metadata.json` → `KPlugin.Version`
* Changelog: `CHANGELOG.md`
* README version line
* Annotated git tag `vX.Y.Z`
* GitHub Release for that tag (manual; no CI pipeline)

Current release: **0.1.1** (`v0.1.1`).

## Produce / install from a clean tree

```bash
git checkout v0.1.1   # or a release tarball
./scripts/install.sh
ai-usage status codex --json
ai-usage status cursor --json
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
6. StepFun token set/replace/remove via settings or CLI (KWallet only); expired tokens may auto-refresh once from stored material (ADR-0010)
7. Secret audit: no tokens in repo/cache/docs

## Tagging and GitHub Release

```bash
git tag -a v0.1.1 -m "Horizon 0.1.1"
git push origin v0.1.1
gh release create v0.1.1 --title "Horizon 0.1.1" --notes-file CHANGELOG.md
```

Use the changelog section for that version as the release notes. Do not attach secrets.

## Notes

No automated CI release pipeline. Manual install from git tag/tarball is the supported path.
