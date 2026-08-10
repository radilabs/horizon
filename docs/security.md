# Horizon security rules

## Credential ownership

Horizon reuses provider authentication that already exists on the machine.

Horizon does **not** own provider credentials.

Horizon must not:

* implement its own provider login or OAuth flow
* copy provider credentials into Horizon-owned storage
* migrate credentials into the repository
* write tokens to cache or config files owned by Horizon
* print tokens to stdout, stderr, logs, docs, or task evidence
* commit authentication files

## Reading credentials

Authentication data may be read only when required to perform a provider request.

Credentials must be retained only in memory for the duration of that request and must not be serialized into Horizon outputs.

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
git grep -Ei 'access[_-]?token|refresh[_-]?token|api[_-]?key|authorization' || true
```

Inspect Horizon cache (must be non-secret normalized usage only):

```bash
jq . "${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-codex.json"
jq . "${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-cursor.json"
```

Never open or commit Cursor session artifacts such as:

* `~/.config/Cursor/User/globalStorage/state.vscdb`
* Cursor `Cookies` / `storage.json`

Horizon may read Cursor `state.vscdb` transiently in memory only; it must not copy tokens into cache or the repository.

Inspect any matches manually. Treat matches as candidates, not automatic leaks.

Confirm:

* no real tokens are tracked
* no real credential files are tracked
* ignored credential-shaped filenames are not force-added
* docs and task evidence contain only sanitized examples
* cache files contain no credentials
* Cursor `state.vscdb` / Cookies are not tracked