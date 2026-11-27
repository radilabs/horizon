# Horizon security rules

## Credential ownership

Prefer **provider-owned** local authentication when it exists (Codex `auth.json`, Cursor `state.vscdb` and `auth.json`, Claude Code `.credentials.json`).

When a provider has **no** local credential store (StepFun, Xiaomi MiMo), Horizon may securely store a **user-supplied** secret in the **OS credential store** (KWallet). See ADR-0009.

Horizon must not:

* implement provider username/password login flows
* store provider passwords
* copy secrets into Horizon config, XDG usage cache, env files, or the repository
* print tokens to stdout, stderr, logs, docs, or task evidence
* accept secrets via CLI flags such as `--token`
* commit authentication files

## Reading credentials

Authentication data may be read only when required to perform a provider request.

Credentials must be retained only in memory for the duration of that request and must not be serialized into Horizon outputs.

## Claude Code session

* Source: `~/.claude/.credentials.json` (Claude Code owns this file)
* Horizon reads it read-only for one usage request (ADR-0011)
* Horizon does **not** refresh, rotate, or copy the access token or refresh token
* Missing, expired, or rejected sessions are `auth_unavailable`; the user re-authenticates in Claude Code
* Never place Claude tokens in Plasma config, cache, docs, or evidence

## StepFun Oasis token

* Configure with: `ai-usage auth stepfun set` (secure prompt / non-echoing TTY)
* Or widget settings → StepFun credential: copy Oasis-Token, then **Save token** (helper reads the clipboard so the secret never appears in process arguments; status becomes `Configured · working` only after a live verify)
* Status/clear: `ai-usage auth stepfun status` / `ai-usage auth stepfun clear`
* Storage: KWallet folder `Horizon`, entry `stepfun/oasis-token`
* On usage `auth_unavailable`, the collector may attempt **one** unofficial `RefreshToken` using that stored value, validate the result against the usage API, then write KWallet only if validation succeeds (ADR-0010)
* Never place the token in Plasma config, cache, docs, or evidence

## Xiaomi MiMo Token Plan key

* Configure with: `ai-usage auth mimo set` (secure prompt / non-echoing TTY, or one stdin line when not a TTY)
* Or widget settings → MiMo credential: copy the `tp-` key, then **Save key** (helper reads the clipboard so the secret never appears in process arguments; the clipboard is cleared after the save attempt returns `working`, `auth_failed`, or `unavailable`)
* Status/clear: `ai-usage auth mimo status` / `ai-usage auth mimo clear`
* Storage: KWallet folder `Horizon`, entry `mimo/token-plan-key`
* Status words: `working` only after a live usage GET is accepted, `auth_failed` for a rejected key, `unavailable` for a network/upstream failure (the stored key is kept), `missing` when nothing is stored, `invalid` when `set` rejects the shape and stores nothing
* Region: `sgp`, `cn`, or `ams`, default `sgp`, never probed
* Horizon **never** reads `XIAOMI_API_KEY`, `MIMO_API_KEY`, or any other environment variable for the key
* Horizon **never** parses `~/.bashrc` or any shell profile
* Horizon **never** reads MiMo-Code credentials (`~/.local/share/mimocode/auth.json`) or MiMo-Code config (`~/.config/mimocode/`)
* Never place the key in Plasma config, cache, docs, or evidence
* Manual refresh only: the interval timer, startup, popup open, and configuration changes never fetch MiMo. Xiaomi's Token Plan terms restrict the quota to programming tools and prohibit "API calls for request behaviors in obvious non-coding scenarios … such as automated scripts and custom application backends", so unattended polling is out of scope. Details in `docs/providers/mimo.md`.

## Documentation and evidence

Sanitized API examples must use fabricated or redacted identifiers.

Task completion evidence must never include secret values.

## Secret-check procedure

From the repository root, before committing Phase work:

```bash
git status
git diff
git diff --cached
git grep -Ei 'bearer[[:space:]]+[A-Za-z0-9._-]+' || true
git grep -Ei 'access[_-]?token|refresh[_-]?token|api[_-]?key|authorization|oasis-token' || true
```

Inspect Horizon cache (must be non-secret normalized usage only):

```bash
jq . "${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-codex.json"
jq . "${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-cursor.json"
jq . "${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-stepfun.json"
jq . "${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-claude.json"
jq . "${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-mimo.json"
```

Never open or commit:

* Cursor `state.vscdb` / Cookies / `storage.json`
* Cursor CLI `~/.config/cursor/auth.json`
* Codex `auth.json`
* Claude Code `~/.claude/.credentials.json`
* any Oasis token material
* any MiMo `tp-` key material, including `XIAOMI_API_KEY` / `MIMO_API_KEY` values and MiMo-Code `auth.json`

Inspect any matches manually. Treat matches as candidates, not automatic leaks.

Confirm:

* no real tokens are tracked
* no real credential files are tracked
* ignored credential-shaped filenames are not force-added
* docs and task evidence contain only sanitized examples
* cache files contain no credentials
* StepFun token exists only in KWallet (not repo/cache)
* MiMo `tp-` key exists only in KWallet (not repo/cache)

MiMo key check (must find only fixtures whose text contains `fake`):

```bash
git grep -nE 'tp-[A-Za-z0-9]{16,}' || true
```
