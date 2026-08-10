# Horizon usage cache (Phase 2)

## Location

```text
${XDG_CACHE_HOME:-$HOME/.cache}/horizon/usage-<provider>.json
```

Example for Codex:

```text
~/.cache/horizon/usage-codex.json
```

Example for Cursor:

```text
~/.cache/horizon/usage-cursor.json
```

Example for StepFun:

```text
~/.cache/horizon/usage-stepfun.json
```

Not in the git repository. Not beside provider credentials. Never contains Oasis tokens or cookies.

## Format

```json
{
  "fetchedAt": "2026-08-10T20:30:00+02:00",
  "provider": "codex",
  "data": {
    "provider": "codex",
    "displayName": "Codex",
    "plan": "ChatGPT Plus",
    "remainingPercent": 94,
    "resetAt": "2026-08-17T12:00:00+02:00",
    "status": "ok"
  }
}
```

## Write rules

* Write only after live `status=ok` normalization
* Atomic replace (temp file + `os.replace`)
* File mode preferably `0600`
* Never write tokens or raw upstream responses

## Read rules

* Used only when live retrieval fails
* Returned payload uses `status=stale`, `stale=true`, preserves `fetchedAt`
* Includes user-safe `error` describing the live failure
* Missing/corrupt cache → normal failure payload (no crash)

## Security

Cache may contain plan name and percentages only — never credentials.
