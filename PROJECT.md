
## General Information

**Project Horizon desired plan (ready to copy into tasks / issues):**

Build a **KDE Plasma widget (plasmoid)** that acts as an “AI agent usage panel”.

**Core goal**  
Show remaining limits / quotas for the AI coding tools and subscriptions I actually use, in a clean Plasma-native panel (progress bars, remaining %, reset timers, plan name, optional daily/model breakdowns). Inspired by the Omarchy Quattro agent panel, but made for KDE Plasma instead of Omarchy.

**Priority providers (start here)**  
1. **Codex** – ChatGPT Plus plan (individual, *not* organization). Use session/token or local auth method (same style existing trackers use).  
2. **Cursor** – individual account (unofficial / local + internal endpoints).  
3. **StepFun Step Plan** – credit-based subscription (unofficial dashboard endpoints).

**Later / nice-to-have**  
- Other LLM providers I use  
- Auto-detection of active subscriptions where possible  
- Local caching + background refresh  
- Notifications when limits are getting low

**Technical notes**  
- Plasma side: QML plasmoid (compact representation + full popup panel).  
- Data side: mostly unofficial/session-based for the three priority providers (no clean public org-style APIs for my Plus Codex / Cursor / Step Plan).  
- Prefer wrapping or adapting existing open-source trackers where they already work, rather than reinventing auth from scratch.

**Global rules**

0. A phase is an immutable execution boundary. Tasks may be refined inside it, but its goal, scope, exclusions, and handoff contract may not be changed during implementation. Any discovered work outside the contract is recorded as deferred work, not implemented.