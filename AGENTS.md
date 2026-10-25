# AGENTS.md — how to work in this repo

MacroVoice: say what you ate, roughly; get macros. Android app + self-hosted Python backend + food-ingestion worker.
Read this file fully, then load **only** the docs your task needs (table below). Don't read the whole repo.

## Non-negotiables
1. **Never assume. Never hallucinate.** If a requirement, data format, API shape, number or user preference is unclear, **stop and ask the owner** (use the question tool, or end your turn with the question). Do not pick a "reasonable default" silently. Details and the exact protocol: `docs/agents/no-assumptions.md`.
2. **Prove it.** Nothing is "done" until tests ran and passed in this session. Say plainly what you could *not* verify. Never claim a real external API/Android behaviour you did not observe.
3. **Decisions are recorded.** Any non-trivial choice → an ADR in `docs/decisions/`. Before changing a past decision, follow `docs/agents/decisions.md`.
4. **Keep the README true.** Any change to setup, config, commands, API or architecture updates `README.md` in the same change (`docs/agents/readme-maintenance.md`).
5. **Don't invent data.** Nutrition values come from a source, the user, or a flagged AI estimate. Unknown stays unknown (`unresolved`).

## Where to look (context map)
| You are about to… | Read first |
|---|---|
| Understand the system | `README.md`, `docs/agents/architecture.md` |
| Change behaviour or a past choice | `docs/decisions/README.md` → the relevant ADR, `docs/open-questions.md` |
| Write/modify backend code | `docs/agents/code-quality.md`, `docs/agents/testing.md` |
| Add a food source | `backend/macrovoice/ingest/off.py` (pattern), ADR 0006 |
| Touch parsing/units/resolution | ADR 0005, ADR 0007, `backend/tests/test_parser.py`, `test_resolver.py` |
| Touch stats/dates | ADR 0009, `backend/tests/test_stats.py` |
| Touch the Android app | `app/` is a thin client; logic belongs in the backend (ADR 0001, 0008) |

## Commands
```
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
pytest -q                      # all tests (<2 s)
pytest -m integration -q       # integration only
uvicorn macrovoice.server:app --reload
python -m macrovoice.worker off-api
```
The Android module needs Android Studio / SDK (not available in the cloud sandbox): `./gradlew test` from the repo root once a wrapper exists.

## Working method
- Context efficiency: start from this file and the map above; use grep/glob for targeted lookups; read ADRs by number, not all. Prefer reading a test to learn behaviour over reading implementation.
- Small, reviewable changes: one concern per commit; tests in the same commit as the behaviour.
- Branch/PR: work on a branch, open a PR, never push secrets (`.env` is git-ignored).
