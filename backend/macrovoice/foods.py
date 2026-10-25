"""Food repository: per-100g nutrition records with full-text + brand/category indexes."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

# Lower = preferred when several foods match equally well.
SOURCE_RANK = {"manual": 0, "off": 1, "usda": 1, "ai": 2}


@dataclass(frozen=True)
class FoodRecord:
    source: str
    source_id: str
    name: str
    kcal_100g: float
    protein_100g: float
    carbs_100g: float
    fat_100g: float
    brand: str | None = None
    category: str | None = None
    serving_g: float | None = None
    package_g: float | None = None


@dataclass(frozen=True)
class Food(FoodRecord):
    id: int = 0


def _row_to_food(r: sqlite3.Row) -> Food:
    return Food(
        id=r["id"], source=r["source"], source_id=r["source_id"], name=r["name"],
        brand=r["brand"], category=r["category"], kcal_100g=r["kcal_100g"],
        protein_100g=r["protein_100g"], carbs_100g=r["carbs_100g"], fat_100g=r["fat_100g"],
        serving_g=r["serving_g"], package_g=r["package_g"],
    )


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def stem(tok: str) -> str:
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    if len(tok) > 4 and tok.endswith("en"):
        return tok[:-2]
    return tok


def fts_query(tokens: list[str]) -> str:
    """AND of all tokens; each token matches by prefix, also in a simple singular form."""
    groups = []
    for t in tokens:
        s = stem(t)
        groups.append(f'"{t}"*' if s == t else f'("{t}"* OR "{s}"*)')
    return " AND ".join(groups)


class FoodRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    _UPSERT = """
        INSERT INTO foods (source, source_id, name, brand, category, kcal_100g, protein_100g,
                           carbs_100g, fat_100g, serving_g, package_g, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT (source, source_id) DO UPDATE SET
            name=excluded.name, brand=excluded.brand, category=excluded.category,
            kcal_100g=excluded.kcal_100g, protein_100g=excluded.protein_100g,
            carbs_100g=excluded.carbs_100g, fat_100g=excluded.fat_100g,
            serving_g=excluded.serving_g, package_g=excluded.package_g,
            updated_at=excluded.updated_at
        RETURNING id
    """

    def _params(self, r: FoodRecord) -> tuple:
        now = datetime.now(timezone.utc).isoformat()
        return (r.source, r.source_id, r.name, r.brand, r.category, r.kcal_100g, r.protein_100g,
                r.carbs_100g, r.fat_100g, r.serving_g, r.package_g, now)

    def upsert(self, rec: FoodRecord) -> int:
        with self.conn:
            return self.conn.execute(self._UPSERT, self._params(rec)).fetchone()[0]

    def upsert_many(self, recs: Iterable[FoodRecord]) -> int:
        n = 0
        with self.conn:
            for r in recs:
                self.conn.execute(self._UPSERT, self._params(r))
                n += 1
        return n

    def get(self, food_id: int) -> Food | None:
        r = self.conn.execute("SELECT * FROM foods WHERE id = ?", (food_id,)).fetchone()
        return _row_to_food(r) if r else None

    def search(self, tokens: list[str], limit: int = 10) -> list[Food]:
        """Foods whose name/brand/category contain ALL tokens, best first."""
        if not tokens:
            return []
        rows = self.conn.execute(
            """
            SELECT f.*, bm25(foods_fts) AS score
            FROM foods_fts JOIN foods f ON f.id = foods_fts.rowid
            WHERE foods_fts MATCH ?
            ORDER BY CASE f.source WHEN 'manual' THEN 0 WHEN 'off' THEN 1 WHEN 'usda' THEN 1
                                   WHEN 'ai' THEN 2 ELSE 3 END,
                     score
            LIMIT ?
            """,
            (fts_query(tokens), limit),
        ).fetchall()
        return [_row_to_food(r) for r in rows]

    def by_brand(self, brand: str, limit: int = 50) -> list[Food]:
        rows = self.conn.execute(
            "SELECT * FROM foods WHERE brand = ? COLLATE NOCASE LIMIT ?", (brand, limit)
        ).fetchall()
        return [_row_to_food(r) for r in rows]

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
