import pytest

from macrovoice.parser import parse_chunk, split_chunks
from macrovoice.units import UnitKind


def test_split_on_and_comma_dutch_en():
    assert split_chunks("2 loaves of AH volkoren, 200g skyr and a banana en een appel") == [
        "2 loaves of AH volkoren", "200g skyr", "a banana", "een appel"]


def test_split_empty():
    assert split_chunks("  ,  ") == []


@pytest.mark.parametrize("text,qty,unit,kind,food", [
    ("2 loaves of AH volkoren", 2, "loaves", UnitKind.PACKAGE, "ah volkoren"),
    ("200g skyr", 200, "g", UnitKind.MASS, "skyr"),
    ("200 g Jumbo skyr", 200, "g", UnitKind.MASS, "jumbo skyr"),
    ("1,5 liter melk", 1.5, "liter", UnitKind.VOLUME, "melk"),
    ("a banana", 1, None, UnitKind.SERVING, "banana"),
    ("banana", 1, None, UnitKind.SERVING, "banana"),
    ("three slices of bread", 3, "slices", UnitKind.SERVING, "bread"),
    ("half a loaf of bread", 0.5, "loaf", UnitKind.PACKAGE, "bread"),
    ("1/2 pak yoghurt", 0.5, "pak", UnitKind.PACKAGE, "yoghurt"),
    ("ongeveer 2 sneetjes brood", 2, "sneetjes", UnitKind.SERVING, "brood"),
    ("2x AH pizza", 2, None, UnitKind.SERVING, "ah pizza"),
    ("2 tbsp peanut butter", 2, "tbsp", UnitKind.MEASURE, "peanut butter"),
])
def test_parse_chunk(text, qty, unit, kind, food):
    p = parse_chunk(text)
    assert (p.quantity, p.unit_text, p.unit_kind, p.food_text) == (qty, unit, kind, food)


def test_vague_amount_has_no_quantity():
    p = parse_chunk("some pasta")
    assert p.quantity is None and p.food_text == "pasta" and "vague" in p.vague_reason


def test_unit_word_alone_is_food_not_unit():
    # "can" with nothing after it is the food name, not a unit
    assert parse_chunk("2 bowl").food_text == "bowl"
