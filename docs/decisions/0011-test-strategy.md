# 0011 — Test strategy
**Status:** accepted
**Decision:** Pure logic (parser, units, stats SQL, OFF/USDA mapping, FTS behaviour) has unit tests. Integration tests (`pytest -m integration`) run the real FastAPI app on a real temporary SQLite file with a fixed clock; only the *network edge* is faked (`httpx.MockTransport` for Open Food Facts / USDA / Anthropic, `FakeAI` for the resolver). Every bug fix adds a regression test first. Expected numbers in tests are computed by hand from fixture data, never copied from program output.
**Why:** Fast (<2 s), deterministic, no network or keys, yet exercises the same code paths as production.
**Known gap:** The real Open Food Facts / USDA / Anthropic endpoints and the Android app were **not** exercised from the authoring sandbox (network blocked, no Android SDK). Response shapes follow the public docs; the first real run of each worker job must be checked (README → "First real run checklist").
