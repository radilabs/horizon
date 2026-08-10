# Provider contract (Phase 2)

Horizon providers are small Python modules selected by an explicit registry in the `ai-usage` CLI.

There is **no** dynamic plugin loading, entry-point discovery, or DI framework.

## Responsibilities

Each provider implementation must support:

| Concern | Method / attribute | Notes |
|---------|--------------------|--------|
| Identity | `id: str` | Stable CLI id (`codex`) |
| Display | `display_name: str` | Default label before fetch |
| Availability | `detect() -> None` | Raises `ProviderError` if auth/local prerequisites missing |
| Retrieval | `fetch_usage(**opts) -> dict` | Returns **normalized** usage payload (`status=ok` or raises) |
| Errors | `ProviderError(code, message)` | Codes aligned with usage schema statuses |

Conceptual shape:

```text
Provider
  id
  display_name
  detect()
  fetch_usage(**options) -> normalized dict
```

Normalization happens inside the provider (or helpers it owns). The CLI dispatcher does not understand upstream HTTP/auth.

## Dispatcher

```text
PROVIDERS = {
  "codex": CodexProvider,
}
```

Unknown provider ids fail with a clear error (no traceback for normal invalid input).

## What providers must not do

* Store Horizon-owned credentials
* Emit tokens/cookies/authorization material in normalized output
* Require Plasma/QML knowledge

## Immediate use

Only `codex` is registered in Phase 2. The registry exists so Phase 3 can add another provider without rewriting the CLI.
