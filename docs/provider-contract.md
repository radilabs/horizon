# Provider contract (Phase 2, updated Phase 7)

Horizon providers are small Python modules selected by an explicit registry in the `ai-usage` CLI.

There is **no** dynamic plugin loading, entry-point discovery, or DI framework.

## Responsibilities

Each provider implementation must support:

| Concern | Method / attribute | Notes |
|---------|--------------------|--------|
| Identity | `id: str` | Stable CLI id (`codex`, `cursor`, `stepfun`, `claude`, `mimo`) |
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

Successful usage payloads use the Phase 7 meter contract in `docs/usage-schema.md` (ADR-0012): an ordered `meters` list of provider-native labels, percent remaining, and per-meter resets. `remainingPercent`, `secondaryRemainingPercent`, and `breakdown` are compatibility projections of that list. Providers build the list through `providers.contract.project_ok` so those copies cannot drift.

## Dispatcher

```text
PROVIDERS = {
  "codex": CodexProvider,
  "cursor": CursorProvider,
  "stepfun": StepFunProvider,
  "claude": ClaudeProvider,
  "mimo": MiMoProvider,
}
```

Unknown provider ids fail with a clear error (no traceback for normal invalid input).

## What providers must not do

* Store Horizon-owned credentials **except** via the minimal OS secret store when no provider-owned local source exists (ADR-0009)
* Emit tokens/cookies/authorization material in normalized output
* Require Plasma/QML knowledge

## Registered providers

* `codex` — ChatGPT / Codex usage (Phase 1–2)
* `cursor` — Cursor DashboardService usage from two read-only, Cursor-owned sources (Phase 3, extended Phase 11)
* `stepfun` — StepFun Step Plan via user-supplied Oasis token in KWallet (Phase 4)
* `claude` — Claude Pro/Max usage via read-only Claude Code credentials (Phase 6.5)
* `mimo` — Xiaomi MiMo Token Plan credits via one official GET and a user-supplied `tp-` key in KWallet (Phase 12)

Cursor reads two sources (ADR-0013): the IDE `~/.config/Cursor/User/globalStorage/state.vscdb` key `cursorAuth/accessToken`, used only when that value is JWT-shaped, and the Cursor CLI `~/.config/cursor/auth.json` top-level `accessToken`. The CLI token is tried only when the IDE value is not sendable or the IDE attempt returns HTTP 401/403. Network errors, non-auth HTTP and bad JSON do not fall through. Both files are read-only; `refreshToken` in either file is never used.

Provider-specific auth path overrides may be passed through the generic `--auth-file` flag (Codex: `auth.json`; Cursor: the IDE `state.vscdb`; Claude: `.credentials.json`). Cursor's second source is overridden with `CURSOR_CLI_AUTH_FILE`, alongside the existing `CURSOR_STATE_VSCDB` and `CURSOR_API_BASE`. StepFun uses `ai-usage auth stepfun …` and the OS credential store instead. Cursor and Claude auth remain read-only. Claude refresh is forbidden (ADR-0011).

`mimo` takes a `--region {sgp,cn,ams}` option on `status` and `auth` (default `sgp`), used only by `mimo` and validated by argparse choices. It is also set in widget settings. Regions are never probed: the request goes to the configured host only, and HTTP 401 is `auth_unavailable` for that region.

MiMo is the only manual-refresh provider. The QML refresh paths for the interval timer, startup, popup open, and configuration change do not include it; `MeterIntake.js` holds that rule so the popup can only fetch MiMo from the Refresh button, the F5 shortcut, or `ai-usage status mimo` run by hand. Details and the Xiaomi terms citation are in `docs/providers/mimo.md`.
