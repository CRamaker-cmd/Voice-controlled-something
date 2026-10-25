"""Unit vocabulary (English + Dutch) and conversion of a quantity to grams.

Only conversions that need no guess are done here. Culinary measures (tbsp, cup, bowl, ...) have
no fixed weight, so they are *not* converted locally; they are routed to the AI fallback or left
unresolved. Volumes are counted as 1 ml = 1 g (documented approximation, ADR 0007).
"""
from __future__ import annotations

from enum import Enum


class UnitKind(Enum):
    MASS = "mass"
    VOLUME = "volume"
    SERVING = "serving"      # slice, piece, portion: weight comes from the product's serving size
    PACKAGE = "package"      # loaf, pack, bottle: weight comes from the product's package size
    MEASURE = "measure"      # tbsp, cup, bowl, handful: no fixed weight


def _u(kind: UnitKind, factor: float, *names: str) -> dict[str, tuple[UnitKind, float]]:
    return {n: (kind, factor) for n in names}


UNITS: dict[str, tuple[UnitKind, float]] = {
    **_u(UnitKind.MASS, 1, "g", "gr", "gram", "grams", "gramme", "grammes"),
    **_u(UnitKind.MASS, 1000, "kg", "kilo", "kilos", "kilogram", "kilograms"),
    **_u(UnitKind.VOLUME, 1, "ml", "milliliter", "milliliters", "millilitre", "millilitres"),
    **_u(UnitKind.VOLUME, 10, "cl", "centiliter", "centiliters"),
    **_u(UnitKind.VOLUME, 100, "dl", "deciliter", "deciliters"),
    **_u(UnitKind.VOLUME, 1000, "l", "liter", "liters", "litre", "litres"),
    **_u(UnitKind.SERVING, 1, "slice", "slices", "sneetje", "sneetjes", "snee", "piece", "pieces",
         "stuk", "stuks", "stukje", "stukjes", "serving", "servings", "portie", "porties"),
    **_u(UnitKind.PACKAGE, 1, "loaf", "loaves", "loafs", "brood", "broden", "pack", "packs",
         "package", "packages", "pak", "pakje", "pakjes", "pot", "potje", "fles", "flesje",
         "bottle", "bottles", "blik", "blikje", "can", "cans", "bak", "bakje", "tub", "carton",
         "pak", "zak", "zakje", "bag"),
    **_u(UnitKind.MEASURE, 1, "tbsp", "tablespoon", "tablespoons", "el", "eetlepel", "eetlepels",
         "tsp", "teaspoon", "teaspoons", "tl", "theelepel", "theelepels", "cup", "cups", "kop",
         "kopje", "glass", "glasses", "glas", "glazen", "bowl", "bowls", "kom", "kommetje",
         "handful", "handvol", "scoop", "scoops", "lepel", "spoon"),
}


def lookup_unit(token: str) -> tuple[UnitKind, float] | None:
    return UNITS.get(token.lower())


def to_grams(
    quantity: float,
    kind: UnitKind,
    factor: float,
    serving_g: float | None,
    package_g: float | None,
) -> tuple[float | None, str | None]:
    """Return (grams, None) or (None, reason-the-amount-cannot-be-derived)."""
    if kind in (UnitKind.MASS, UnitKind.VOLUME):
        return quantity * factor, None
    if kind is UnitKind.SERVING:
        if serving_g:
            return quantity * serving_g, None
        return None, "this product has no known serving size; say the amount in grams"
    if kind is UnitKind.PACKAGE:
        if package_g:
            return quantity * package_g, None
        return None, "this product has no known package size; say the amount in grams"
    return None, "this measure has no fixed weight; say the amount in grams"
