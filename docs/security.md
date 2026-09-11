# Horizon security rules

## Credential ownership

Prefer **provider-owned** local authentication when it exists (Codex `auth.json`, Cursor `state.vscdb`).

When a provider has **no** local credential store (StepFun), Horizon may securely store a **user-supplied** secret in the **OS credential store** (KWallet). See ADR-0009.

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

## StepFun Oasis token

* Configure with: `ai-usage auth stepfun set` (secure prompt / non-echoing TTY)
* Or widget settings → StepFun credential: copy Oasis-Token, then **Save token** (helper reads the clipboard so the secret never appears in process arguments; status becomes `Configured · working` only after a live verify)
* Status/clear: `ai-usage auth stepfun status` / `ai-usage auth stepfun clear`
* Storage: KWallet folder `Horizon`, entry `stepfun/oasis-token`
* On usage `auth_unavailable`, the collector may attempt **one** unofficial `RefreshToken` using that stored value, validate the result against the usage API, then write KWallet only if validation succeeds (ADR-0010)
* Never place the token in Plasma config, cache, docs, or evidence

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
```

Never open or commit:

* Cursor `state.vscdb` / Cookies / `storage.json`
* Codex `auth.json`
* any Oasis token material

Inspect any matches manually. Treat matches as candidates, not automatic leaks.

Confirm:

* no real tokens are tracked
* no real credential files are tracked
* ignored credential-shaped filenames are not force-added
* docs and task evidence contain only sanitized examples
* cache files contain no credentials
* StepFun token exists only in KWallet (not repo/cache)
