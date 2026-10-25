# MacroVoice

Say what you ate, roughly — *"2 loaves of Albert Heijn volkoren and 200 g Jumbo skyr"* — and it is logged to today with
calories, protein, carbs and fat. Day / week / month totals, averages and stats.

* **Android app** (Kotlin + Compose): speech → text → one HTTP call. Thin client.
* **Backend** (Python + FastAPI + SQLite): rule-based parser, local food database, optional AI fallback, diary, stats.
* **Worker**: fills the food database from Open Food Facts and USDA FoodData Central.

Why it is built this way: [`docs/decisions/`](docs/decisions/README.md). Open questions for the owner: [`docs/open-questions.md`](docs/open-questions.md). Rules for coding agents: [`AGENTS.md`](AGENTS.md).

## How a sentence becomes macros
```
"2 loaves of AH volkoren, 200 g Jumbo skyr"
  → split on , ; & and/en/plus            → ["2 loaves of AH volkoren", "200 g Jumbo skyr"]
  → parse quantity + unit + food          → 2 × loaf "ah volkoren" ; 200 g "jumbo skyr"
  → FTS5 lookup in `foods` (brand aliases: AH ↔ Albert Heijn)
  → grams: g/kg direct · loaf/pack = product package size · slice/piece = product serving size
  → macros = per-100 g × grams / 100
  → not found / vague amount / "tbsp"-type measure → AI fallback (if configured) → result cached as a food
  → still unknown → saved as `unresolved` (shown in red, not counted, fixable)
```
Details and reasoning: ADR [0005](docs/decisions/0005-local-first-ai-fallback.md), [0007](docs/decisions/0007-portion-and-unit-semantics.md).

## Repo layout
```
app/                       Android app (Compose). ApiClient/ApiJson = server contract, MainViewModel = state
backend/macrovoice/        api.py (routes) · entries.py (diary) · resolver.py · parser.py · units.py · stats.py
                           foods.py (FTS + indexes) · ai.py (Anthropic fallback) · db.py (schema+migrations)
                           worker.py + ingest/ (off.py, usda.py, pipeline.py)
backend/tests/             unit + integration tests (pytest)
docs/decisions/            ADRs        docs/agents/  agent rules        docs/open-questions.md
docker-compose.yml         api + worker on one server      .env.example
```

## Prerequisites
* Backend/worker: Python ≥ 3.11 (or Docker). SQLite with FTS5 (standard in CPython builds).
* App: Android Studio (Koala+), JDK 17, a phone/emulator with Google speech services (Android 8+).

## Run the backend
```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export MACROVOICE_API_TOKEN=change-me          # optional but recommended
uvicorn macrovoice.server:app --host 0.0.0.0 --port 8000
```
Or on the home server: `cp .env.example .env`, edit it, `docker compose up -d` (service `api` on :8000 and service `worker`; they share the SQLite volume).

## Fill the food database (worker)
```bash
python -m macrovoice.worker off-api            # Open Food Facts search API, most-scanned Dutch products first (~10 req/min limit respected)
python -m macrovoice.worker off-dump FILE.gz   # bulk: download openfoodfacts-products.jsonl.gz from https://world.openfoodfacts.org/data first
USDA_API_KEY=… python -m macrovoice.worker usda
python -m macrovoice.worker loop               # what the docker `worker` service runs: WORKER_JOBS every WORKER_INTERVAL_HOURS
```
Runs are logged in table `ingest_runs` (stored/skipped/error). Incomplete or implausible source rows are skipped, never repaired.
You can also add your own product any time: `POST /foods` (source `manual`, always preferred over scraped data).

## Run the app
Open the repo root in Android Studio (it creates the Gradle wrapper on first sync), run on a device, open **Settings** and enter the
server address (e.g. `http://192.168.1.20:8000`), the token, and the speech language. Tap the mic and speak — the sentence is recorded the moment recognition
finishes (or type and press send). Tabs: Day / Week / Month with ◀ ▶ navigation.

