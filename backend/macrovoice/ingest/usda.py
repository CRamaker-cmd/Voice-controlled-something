"""USDA FoodData Central (public domain; free API key at https://fdc.nal.usda.gov/api-key-signup)."""
from __future__ import annotations

import time
from typing import Callable, Iterator

import httpx

from ..foods import FoodRecord

LIST_URL = "https://api.nal.usda.gov/fdc/v1/foods/list"
# nutrient numbers: 208 energy (kcal), 203 protein, 205 carbohydrate, 204 total fat
_NUTRIENTS = {"208": "kcal", "203": "protein", "205": "carbs", "204": "fat"}


def _nutrients(food: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for n in food.get("foodNutrients") or []:
        number = str(n.get("number") or n.get("nutrientNumber") or (n.get("nutrient") or {}).get("number") or "")
        key = _NUTRIENTS.get(number)
        amount = n.get("amount", n.get("value"))
        if key and isinstance(amount, (int, float)):
            out[key] = float(amount)
    return out


def food_to_record(food: dict) -> FoodRecord | None:
    n = _nutrients(food)
    if not food.get("fdcId") or not food.get("description") or len(n) < 4:
        return None
    category = food.get("foodCategory")
    if isinstance(category, dict):
        category = category.get("description")
    return FoodRecord(
        source="usda", source_id=str(food["fdcId"]), name=food["description"],
        brand=food.get("brandOwner"), category=category,
        kcal_100g=n["kcal"], protein_100g=n["protein"], carbs_100g=n["carbs"], fat_100g=n["fat"],
    )


class USDASource:
    def __init__(self, client: httpx.Client, api_key: str, data_types: str = "Foundation,SR Legacy",
                 pages: int = 20, page_size: int = 200, delay_s: float = 1.0,
                 sleep: Callable[[float], None] = time.sleep):
        self.client, self.api_key, self.data_types = client, api_key, data_types
        self.pages, self.page_size, self.delay_s, self.sleep = pages, page_size, delay_s, sleep

    def fetch(self) -> Iterator[FoodRecord | None]:
        for page in range(1, self.pages + 1):
            resp = self.client.get(LIST_URL, params={
                "api_key": self.api_key, "dataType": self.data_types,
                "pageSize": self.page_size, "pageNumber": page,
            })
            resp.raise_for_status()
            foods = resp.json()
            if not foods:
                return
            for f in foods:
                yield food_to_record(f)
            self.sleep(self.delay_s)
