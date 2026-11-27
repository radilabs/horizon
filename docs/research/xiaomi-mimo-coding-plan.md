# Xiaomi MiMo Coding Plan (Token Plan) — discovery note

> **Status: DISCOVERY ONLY. This is not an authorized Stage or Phase.**
> `TASKS.md` is still the execution authority, and it authorizes nothing.
> The Stage 4 / Phase 12 contract below is a **proposal the owner has not authorized**.
> No provider code, task file, or ADR exists for MiMo.
>
> **Status update (2026-11-27):** The owner authorized Stage 4 / Phase 12 on 2026-11-27. The decisions are recorded in `PHASES.md` (Phase 12, Owner Decisions). The text below is the original discovery record and is kept unchanged.

Researched 2026-11-27 against `main` at `220563f` (Horizon 0.2.1).

Evidence labels used in this note:

* **[V]** Verified fact from a primary Xiaomi source (official docs on `mimo.mi.com`).
* **[O]** Account-specific observation from one live, read-only request made during this discovery.
* **[T]** Third-party source (open-source client, issue tracker, aggregator). Not authoritative.
* **[A]** Assumption or inference. Not verified.

## 1. Product identity

* **[V]** Xiaomi's official docs call the product **"Token Plan"**. They describe it as "an exclusive subscription solution launched for AI programming scenarios".
* **[T]** Aggregators say Token Plan was formerly sold as **"MiMo Coding Plan"** (also "Xiaomi Coding Plan" or "小米 Coding Plan"), introduced around April 2026. The official pages that were read never use the name "Coding Plan".
* **[A]** In this note, "MiMo Coding Plan" and "Token Plan" mean the same product.

## 2. Subscription model

### Tiers (individual) — [V]

| Tier | Monthly | Monthly credits | Annual | Annual credits |
|------|---------|-----------------|--------|----------------|
| Lite | $6 / ¥39 | 4.1B | $63.36 / ¥408 | 49.2B |
| Standard | $16 / ¥99 | 11B | $168.96 / ¥1044 | 132B |
| Pro | $50 / ¥329 | 38B | $528 / ¥3468 | 456B |
| Max | $100 / ¥659 | 82B | $1056 / ¥6948 | 984B |

Pro and Max also get `mimo-v2.6-pro-ultraspeed`.

**[T]** An aggregator (codingplans.com) lists 60M / 200M / 700M / 1.6B credits. Those numbers conflict with the official docs and look stale. Ignore them.

### Billing terms — [V]

* **Monthly auto-renew** and **annual auto-renew** for individuals. Without auto-renew, service stops at expiry and the user must buy the plan again.
* **Promotions:** 12% off the first individual purchase, once per account. Annual auto-renew is 12% cheaper than monthly.
* **Team edition:** per-seat Standard, Pro, or Max, monthly or annual. Teams can also buy 1-, 3-, 6-, or 12-month one-time terms. Each seat has its own quota, and team plans cannot be upgraded or downgraded.
* **Upgrades:** an upgrade costs the price difference, and old-plan credits are converted to money value. Downgrades are not allowed. Refunds are not supported.
* **Off-peak multiplier:** credits are consumed at 0.8× from 00:00 to 08:00 Beijing time (16:00 to 24:00 UTC).

### Duration vs reset window

