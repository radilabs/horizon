# Decision Records

`decisions/` stores architectural and product decisions that future work must respect.

Create a decision record only when a future agent or phase needs to know a choice, constraint, rejection, or tradeoff.

Do not create decisions merely to narrate implementation.

Do not silently rewrite accepted historical records. Supersede them with a new record when needed.

## Format

Each decision should include:

- **Status:** Proposed | Accepted | Superseded
- **Context:** why a decision was required
- **Decision:** what was chosen
- **Consequences:** what becomes easier, harder, allowed, or constrained

Use sequential filenames such as `0010-example-decision.md`.
