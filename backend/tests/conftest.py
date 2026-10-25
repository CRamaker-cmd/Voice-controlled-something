from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from macrovoice import db
from macrovoice.ai import AIEstimate, AIError
from macrovoice.api import create_app
from macrovoice.config import Settings
from macrovoice.foods import FoodRepo
from macrovoice.ingest.off import product_to_record
from macrovoice.ingest.pipeline import ingest

AMS = ZoneInfo("Europe/Amsterdam")
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=AMS)  # a Wednesday; its ISO week is Oct 19-25

OFF_PRODUCTS = [
    {"code": "1", "product_name": "Volkoren brood", "brands": "Albert Heijn",
     "categories_tags": ["en:breads", "en:wholemeal-breads"], "serving_quantity": "35", "product_quantity": "800",
     "nutriments": {"energy-kcal_100g": 240, "proteins_100g": 9, "carbohydrates_100g": 40, "fat_100g": 3}},
    {"code": "2", "product_name": "Skyr naturel", "brands": "Jumbo,Other",
     "categories_tags": ["en:skyr"], "product_quantity": 500,
     "nutriments": {"energy-kcal_100g": 63, "proteins_100g": 11, "carbohydrates_100g": 4, "fat_100g": 0.2}},
    {"code": "3", "product_name": "Banaan", "brands": "", "categories_tags": ["en:bananas"],
     "serving_quantity": 120, "nutriments": {"energy-kcal_100g": 89, "proteins_100g": 1.1,
                                             "carbohydrates_100g": 22.8, "fat_100g": 0.3}},
]


class FakeAI:
    """Deterministic stand-in for the Anthropic estimator; records every call."""

    def __init__(self, result: AIEstimate | None = None, fail: bool = False):
        self.calls: list[str] = []
        self.result = result or AIEstimate(identified=True, grams=250, kcal=500, protein=20, carbs=50, fat=20,
                                           note="generic equivalent")
        self.fail = fail

    def estimate(self, chunk: str) -> AIEstimate:
        self.calls.append(chunk)
        if self.fail:
            raise AIError("boom")
        return self.result


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(db_path=str(tmp_path / "t.db"), timezone="Europe/Amsterdam")


@pytest.fixture
def conn(settings):
    c = db.connect(settings.db_path)
    yield c
    c.close()


@pytest.fixture
def seeded(conn):
    ingest(conn, "off", (product_to_record(p) for p in OFF_PRODUCTS))
    return conn


@pytest.fixture
def fake_ai():
    return FakeAI()


@pytest.fixture
def client(settings, seeded, fake_ai):
    app = create_app(settings, ai=fake_ai, clock=lambda: NOW)
    return TestClient(app)
