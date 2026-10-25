# Working with decisions

**Find:** `docs/decisions/README.md` is the index; each ADR has context, decision, why, consequences, *revisit when*. Unconfirmed ones are listed in `docs/open-questions.md`.

**Follow:** Treat accepted ADRs as constraints. Don't silently work around one.

**Challenge (allowed, but explicit):** Adjust a decision only when (a) its *revisit when* condition has occurred, (b) evidence shows it's wrong (cite the test, data, or failure), or (c) the owner asks. Then:
1. Tell the owner: which ADR, what evidence, proposed change, impact. **Wait for approval** (no-assumptions protocol).
2. Add a new ADR; mark the old one `superseded by NNNN`; update the index.
3. Update tests, README, and `docs/agents/*` that mention it.

**Create:** Any choice a future reader might question (library, data model, semantics, trade-off) gets an ADR in the same change. Number sequentially. Keep to one screen.
