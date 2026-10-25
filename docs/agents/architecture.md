# Architecture (agent view)

```
Android app (Compose) ──HTTP/JSON──▶ FastAPI (backend/macrovoice/api.py) ──▶ SQLite (WAL)
   mic → SpeechRecognizer                │ entries.py  diary + corrections                ▲
   text box → POST /entries              │ resolver.py parse→lookup→AI→cache              │
                                         │ stats.py    day/week/month                     │
                                         └ ai.py       optional Anthropic fallback        │
Worker (macrovoice.worker) ── ingest/{off,usda}.py ── pipeline.py (sanity + upsert) ──────┘
```
- **Layering (dependencies point down):** `api` → `entries`/`stats`/`resolver` → `foods`/`parser`/`units`/`ai` → `db`. `ingest/*` → `foods`. Nothing imports `api`. The Android app only knows the JSON API.
- **Pure vs I/O:** `parser`, `units`, `stats.period_bounds`, `ingest/*.product_to_record` are pure → test them directly. I/O is injected: `create_app(settings, ai, clock)`, `OFFApiSource(client, sleep=…)`.
- **Data:** `foods` (per-100 g, unique `(source, source_id)`, FTS5 `foods_fts`, indexes on brand/category), `entries` (+`local_date` index), `entry_items` (status resolved/unresolved), `ingest_runs`. Schema changes = new entry in `db.MIGRATIONS`, never edit an old one.
- **Source rank** when several foods match: manual > off/usda > ai.
- **Performance rules:** lookups go through FTS/indexes (check with `EXPLAIN QUERY PLAN`); bulk writes use one transaction (`upsert_many`); the request path never calls the network unless the local lookup failed.
- **Reliability rules:** AI/network failure never fails a log request (item becomes `unresolved`); worker failures are recorded in `ingest_runs` and the loop continues; data from outside is validated before storage.
