# Code quality rules

- Match surrounding code: naming, comment density, idiom. Comments explain *why* (constraints, decisions), not what.
- Small functions with one reason to change; pure functions where possible; dependencies injected (clock, HTTP client, AI, sleep) so tests need no monkeypatching.
- Type-annotate public Python functions. No bare `except`; catch what you can handle and surface the rest.
- No speculative features, config flags or abstractions. Three similar lines beat a premature framework.
- Validate at boundaries (HTTP input via pydantic, external data via `sane`), trust internal calls.
- Secrets only via env vars; never log or commit them.
- Performance: measure before optimising; but never add an unindexed lookup on `foods`/`entries`, never do per-row commits in bulk paths.
- Reliability: every external call has a timeout and a failure path with a test.
- Android: no business logic in composables; keep parsing of API JSON in one file with a JVM unit test.
