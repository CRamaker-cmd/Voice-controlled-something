"""Ingestion worker integration: HTTP faked at the transport level, real SQLite and pipeline."""
import gzip
import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from macrovoice import db
from macrovoice.api import create_app
from macrovoice.foods import FoodRepo
from macrovoice.worker import run_job
from conftest import NOW, OFF_PRODUCTS

pytestmark = pytest.mark.integration


def off_transport(pages):
    seen = []

    def handler(req: httpx.Request):
        seen.append(req)
        page = int(req.url.params["page"])
        return httpx.Response(200, json={"products": pages[page - 1] if page <= len(pages) else []})
    return httpx.MockTransport(handler), seen


def test_off_api_job_paginates_stops_on_empty_and_is_polite(settings):
    transport, seen = off_transport([OFF_PRODUCTS[:2], OFF_PRODUCTS[2:] + [{"code": "bad", "product_name": "No macros"}]])
    sleeps = []
    stats = run_job("off-api", replace(settings, off_pages=10), httpx.Client(transport=transport), sleep=sleeps.append)
    assert (stats.stored, stats.skipped) == (3, 1)
    assert len(seen) == 3                                    # two data pages + the empty one that ends it
    assert seen[0].headers["user-agent"].startswith("MacroVoice") and seen[0].url.params["countries_tags_en"] == "netherlands"
    assert sleeps == [6.5, 6.5]                              # rate limit respected between pages


def test_rerunning_a_job_updates_instead_of_duplicating(settings):
    for kcal in (240, 250):
        changed = [dict(OFF_PRODUCTS[0], nutriments={**OFF_PRODUCTS[0]["nutriments"], "energy-kcal_100g": kcal})]
        transport, _ = off_transport([changed])
        run_job("off-api", settings, httpx.Client(transport=transport), sleep=lambda s: None)
    conn = db.connect(settings.db_path)
    repo = FoodRepo(conn)
    assert repo.count() == 1 and repo.search(["volkoren"])[0].kcal_100g == 250
    runs = conn.execute("SELECT stored, error FROM ingest_runs ORDER BY id").fetchall()
    assert [(r["stored"], r["error"]) for r in runs] == [(1, None), (1, None)]


def test_failed_job_is_recorded_and_raises(settings):
    transport = httpx.MockTransport(lambda r: httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        run_job("off-api", settings, httpx.Client(transport=transport), sleep=lambda s: None)
    row = db.connect(settings.db_path).execute("SELECT error, finished_at FROM ingest_runs").fetchone()
    assert "503" in row["error"] and row["finished_at"]


def test_off_dump_job_filters_by_country_and_skips_garbage(settings, tmp_path):
    dump = tmp_path / "off.jsonl.gz"
    foreign = dict(OFF_PRODUCTS[1], code="77", countries_tags=["en:france"])
    dutch = dict(OFF_PRODUCTS[0], countries_tags=["en:netherlands", "en:belgium"])
    with gzip.open(dump, "wt") as fh:
        fh.write(json.dumps(dutch) + "\n{not json\n" + json.dumps(foreign) + "\n")
    stats = run_job("off-dump", settings, dump_path=str(dump))
    assert (stats.stored, stats.skipped) == (1, 1)
    assert FoodRepo(db.connect(settings.db_path)).search(["volkoren"])


def test_usda_job_handles_both_nutrient_shapes(settings):
    foods = [
        {"fdcId": 11, "description": "Bananas, raw", "foodCategory": "Fruits",
         "foodNutrients": [{"number": "208", "amount": 89}, {"number": "203", "amount": 1.1},
                           {"number": "205", "amount": 22.8}, {"number": "204", "amount": 0.3}]},
        {"fdcId": 12, "description": "Apple", "foodCategory": {"description": "Fruits"},
         "foodNutrients": [{"nutrientNumber": "208", "value": 52}, {"nutrientNumber": "203", "value": 0.3},
                           {"nutrientNumber": "205", "value": 14}, {"nutrientNumber": "204", "value": 0.2}]},
        {"fdcId": 13, "description": "Missing fat", "foodNutrients": [{"number": "208", "amount": 1}]},
    ]
    handler = lambda r: httpx.Response(200, json=foods if r.url.params["pageNumber"] == "1" else [])
    stats = run_job("usda", replace(settings, usda_api_key="k"), httpx.Client(transport=httpx.MockTransport(handler)),
                    sleep=lambda s: None)
    assert (stats.stored, stats.skipped) == (2, 1)


def test_job_validation(settings):
    with pytest.raises(ValueError, match="USDA_API_KEY"):
        run_job("usda", settings)
    with pytest.raises(ValueError, match="dump file"):
        run_job("off-dump", settings)
    with pytest.raises(ValueError, match="unknown job"):
        run_job("nope", settings)


def test_end_to_end_worker_feeds_the_api(settings):
    """Empty DB -> worker ingests -> user speaks -> macros come from the local DB, AI never called."""
    transport, _ = off_transport([OFF_PRODUCTS])
    run_job("off-api", settings, httpx.Client(transport=transport), sleep=lambda s: None)

    class ExplodingAI:
        def estimate(self, chunk):
            raise AssertionError("AI must not be consulted for foods the worker already stored")

    client = TestClient(create_app(settings, ai=ExplodingAI(), clock=lambda: NOW))
    e = client.post("/entries", json={"text": "2 loaves of AH volkoren"}).json()
    assert e["items"][0]["source"] == "db" and e["totals"]["kcal"] == pytest.approx(3840)
