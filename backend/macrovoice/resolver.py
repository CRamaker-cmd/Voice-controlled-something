"""Turn a ParsedItem into macros: local database first, AI fallback second, never a guess."""
from __future__ import annotations

from dataclasses import dataclass

from .ai import AIError, AIEstimator
from .foods import Food, FoodRecord, FoodRepo, tokenize
from .parser import ParsedItem
from .units import UnitKind, to_grams

_STOPWORDS = {"of", "van", "the", "de", "het", "a", "an", "een"}
_ALIASES = {("ah",): ("albert", "heijn"), ("albert", "heijn"): ("ah",)}


@dataclass(frozen=True)
class ResolvedItem:
    name: str
    amount_text: str
    status: str                      # resolved | unresolved
    source: str                      # db | ai | unresolved
    grams: float | None = None
    kcal: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    food_id: int | None = None
    note: str | None = None


def _query_variants(tokens: list[str]) -> list[list[str]]:
    variants = [tokens]
    for src, dst in _ALIASES.items():
        n = len(src)
        for i in range(len(tokens) - n + 1):
            if tuple(tokens[i:i + n]) == src:
                variants.append(tokens[:i] + list(dst) + tokens[i + n:])
    return variants


def _amount_text(p: ParsedItem) -> str:
    if p.quantity is None:
        return p.vague_reason or "unclear amount"
    q = f"{p.quantity:g}"
    return f"{q} {p.unit_text}" if p.unit_text else q


class Resolver:
    def __init__(self, foods: FoodRepo, ai: AIEstimator | None = None):
        self.foods = foods
        self.ai = ai

    # -- local ---------------------------------------------------------------------------------
    def _find(self, p: ParsedItem) -> Food | None:
        tokens = [t for t in tokenize(p.food_text) if t not in _STOPWORDS]
        for variant in _query_variants(tokens):
            hits = self.foods.search(variant, limit=1)
            if hits:
                return hits[0]
        return None

    def _from_food(self, p: ParsedItem, food: Food) -> ResolvedItem | str:
        grams, reason = to_grams(p.quantity, p.unit_kind, p.unit_factor, food.serving_g, food.package_g)
        if grams is None:
            return reason or "cannot derive grams"
        k = grams / 100.0
        label = f"{food.brand} {food.name}" if food.brand and food.brand.lower() not in food.name.lower() else food.name
        note = "volume counted as 1 ml = 1 g" if p.unit_kind is UnitKind.VOLUME else None
        return ResolvedItem(
            name=label, amount_text=_amount_text(p), status="resolved", source="db", grams=grams,
            kcal=food.kcal_100g * k, protein=food.protein_100g * k, carbs=food.carbs_100g * k,
            fat=food.fat_100g * k, food_id=food.id, note=note,
        )

    # -- AI ------------------------------------------------------------------------------------
    def _from_ai(self, p: ParsedItem, why: str) -> ResolvedItem:
        unresolved = ResolvedItem(
            name=p.food_text or p.raw, amount_text=_amount_text(p), status="unresolved",
            source="unresolved", note=why,
        )
        if self.ai is None:
            return unresolved
        try:
            est = self.ai.estimate(p.raw)
        except AIError as e:
            return ResolvedItem(**{**unresolved.__dict__, "note": f"{why}; AI unavailable: {e}"})
        if not est.identified:
            return ResolvedItem(**{**unresolved.__dict__, "note": f"{why}; AI could not identify it. {est.note}".strip()})

        food_id = self._cache(p, est)
        return ResolvedItem(
            name=p.food_text or p.raw, amount_text=_amount_text(p), status="resolved", source="ai",
            grams=est.grams, kcal=est.kcal, protein=est.protein, carbs=est.carbs, fat=est.fat,
            food_id=food_id, note=f"AI estimate. {est.note}".strip(),
        )

    def _cache(self, p: ParsedItem, est) -> int | None:
        """Store the AI result per 100 g so the same food resolves locally next time."""
        if not p.food_text:
            return None
        per = 100.0 / est.grams
        qty = p.quantity or 0
        serving = est.grams / qty if p.unit_kind is UnitKind.SERVING and qty else None
        package = est.grams / qty if p.unit_kind is UnitKind.PACKAGE and qty else None
        return self.foods.upsert(FoodRecord(
            source="ai", source_id=" ".join(tokenize(p.food_text)), name=p.food_text,
            kcal_100g=est.kcal * per, protein_100g=est.protein * per, carbs_100g=est.carbs * per,
            fat_100g=est.fat * per, serving_g=serving, package_g=package,
        ))

    # -- entry point ---------------------------------------------------------------------------
    def resolve(self, p: ParsedItem) -> ResolvedItem:
        if not p.food_text:
            return ResolvedItem(name=p.raw, amount_text=_amount_text(p), status="unresolved",
                                source="unresolved", note="no food name found")
        if p.quantity is None:
            return self._from_ai(p, p.vague_reason or "amount is vague")
        if p.unit_kind is UnitKind.MEASURE:
            return self._from_ai(p, "this measure has no fixed weight")

        food = self._find(p)
        if food is None:
            return self._from_ai(p, "not found in the food database")
        result = self._from_food(p, food)
        if isinstance(result, str):
            return self._from_ai(p, f"found '{food.name}' but {result}")
        return result
