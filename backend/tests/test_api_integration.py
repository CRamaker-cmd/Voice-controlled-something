"""API integration: real SQLite file, real parser/resolver/stats, fake AI and fixed clock."""
import pytest
from fastapi.testclient import TestClient

from macrovoice.api import create_app
from conftest import NOW, FakeAI

pytestmark = pytest.mark.integration


def log(client, text, **extra):
    r = client.post("/entries", json={"text": text, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def test_single_post_logs_and_defaults_to_today(client):
    e = log(client, "2 loaves of Albert Heijn volkoren and 200 g Jumbo skyr")
    assert e["local_date"] == "2026-10-21"                       # default = today per the clock
    assert [i["status"] for i in e["items"]] == ["resolved", "resolved"]
    assert e["totals"]["kcal"] == pytest.approx(3966.0)          # 3840 bread + 126 skyr
    assert e["totals"]["protein"] == pytest.approx(166.0)
    day = client.get("/entries").json()
    assert day["date"] == "2026-10-21" and [x["id"] for x in day["entries"]] == [e["id"]]


def test_explicit_timestamp_lands_on_that_local_day(client):
    e = log(client, "200 g skyr", logged_at="2026-10-19T23:30:00+02:00")
    assert e["local_date"] == "2026-10-19"
    late_utc = log(client, "200 g skyr", logged_at="2026-10-19T23:30:00+00:00")   # 01:30 on the 20th in Amsterdam
    assert late_utc["local_date"] == "2026-10-20"


def test_day_week_month_stats_end_to_end(client):
    log(client, "200 g skyr", logged_at="2026-10-19T08:00:00+02:00")       # 126 kcal, Monday
    log(client, "200 g skyr", logged_at="2026-10-21T08:00:00+02:00")       # 126 kcal, Wednesday
    log(client, "2 bananas", logged_at="2026-10-05T08:00:00+02:00")        # 213.6 kcal, other week
    day = client.get("/stats/day").json()
    assert day["totals"]["kcal"] == 126.0 and day["days_logged"] == 1
    week = client.get("/stats/week").json()
    assert (week["start"], week["end"]) == ("2026-10-19", "2026-10-25")
    assert week["totals"]["kcal"] == 252.0 and week["avg_per_logged_day"]["kcal"] == 126.0
    assert week["avg_per_day"]["kcal"] == 84.0                              # 252 / 3 elapsed days
    month = client.get("/stats/month", params={"date": "2026-10-15"}).json()
    assert month["totals"]["kcal"] == pytest.approx(465.6) and month["days_logged"] == 3
    assert month["highest_day"]["kcal"] == 213.6


def test_unknown_item_is_unresolved_then_fixable(settings, seeded):
    client = TestClient(create_app(settings, ai=None, clock=lambda: NOW))   # no AI configured
    e = log(client, "200 g dragonfruit and 200 g skyr")
    assert [i["status"] for i in e["items"]] == ["unresolved", "resolved"]
    assert e["totals"]["unresolved_items"] == 1 and e["totals"]["kcal"] == 126.0
    assert client.get("/stats/day").json()["unresolved_items"] == 1

    fixed = client.put(f"/items/{e['items'][0]['id']}", json={"grams": 200, "kcal": 60, "protein": 1, "carbs": 14, "fat": 0.3}).json()
    assert fixed["items"][0]["status"] == "resolved" and fixed["items"][0]["source"] == "manual"
    assert fixed["totals"]["kcal"] == 186.0 and fixed["totals"]["unresolved_items"] == 0


def test_ai_fallback_is_cached_so_second_request_is_local(client, fake_ai):
    first = log(client, "250 g pad thai")
    assert first["items"][0]["source"] == "ai" and len(fake_ai.calls) == 1
    second = log(client, "250 g pad thai")
    assert second["items"][0]["source"] == "db" and len(fake_ai.calls) == 1
    assert second["items"][0]["kcal"] == pytest.approx(500)


def test_delete_entry_updates_stats(client):
    e = log(client, "200 g skyr")
    assert client.delete(f"/entries/{e['id']}").status_code == 204
    assert client.delete(f"/entries/{e['id']}").status_code == 404
    assert client.get("/stats/day").json()["totals"]["kcal"] == 0


def test_validation_errors(client):
    assert client.post("/entries", json={"text": ""}).status_code == 422
    assert client.post("/entries", json={"text": " , "}).status_code == 422
    assert client.put("/items/999", json={"kcal": 1, "protein": 1, "carbs": 1, "fat": 1}).status_code == 404
    assert client.put("/items/1", json={"kcal": -1, "protein": 1, "carbs": 1, "fat": 1}).status_code == 422
    assert client.get("/entries", params={"date": "nope"}).status_code == 422


def test_manual_food_then_log_it(client):
    r = client.post("/foods", json={"name": "Protein bar", "brand": "Acme", "kcal_100g": 380, "protein_100g": 33,
                                    "carbs_100g": 35, "fat_100g": 12, "serving_g": 60})
    assert r.status_code == 201 and r.json()["source"] == "manual"
    e = log(client, "2 acme protein bar")
    assert e["items"][0]["grams"] == 120 and e["items"][0]["kcal"] == pytest.approx(456)
    assert client.get("/foods/search", params={"q": "protein bar"}).json()[0]["brand"] == "Acme"


def test_auth_token_protects_everything_but_health(settings, seeded):
    from dataclasses import replace
    c = TestClient(create_app(replace(settings, api_token="s3cret"), clock=lambda: NOW))
    assert c.get("/health").status_code == 200
    assert c.get("/entries").status_code == 401
    assert c.get("/entries", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert c.get("/entries", headers={"Authorization": "Bearer s3cret"}).status_code == 200


def test_health_reports_ai_state(client, settings):
    assert client.get("/health").json() == {"status": "ok", "ai_enabled": True}
    assert TestClient(create_app(settings)).get("/health").json()["ai_enabled"] is False