* **[V]** A plan is "valid for one calendar month/year from the date of purchase based on UTC time". For example, a plan bought on March 28 expires at 23:59:59 UTC on April 28.
* **[V]** The official docs give **no** 5-hour, weekly, or daily quota windows. Quota is one pool per billing period.
* **[V]** The credits API reports the "current billing cycle" as `period.start_at` / `period.end_at` (UTC).
* **[O]** On this account, an **annual Lite** plan (`plan_code` = `lite:year`) reports a period of about one year (Nov 2026 → Nov 2027, ending `23:59:59`). `total_credits` is about **49.2B**, which matches the annual allowance. **So an annual plan is one yearly pool with no monthly sub-reset.** For annual plans, the period end is plan expiry or renewal, not a monthly refill.
* **[A]** For monthly plans, the period is presumably one calendar month from purchase. A third-party fixture (CodexBar #5124, `plan_code` `lite`) shows `2026-11-11 21:05:27 → 2026-12-11 23:59:59`, which fits that.

### Quota unit and sharing — [V]

* The unit is **credits**. Each model converts tokens to credits at its own rate:

  | Model | Input (cache hit) | Input (cache miss) | Output |
  |-------|-------------------|--------------------|--------|
  | `mimo-v2.6-pro` | 2.5 | 300 | 600 |
  | `mimo-v2.6-flash` | 2 | 100 | 200 |
  | `mimo-v2.6-pro-ultraspeed` | 25 | 3000 | 6000 |

  ASR costs 30M credits per audio hour. TTS is free for a limited time.
* **One shared pool:** all models draw on a single quota, "consumed in parallel at different ratios". There are no model-specific pools.
* **Compensation credits:** if the remaining value of the old plan exceeds the price of the new plan on renewal, the difference is credited. `total_credits` includes these compensation credits.
* **Rollover:** none. "Any unused quota from your old plan will not be carried over."
* **Exhaustion:** individual service stops and does **not** fall back to bonus or account balance. The user must upgrade or switch to pay-as-you-go. A team seat that runs out stops for the rest of the month.
* **Alerts:** SMS and email at 50%, 90%, and 100% of quota.

## 3. Authentication and usage retrieval

### Official, API-key quota endpoint — [V]

The official API reference lists this endpoint under Finance → "Query Token Plan Credits" (`mimo.mi.com/static/docs/api/asset/credits-get.md`):

```http
GET https://token-plan-{region}.xiaomimimo.com/v1/platform/token_plan
Authorization: Bearer <tp- key>        # or: api-key: <tp- key>
```

* **[V]** It needs the dedicated Token Plan key (prefix `tp-`). The docs show the `cn` host and say to take the dedicated Base URL from the Token Plan console. The documented regions are `cn`, `sgp`, and `ams`.
* **[V]** The docs do not state the HTTP method. **[O]** `GET` returned 200, and both header forms worked.
* **[V]** Response fields:

```json
{
  "object": "token_plan",
  "plan_code": "<string>",
  "period": { "start_at": "YYYY-MM-DD HH:MM:SS (UTC)", "end_at": "YYYY-MM-DD HH:MM:SS (UTC)" },
  "quota": { "total_credits": 0, "used_credits": 0, "remaining_credits": 0 },
  "auto_renew": false,
  "claw_enabled": false
}
```

  `remaining_credits` = `max(0, total_credits − used_credits)`. `total_credits` includes compensation credits.
* **[O]** The live response had exactly this shape, and `used_credits + remaining_credits == total_credits`. Timestamps have no `T` and no offset. They are 19-character UTC strings.
* **[O]** Keys are **region-bound**. The account's key returned 200 on `sgp` and `401 {"error":{"code":"invalid_api_key",…}}` on `cn` and `ams`. A wrong region therefore looks exactly like a bad key.
* **[V]** The same Finance section also lists "Query Account Balance", "Query Daily Consumption", and "Query Daily Bill". They were not read. Pay-as-you-go balances are outside this contract.
* **[T]** CodexBar added this API source in PR #5138, merged 2026-11-21. It uses a `tp-` key from its own config and a `cn`/`sgp` region choice, and does not treat quota as cash. This is the first open-source client to use the official endpoint.
* **[T]** MiMo-Code issue #2495 (opened 2026-09-22, still open, no official reply) asks for a key-based usage endpoint. The official endpoint seems to have appeared after that issue, and before 2026-11-19.

### Inference hosts — [V]/[T]

* **[V]** The OpenAI-compatible base URL is `https://token-plan-{cn|sgp|ams}.xiaomimimo.com/v1`. The Anthropic-compatible one is `…/anthropic`.
* **[T]** Responses carry no rate-limit or quota headers (ai-usagebar #146). Paths such as `/v1/usage` and `/api/quota` return 404.

### Console (dashboard) endpoints — [T], rejected for Horizon

* `GET https://platform.xiaomimimo.com/api/v1/tokenPlan/usage` and `/api/v1/tokenPlan/detail` (plus `/api/v1/balance`) return `monthUsage.items[]` / `usage.items[]` (`name`, `used`, `limit`, `percent`) and `planName`, `planCode`, `currentPeriodEnd`, `expired`, `enableAutoRenew`.
* Authentication is a Xiaomi Account web SSO session (`sid=api-platform`), using cookies `api-platform_serviceToken` and `userId`. The `tp-` key gets a 401 with a `loginUrl`.
* Known clients either paste a browser cookie (OmniRoute, hermes-quota-plugin PR #86) or decrypt the browser's cookie DB and mint `serviceToken` through the SSO redirect chain (omarchy-xiaomi-usage).
* **Horizon must not use this path.** It needs browser-cookie extraction or a pasted session cookie, and those are the prohibited, primary-path mechanisms in `docs/security.md` and `docs/providers/stepfun.md`. It is also unnecessary now that the official endpoint exists. One thing it has that the official API lacks is `planName` (a display name).

### Local credential reuse

* **[O]** On this machine, the `tp-` key is in the environment variable **`XIAOMI_API_KEY`**, exported from `~/.bashrc`. It is 51 characters, starts with `tp-`, and has no whitespace. It is not a Horizon-owned store. The value was not recorded.
* **[T]** omarchy-xiaomi-usage looks for `XIAOMI_API_KEY`, then `MIMO_API_KEY`, then opencode's `auth.json`. **[A]** Neither variable name is a Xiaomi convention. The official docs use `$MIMO_API_KEY` in their examples.
* **[V]** MiMo-Code (Xiaomi's CLI) stores credentials in `~/.local/share/mimocode/auth.json`, with config in `~/.config/mimocode/mimocode.jsonc`. Its documented login is OAuth, with auto-created pay-as-you-go keys (`mimo-code-cli-key…`). **Unknown:** whether it ever stores a `tp-` key, and under what key name. That file is not present on this machine.
* **[A]** A plasmoid launched by Plasma does **not** reliably inherit variables exported in `~/.bashrc`. An env-only source may work from a terminal and fail in the widget.
* **Reuse is read-only by nature.** The endpoint is a plain GET with a static API key. No refresh, rotation, or write-back exists or is needed. Quota and reset can be read without changing any credential.

### Terms-of-use note — [V]

The Subscription page says Token Plan quota "is only available for use in programming tools", and prohibits "API calls for request behaviors in obvious non-coding scenarios … such as automated scripts and custom application backends". The credits endpoint is part of the official API reference and consumes no credits. **[A]** A low-frequency quota read by a usage meter is the endpoint's documented purpose and does not look like the prohibited inference use. Xiaomi has not said this explicitly.

## 4. Horizon compatibility (ADR-0012 mapping)

| Horizon field | MiMo source | Notes |
|---------------|-------------|-------|
| `meters[0].label` | constant `Credits` | Matches Xiaomi's own unit name. One meter only. |
| `meters[0].remainingPercent` | `remaining_credits / total_credits × 100`, integer, clamped 0–100 | Total is known, so no scale is invented. Rounding rule to be fixed in the contract (StepFun uses `round`). |
| `meters[0].resetAt` | `period.end_at`, parsed as UTC → ISO-8601 with `+00:00` | For an annual plan this is **plan expiry or renewal (about a year away)**, not a monthly refill. [O] |
| `plan` | derived from `plan_code` (owner decision, see Q1) | `plan_code` is a code (`lite`, `lite:year`), not a display name. |
| compatibility fields | via `providers.contract.project_ok` | Same as other providers. |

**Data that does not fit, and is not emitted:**

* Raw `total_credits`, `used_credits`, and `remaining_credits` (absolute counts). Only the percent is shown.
* `auto_renew` and `claw_enabled` (subscription flags, not quota).
* Compensation credits as a separate pool. The official API folds them into `total_credits`. The console's separate `compensation_total_token` item is not available from the official API.
* Pay-as-you-go account balance (Finance → Account Balance) is cash, not a meter. Excluded.
* Team seats or multiple keys or regions per user would mean multiple accounts. Excluded: one key, one account.
* Model-specific pools: none exist. All models share one pool.
* `total_credits == 0`, or a missing or expired plan: no meter is emitted. The result is a failure payload; there is no fake 0% bar.

**Interface sufficiency:** the current `Provider` interface (`id`, `display_name`, `detect()`, `fetch_usage()`, `ProviderError`) and the ADR-0012 meter schema are **sufficient**. A MiMo provider is a small adapter: one GET, one meter, a plan string. It needs no schema change, no new auth framework, and no refresh logic.

## 5. Feasibility verdict: **CONDITIONAL GO**

Evidence for GO:

* An **official, documented** quota endpoint exists and authenticates with the user's existing `tp-` key. [V]
* It returns total, used, and remaining credits plus a UTC period end, which maps cleanly onto one `Credits` meter with a `resetAt`. [V][O]
* A live read-only call on this account returned the documented shape. [O]
* Reading the key is read-only, with no refresh or rotation. There is no dashboard scraping and no cookie handling.
* Open-source precedent exists: CodexBar PR #5138 uses the same official endpoint. [T]

Conditions that need an owner decision before authorization:

1. Which credential source to use (env var, KWallet per ADR-0009, or both). See Q2.
2. How to handle the region (configured, or probing `sgp`, `cn`, and `ams`). See Q3.
3. Whether to accept the terms-of-use reading in §3. See Q5.
4. How to present `resetAt` for annual plans, where it is expiry or renewal rather than a refill. See Q4.

## 6. Proposed Stage 4 / Phase 12 contract — **PROPOSAL, NOT AUTHORIZED**

> The owner has not authorized this. Do not create `tasks/phase-12-*.md`, and do not edit `TASKS.md` or `PHASES.md`, until the owner explicitly authorizes Stage 4 / Phase 12.

**Goal.** Add a `mimo` provider that shows the remaining Xiaomi MiMo Token Plan credits as one ordered meter, using the official `GET /v1/platform/token_plan` endpoint and the user's existing `tp-` key, read-only.

**Scope.**

* `providers/mimo.py`, a small adapter: `id = "mimo"`, display name `Xiaomi MiMo`, `detect()` and `fetch_usage()`, built with `project_ok`.
* Register it in the explicit `PROVIDERS` registry.
* Credential source as decided in Q2. The proposed default is read-only `XIAOMI_API_KEY` / `MIMO_API_KEY` from the environment, with an optional user-supplied key in KWallet (`Horizon/mimo/token-plan-key`) through the existing ADR-0009 pattern and an `ai-usage auth mimo set|status|clear` command that mirrors StepFun. The key is never accepted as a CLI flag.
* Region as decided in Q3. Proposed: an optional `MIMO_REGION` (`cn|sgp|ams`) or setting. If none is set, probe `sgp`, `cn`, then `ams`, and stop at the first 200. Cache only the **region name** (not the key) in normalized config or cache.
* One meter `Credits`: integer remaining percent from `remaining_credits/total_credits`, and `resetAt` = `period.end_at` as UTC ISO-8601 with `+00:00`.
* `plan` as decided in Q1.
* Error mapping: missing key → `auth_unavailable`. 401 `invalid_api_key` in every probed region → `auth_unavailable`. Network → `network_error`. Bad JSON or shape → the existing parse/upstream status. `total_credits <= 0` → error payload with no meter.
* Cache at `~/.cache/horizon/usage-mimo.json`, normalized fields only.
* Add the provider to the plasmoid's provider list, with no new UI component beyond what existing providers use.
* Docs: `docs/providers/mimo.md`, and updates to `docs/provider-contract.md` and `docs/security.md`. Write an ADR only if Q2 changes the credential rules.

**Exclusions.**

* Console or dashboard endpoints (`platform.xiaomimimo.com/api/v1/tokenPlan/*`), browser-cookie reading, SSO token minting, and any Xiaomi Account login flow.
* Pay-as-you-go balance, daily consumption, or bill endpoints. No absolute credit counts, spend, or cash.
* Inference calls of any kind, and any call that consumes credits.
* Team-edition seats, multiple keys, multiple accounts, and per-model breakdowns.
* Reading MiMo-Code's `auth.json` (unverified key name; deferred until verified).
* A new auth framework, shared-auth rewrite, or changes to other providers.
* A release or VERSION bump unless the owner asks for one separately.

**Risks.** See the list at the end of this section.

**Acceptance criteria.**

1. `ai-usage mimo` with a valid key returns `status=ok` and exactly one meter, labeled `Credits`, with `0 ≤ remainingPercent ≤ 100` equal to the documented formula, and `resetAt` matching `period.end_at` with a `+00:00` offset.
2. The compatibility fields equal the projections of `meters` (`project_ok`).
3. `plan` follows the owner's Q1 decision and is never an invented string.
4. A missing key gives `auth_unavailable` with a clear message and no traceback. A wrong key or region gives `auth_unavailable` after the probe policy runs.
5. `total_credits == 0` or a malformed body gives an error payload with no meter and no 0% bar.
6. The key never appears in stdout, stderr, cache, logs, docs, test fixtures, or process arguments. The `docs/security.md` secret-check is clean.
7. The collector makes no request other than `GET /v1/platform/token_plan` to `token-plan-{region}.xiaomimimo.com`.
8. The plasmoid shows the MiMo row with one bar and a reset, using existing components.
9. Existing provider tests pass unchanged. Watcher PASS, then explicit owner acceptance.

**Tests (all offline, with fabricated fixtures).**

* Parse fixtures: monthly (`lite`), annual (`lite:year`), compensation included, `remaining_credits = 0`, `total_credits = 0`, missing `quota`, missing `period`, and a malformed timestamp.
* Percent rounding and clamping at the boundaries (0, 0.5, 99.5, 100, and remaining > total).
* Converting `end_at` to ISO-8601 `+00:00`.
* Region probe: first-region 200; a 401 then a 200; all regions 401 → `auth_unavailable`; a network error during the probe → `network_error`, with no fall-through that hides it.
* Credential precedence (env vs KWallet) per Q2, and no key in the arguments of any spawned process.
* Error payloads omit `meters` (ADR-0012 item 8).
* Cache allowlist: no key and no raw upstream body.
* Registry: `mimo` is listed, and unknown ids still fail cleanly.
* One manual live run, recorded only in sanitized form.

### Risks

* **Region-bound keys:** a wrong region gives a 401 that looks like a bad key [O]. Probing also sends the key to the other regional hosts on Xiaomi's own domain.
* **Terms of use:** the official wording bans `tp-` key use in "automated scripts". A background quota poll could be read that way. Keep polling infrequent.
* **Plasma environment:** a key exported only in `~/.bashrc` may not reach the plasmoid. An env-only design may fail silently in the widget.
* **Annual plans:** `resetAt` is a renewal or expiry date up to a year away. Showing it as a "reset" can mislead users.
* **Incomplete spec:** the docs do not state the HTTP method, the full `plan_code` vocabulary, or the semantics of `period` for team or one-time plans.
* **New endpoint:** the endpoint is recent (after 2026-09-22, before 2026-11-19). Its path or fields may change.
* **Plaintext key on disk:** `~/.bashrc` (and MiMo-Code's `auth.json`) is outside Horizon's control. Horizon only reads it.
* **Off-peak multiplier:** the 0.8× rate makes the burn rate vary by time of day. It does not affect the percent shown.

## 7. Unresolved questions for the owner

1. **Plan string:** should `plan` be `null`, the raw `plan_code` (`lite:year`), or a mapping of the documented tier codes to Xiaomi's official tier names (`lite` → `Lite`, `:year` → `(annual)`)? Is a mapping from official tier names "inventing" a plan name?
2. **Credential source:** env var only (`XIAOMI_API_KEY` / `MIMO_API_KEY`), a KWallet user-supplied key (ADR-0009), or both with a defined precedence? Given the Plasma environment risk, is KWallet required?
3. **Region:** should it be a required setting, or auto-probed across `sgp`, `cn`, and `ams`, with only the region name cached? Is sending the key to all three Xiaomi hosts acceptable?
4. **Annual reset label:** is `resetAt` = `period.end_at` acceptable for annual plans, or should the meter omit `resetAt` (or the UI wording change) when the period is longer than about 31 days?
5. **Terms of use:** does the owner accept that an infrequent quota read through the official endpoint is allowed under Token Plan's "programming tools only" rule? What polling floor should apply (for example, at least 5 minutes)?
6. **Stage placement:** is this the first phase of a new Stage 4 ("additional providers"), or should it go elsewhere?
7. **MiMo-Code `auth.json`:** is it worth a later discovery to confirm whether MiMo-Code stores a `tp-` key there, or should it stay out of scope?

## Sources

Primary (Xiaomi):

* MiMo docs index: <https://mimo.mi.com>
* Query Token Plan Credits: <https://mimo.mi.com/docs/en-US/api/asset/credits-get> (raw: <https://mimo.mi.com/static/docs/api/asset/credits-get.md>)
* Token Plan pricing: <https://mimo.mi.com/static/docs/price/token-plan.md>
* Subscription: <https://mimo.mi.com/static/docs/tokenplan/Token%20Plan/subscription.md>
* FAQ, Plans & Pricing: <https://mimo.mi.com/static/docs/quick-start/faq/token-plan/Plans%26Pricing.md>
* FAQ, Usage & Quota: <https://mimo.mi.com/static/docs/quick-start/faq/token-plan/Usage%26Quota.md>
* FAQ, Validity & Expiry: <https://mimo.mi.com/static/docs/quick-start/faq/token-plan/Validity%26Expiry.md>
* MiMo-Code integration: <https://mimo.mi.com/static/docs/integration/mimo-code.md>
* MiMo-Code repo: <https://github.com/XiaomiMiMo/MiMo-Code>, issue #2495: <https://github.com/XiaomiMiMo/MiMo-Code/issues/2495>

Third-party:

* CodexBar issue #5124 / PR #5138: <https://github.com/steipete/CodexBar/issues/5124>, <https://github.com/steipete/CodexBar/pull/5138>
* OmniRoute issues #14834, #15753: <https://github.com/diegosouzapw/OmniRoute/issues/14834>, <https://github.com/diegosouzapw/OmniRoute/issues/15753>
* ai-usagebar issue #146: <https://github.com/akitaonrails/ai-usagebar/issues/146>
* hermes-quota-plugin PR #86: <https://github.com/rarf/hermes-quota-plugin/pull/86>
* omarchy-xiaomi-usage: <https://github.com/carlospp95/omarchy-xiaomi-usage>
* codingplanhub (aliases, retired models): <https://codingplanhub.com/coding-plan/mimo>
* codingplans.com (stale allowances): <https://codingplans.com/plans/xiaomi-mimo-token-plan/>
