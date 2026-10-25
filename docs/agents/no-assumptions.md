# No-assumptions protocol

The owner's rule: **never assume anything; where something is unclear, no hallucination is allowed — prompt the owner.**

## When this applies (ask, don't proceed)
- A requirement has two plausible readings (e.g. "average" = per logged day or per calendar day).
- A fact about an external system you haven't observed (API field names, rate limits, licence terms, file URLs). Public docs you *read in this session* count; memory does not.
- A number that affects the user's data (portion sizes, densities, nutrient values, timezone, week start).
- Scope: adding a data source, a feature, a dependency, a permission, or anything outward-facing (network calls, publishing, scraping).
- Anything already listed in `docs/open-questions.md` that you'd be deciding by implementing.

## How to ask
1. One message, specific, with 2–4 concrete options and your recommendation + why. Don't ask what the code or docs already answer — check first.
2. Batch related questions. Don't block on trivia (naming, formatting): follow the existing style.
3. While waiting, do the parts that don't depend on the answer. Write the open question into `docs/open-questions.md`.
4. When answered: implement, record an ADR (or update the existing one), remove the question.

## What "no hallucination" means in code
- Missing data → `None`/`unresolved` with a reason, never a plausible-looking default.
- External response shapes you couldn't verify → parse defensively, drop what doesn't validate (`ingest/pipeline.sane`), and flag the gap in the ADR/README "not verified" list.
- AI output is always labelled (`source='ai'`, `note`), may answer `identified=false`, and is validated before use.
- In your own reports: state what ran, what didn't, and what you inferred. No "should work" for things you did not run.
