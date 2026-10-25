"""Rule-based parsing of a spoken meal description into items. No AI, no network."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .units import UnitKind, lookup_unit

_SPLIT = re.compile(r"\s*(?:,|;|&|\+|\band\b|\ben\b|\bplus\b)\s*", re.IGNORECASE)
_APPROX = {"about", "ca", "ca.", "circa", "roughly", "approximately", "around", "ongeveer", "like", "~"}
_VAGUE = {"some", "wat", "few", "several", "couple", "paar", "beetje", "bit", "little", "lots", "veel"}
_FILLER = {"of", "van", "aan", "the", "de", "het"}
_ARTICLES = {"a", "an", "een", "one"}
_HALF = {"half", "halve", "halfje"}
_WORD_NUMBERS = {
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "twee": 2, "drie": 3, "vier": 4, "vijf": 5, "zes": 6,
    "zeven": 7, "acht": 8, "negen": 9, "tien": 10, "elf": 11, "twaalf": 12,
}
_NUM = re.compile(r"^(\d+(?:[.,]\d+)?)$")
_FRACTION = re.compile(r"^(\d+)/(\d+)$")
_GLUED = re.compile(r"^(\d+(?:[.,]\d+)?)([a-z]+)$")


@dataclass(frozen=True)
class ParsedItem:
    raw: str
    food_text: str
    quantity: float | None          # None = vague ("some"), cannot be computed locally
    unit_text: str | None
    unit_kind: UnitKind
    unit_factor: float
    vague_reason: str | None = None


def split_chunks(text: str) -> list[str]:
    return [c.strip() for c in _SPLIT.split(text.strip()) if c.strip()]


def _number(tok: str) -> float | None:
    frac = _FRACTION.match(tok)
    if frac and float(frac.group(2)) != 0:
        return float(frac.group(1)) / float(frac.group(2))
    m = _NUM.match(tok)
    if m:
        return float(m.group(1).replace(",", "."))
    return _WORD_NUMBERS.get(tok)


def parse_chunk(chunk: str) -> ParsedItem:
    tokens = [t for t in chunk.lower().replace("(", " ").replace(")", " ").split() if t]
    while tokens and tokens[0] in _APPROX:
        tokens.pop(0)

    quantity: float | None = 1.0
    vague_reason: str | None = None
    unit_text: str | None = None
    kind, factor = UnitKind.SERVING, 1.0

    # --- quantity -------------------------------------------------------------------------
    if tokens:
        glued = _GLUED.match(tokens[0])
        if glued and (glued.group(2) == "x" or lookup_unit(glued.group(2))):
            tokens[0:1] = [glued.group(1), glued.group(2)]
        first = tokens[0]
        if first in _VAGUE:
            quantity, vague_reason = None, f"amount is vague ('{first}')"
            tokens.pop(0)
            if tokens and tokens[0] in ("a", "of", "van", "aan", "een"):
                tokens.pop(0)
        elif first in _HALF:
            quantity = 0.5
            tokens.pop(0)
            if tokens and tokens[0] in _ARTICLES:
                tokens.pop(0)
        elif (n := _number(first)) is not None:
            quantity = n
            tokens.pop(0)
            if tokens and tokens[0] == "x":
                tokens.pop(0)
        elif first in _ARTICLES:
            quantity = 1.0
            tokens.pop(0)

    # --- unit -----------------------------------------------------------------------------
    if tokens:
        u = lookup_unit(tokens[0])
        if u and len(tokens) > 1:
            unit_text = tokens.pop(0)
            kind, factor = u
    while tokens and tokens[0] in _FILLER:
        tokens.pop(0)

    return ParsedItem(
        raw=chunk,
        food_text=" ".join(tokens),
        quantity=quantity,
        unit_text=unit_text,
        unit_kind=kind,
        unit_factor=factor,
        vague_reason=vague_reason,
    )
