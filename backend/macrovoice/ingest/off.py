"""Open Food Facts (ODbL; https://world.openfoodfacts.org): packaged products incl. Dutch brands."""
from __future__ import annotations

import gzip
import json
import time
from typing import Callable, Iterator

import httpx

from ..foods import FoodRecord

SEARCH_URL = "https://world.openfoodfacts.org/api/v2/search"
FIELDS = ("code,product_name,product_name_nl,product_name_en,generic_name,brands,categories_tags,"
          "nutriments,serving_quantity,product_quantity,countries_tags")
USER_AGENT = "MacroVoice/0.1 (self-hosted personal food diary)"


def _num(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def product_to_record(p: dict) -> FoodRecord | None:
    n = p.get("nutriments") or {}
    kcal = _num(n.get("energy-kcal_100g"))
    if kcal is None and _num(n.get("energy_100g")) is not None:   # energy_100g is kJ
        kcal = _num(n["energy_100g"]) / 4.184
    protein, carbs, fat = (_num(n.get(k)) for k in ("proteins_100g", "carbohydrates_100g", "fat_100g"))
    name = next((p[k].strip() for k in ("product_name", "product_name_nl", "product_name_en", "generic_name")
                 if isinstance(p.get(k), str) and p[k].strip()), None)
    if not p.get("code") or name is None or None in (kcal, protein, carbs, fat):
        return None
    brand = next((b.strip() for b in (p.get("brands") or "").split(",") if b.strip()), None)
    cats = p.get("categories_tags") or []
    category = cats[-1].split(":", 1)[-1] if cats else None
    serving, package = _num(p.get("serving_quantity")), _num(p.get("product_quantity"))
    return FoodRecord(
        source="off", source_id=str(p["code"]), name=name, brand=brand, category=category,
        kcal_100g=kcal, protein_100g=protein, carbs_100g=carbs, fat_100g=fat,
        serving_g=serving if serving and serving > 0 else None,
        package_g=package if package and package > 0 else None,
    )


class OFFApiSource:
    """Paged search API, most-scanned products first. OFF limits search to ~10 requests/minute."""

    def __init__(self, client: httpx.Client, country: str = "netherlands", pages: int = 50,
                 page_size: int = 100, delay_s: float = 6.5, sleep: Callable[[float], None] = time.sleep):
        self.client, self.country, self.pages, self.page_size = client, country, pages, page_size
        self.delay_s, self.sleep = delay_s, sleep

    def fetch(self) -> Iterator[FoodRecord | None]:
        for page in range(1, self.pages + 1):
            resp = self.client.get(SEARCH_URL, headers={"User-Agent": USER_AGENT}, params={
                "countries_tags_en": self.country, "fields": FIELDS, "page_size": self.page_size,
                "page": page, "sort_by": "unique_scans_n",
            })
            resp.raise_for_status()
            products = resp.json().get("products", [])
            if not products:
                return
            for p in products:
                yield product_to_record(p)
            self.sleep(self.delay_s)


class OFFDumpSource:
    """Bulk import from the official JSONL dump (download it first, see README)."""

    def __init__(self, path: str, country_tag: str = "en:netherlands"):
        self.path, self.country_tag = path, country_tag

    def fetch(self) -> Iterator[FoodRecord | None]:
        with gzip.open(self.path, "rt", encoding="utf-8") as fh:
            for line in fh:
                try:
                    p = json.loads(line)
                except json.JSONDecodeError:
                    yield None
                    continue
                if self.country_tag in (p.get("countries_tags") or []):
                    yield product_to_record(p)
