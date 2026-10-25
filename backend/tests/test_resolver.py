import pytest

from macrovoice.ai import AIEstimate
from macrovoice.foods import FoodRepo
from macrovoice.parser import parse_chunk
from macrovoice.resolver import Resolver
from conftest import FakeAI


def resolve(conn, text, ai=None):
    return Resolver(FoodRepo(conn), ai).resolve(parse_chunk(text))


def test_package_unit_uses_package_size_and_brand_alias(seeded):
    r = resolve(seeded, "2 loaves of AH volkoren")
    assert (r.status, r.source, r.grams) == ("resolved", "db", 1600)
    assert (r.kcal, r.protein, r.carbs, r.fat) == (3840, 144, 640, 48)
    assert "Albert Heijn" in r.name


def test_grams_and_serving(seeded):
    r = resolve(seeded, "200 g Jumbo skyr")
    assert (r.grams, round(r.kcal, 1), round(r.protein, 1)) == (200, 126.0, 22.0)
    b = resolve(seeded, "2 bananas")
    assert (b.grams, round(b.kcal, 1)) == (240, 213.6)


def test_volume_is_flagged(seeded):
    assert resolve(seeded, "100 ml skyr").note == "volume counted as 1 ml = 1 g"


def test_unknown_food_without_ai_is_unresolved_not_invented(seeded):
    r = resolve(seeded, "200 g dragonfruit")
    assert r.status == "unresolved" and r.kcal is None and "not found" in r.note


def test_missing_serving_size_without_ai_is_unresolved(seeded):
    r = resolve(seeded, "2 slices of skyr")   # skyr has no serving size in the fixtures
    assert r.status == "unresolved" and "serving size" in r.note


def test_vague_amount_and_measure_go_to_ai(seeded):
    ai = FakeAI()
    assert resolve(seeded, "some pasta", ai).source == "ai"
    assert resolve(seeded, "2 tbsp peanut butter", ai).source == "ai"
    assert ai.calls == ["some pasta", "2 tbsp peanut butter"]


def test_vague_amount_without_ai_is_unresolved(seeded):
    assert resolve(seeded, "some pasta").status == "unresolved"


def test_ai_result_is_cached_and_reused_locally(seeded):
    ai = FakeAI(AIEstimate(identified=True, grams=250, kcal=500, protein=20, carbs=50, fat=20))
    first = resolve(seeded, "250 g pad thai", ai)
    assert first.source == "ai" and first.kcal == 500
    second = resolve(seeded, "100 g pad thai", ai)       # different amount, same food
    assert second.source == "db" and second.kcal == pytest.approx(200) and len(ai.calls) == 1


def test_ai_cache_learns_package_size(seeded):
    ai = FakeAI(AIEstimate(identified=True, grams=600, kcal=1200, protein=50, carbs=100, fat=60))
    resolve(seeded, "1 pak pizza", ai)
    again = resolve(seeded, "2 pak pizza", ai)
    assert again.source == "db" and again.grams == 1200 and len(ai.calls) == 1


def test_ai_failure_degrades_to_unresolved(seeded):
    r = resolve(seeded, "200 g dragonfruit", FakeAI(fail=True))
    assert r.status == "unresolved" and "AI unavailable" in r.note


def test_ai_unidentified_stays_unresolved_and_is_not_cached(seeded):
    ai = FakeAI(AIEstimate(identified=False, note="no idea"))
    assert resolve(seeded, "200 g blorf", ai).status == "unresolved"
    assert FoodRepo(seeded).search(["blorf"]) == []


def test_empty_food_name(seeded):
    assert resolve(seeded, "200 g").status == "unresolved"
