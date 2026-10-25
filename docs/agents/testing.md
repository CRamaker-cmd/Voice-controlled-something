# Testing rules

- Run `cd backend && pytest -q` before and after every change. All green or it isn't done. Report the counts.
- New behaviour → test first (or same commit). Bug → failing regression test first, then the fix.
- Pyramid: unit tests for pure logic; integration tests (`@pytest.mark.integration`) for API + SQLite + worker with only the network edge faked (`httpx.MockTransport`, `FakeAI` in `tests/conftest.py`).
- Compute expected numbers by hand from fixtures (see comments in `test_api_integration.py`); never paste program output as the expectation.
- Test failure paths: AI down, source returns 503, malformed rows, empty period, future period, auth failure.
- Tests must be deterministic: inject the clock (`NOW` in conftest), no real network, no sleeps (inject `sleep`).
- A smoke test with the real server (`uvicorn` + `curl`) is cheap and catches wiring bugs `TestClient` can't; do it after API changes.
- Say what you could not test (real OFF/USDA/Anthropic endpoints, Android UI) — never imply coverage you don't have.
