# 0004 — Self-hosted backend: Python + FastAPI + SQLite (FTS5)
**Status:** accepted
**Context:** A small home server must host the food database, the ingestion worker, the diary and the stats. The user suggested the DB need not be relational but needs indexes (e.g. on brand and type).
**Decision:** Python 3.11+, FastAPI, a single SQLite file (WAL mode), FTS5 for text search, ordinary B-tree indexes on `brand` (NOCASE) and `category`, `entries.local_date`.
**Why:**
- *SQLite over a document DB:* the data is small (hundreds of thousands of rows), single-user, and queried by text + brand + category + date ranges, which SQLite does well. Zero administration, one file to back up, runs on anything. FTS5 gives ranked full-text search without a separate search server. The product data is effectively one flat table, so we are not paying for relational complexity; the diary needs `SUM … GROUP BY date`, which is exactly what SQL is for.
- *Python:* the ingestion/parsing work is text-heavy, the ecosystem for HTTP/data is strongest, and the API and worker share one code base and one test suite.
- *API and worker as two processes, one image:* the worker can be slow/rate-limited without affecting the API; WAL mode lets both use the file.
**Consequences:** One writer at a time (fine for one user). Schema changes go through numbered migrations in `db.py`. If we ever need multi-user or heavy concurrency, move to Postgres (the SQL is plain).
**Revisit when:** More than one user, or write contention appears in `ingest_runs` / logs.
