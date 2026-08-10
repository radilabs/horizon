# Provider contract (Phase 2+)

Horizon providers are small Python modules selected by an explicit registry in the `ai-usage` CLI.

There is **no** dynamic plugin loading, entry-point discovery, or DI framework.

## Responsibilities

Each provider implementation must support:

| Concern | Method / attribute | Notes |
|---------|--------------------|--------|
| Identity | `id: str` | Stable CLI id (`codex`, `cursor`, `stepfun`) |
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
  "cursor": CursorProvider,
  "stepfun": StepFunProvider,
}
```

Unknown provider ids fail with a clear error (no traceback for normal invalid input).

## What providers must not do

* Store Horizon-owned credentials **except** via the minimal OS secret store when no provider-owned local source exists (ADR-0009)
* Emit tokens/cookies/authorization material in normalized output
* Require Plasma/QML knowledge

## Registered providers

* `codex` — ChatGPT / Codex usage (Phase 1–2)
* `cursor` — Cursor DashboardService usage via local `state.vscdb` (Phase 3)
* `stepfun` — StepFun Step Plan via user-supplied Oasis token in KWallet (Phase 4)

Provider-specific auth path overrides may be passed through the generic `--auth-file` flag (Codex: `auth.json`; Cursor: `state.vscdb`). StepFun uses `ai-usage auth stepfun …` and the OS credential store instead. Cursor auth remains read-only.