## Configuration (environment variables)
| Variable | Default | Meaning |
|---|---|---|
| `MACROVOICE_DB` | `data/macrovoice.db` | SQLite file (docker: `/data/macrovoice.db`) |
| `MACROVOICE_TZ` | `Europe/Amsterdam` | Timezone that decides which day an entry belongs to |
| `MACROVOICE_API_TOKEN` | unset | If set, all endpoints but `/health` need `Authorization: Bearer <token>` |
| `ANTHROPIC_API_KEY` | unset | Enables the AI fallback; without it unknown foods become `unresolved` |
| `MACROVOICE_AI_MODEL` | `claude-haiku-5-5` | Model used by the fallback |
| `USDA_API_KEY` | unset | Needed for the `usda` job |
| `WORKER_JOBS` | `off-api` | Comma list for `loop`: `off-api`, `usda` |
| `WORKER_INTERVAL_HOURS` | `168` | Pause between loop rounds |
| `OFF_PAGES` / `OFF_COUNTRY` | `50` / `netherlands` | Pages (100 products each) and country for `off-api` |

## API
All JSON. Auth header as above. Dates are `YYYY-MM-DD`; omitted `date` means today (server timezone).

| Method & path | Purpose |
|---|---|
| `GET /health` | `{"status":"ok","ai_enabled":bool}` (no auth) |
| `POST /entries` `{"text": "...", "logged_at"?: ISO-8601}` | Parse, resolve, store, return the entry (201). `logged_at` defaults to now. 422 if no food found. |
| `GET /entries?date=` | `{"date", "entries":[…]}` for one day |
| `DELETE /entries/{id}` | 204 / 404 |
| `PUT /items/{id}` `{"name"?, "grams"?, "kcal","protein","carbs","fat"}` | Manually set/fix an item (also resolves an unresolved one) |
| `GET /stats/day\|week\|month?date=` | Totals, `avg_per_logged_day`, `avg_per_day`, `macro_split`, `highest_day`, `lowest_day`, `unresolved_items`, `per_day[]` |
| `GET /foods/search?q=&limit=` | Look up foods in the local DB |
| `POST /foods` | Add a product (per-100 g values, optional `serving_g`, `package_g`) |

Example:
```bash
curl -H "Authorization: Bearer $T" -H 'content-type: application/json' \
     -d '{"text":"2 loaves of AH volkoren and 200 g Jumbo skyr"}' http://localhost:8000/entries
```
Entry item `status` is `resolved` or `unresolved`; `source` is `db`, `ai`, `manual` or `unresolved`. Semantics of weeks/averages: ADR [0009](docs/decisions/0009-dates-weeks-averages.md).

## Tests
```bash
cd backend && pytest -q                 # 73 tests, ~1 s: units + integration (real SQLite, fake HTTP/AI, fixed clock)
pytest -m integration -q                # integration only
./gradlew test                          # Android JVM tests (ApiJsonTest) — needs Android SDK; not yet run, see below
```
Strategy: ADR [0011](docs/decisions/0011-test-strategy.md).

## Data sources & licences
* **Open Food Facts** — ODbL; attribute "Open Food Facts contributors" if you redistribute data. Use a meaningful User-Agent (done) and respect rate limits (done).
* **USDA FoodData Central** — public domain.
* AI estimates (`source='ai'`) are labelled in the API and the app and are cached per 100 g.

## Known limitations / not verified yet
* **Never run against the real services:** the sandbox this was written in blocks Open Food Facts, USDA and Anthropic. Request/response shapes follow their public documentation and are tested against fakes only (parameters like `countries_tags_en`, `sort_by=unique_scans_n`, USDA `/foods/list` shape).
* **The Android app has not been compiled or run** (no Android SDK in the sandbox). Expect a first-sync fix or two. `ApiJsonTest` mirrors real backend JSON.
* No Gradle wrapper is committed; Android Studio generates it.
* Only kcal/protein/carbs/fat; no goals; single user; liquids use 1 ml = 1 g; parser splits on "and" (so "mac and cheese" becomes two items). See open questions.
* Cleartext HTTP is enabled in the app for LAN use; put the server behind HTTPS/VPN if reachable from outside.

## First real run checklist
1. `docker compose up -d`; `curl localhost:8000/health`.
2. `python -m macrovoice.worker off-api` with `OFF_PAGES=2`; check `SELECT * FROM ingest_runs;` and `SELECT COUNT(*) FROM foods;`. If `stored=0`, inspect the API response shape/params.
3. `POST /entries` with a sentence using a product you know exists; compare the macros with the package label.
4. Set `ANTHROPIC_API_KEY`, log something exotic, confirm `source":"ai"` and that repeating it is `"db"`.
5. Build the app, set server URL + token, record by voice.
