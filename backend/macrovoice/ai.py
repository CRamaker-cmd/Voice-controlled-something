"""AI fallback for items the local database cannot resolve. Optional: the app works without it."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx


class AIError(RuntimeError):
    pass


@dataclass(frozen=True)
class AIEstimate:
    identified: bool
    grams: float = 0.0
    kcal: float = 0.0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    note: str = ""


class AIEstimator(Protocol):
    def estimate(self, chunk: str) -> AIEstimate: ...


_SYSTEM = (
    "You estimate nutrition for ONE food item from a voice food log (speech-recognition text, "
    "possibly Dutch, often naming a Dutch supermarket brand). Return the total weight in grams "
    "of the portion described and the macros for that whole portion (not per 100 g). "
    "If you do not recognise the food, or the portion cannot be inferred from the text, set "
    "identified=false and leave the numbers at 0: never invent a product. If you know the brand's "
    "actual product use it; if you only know a typical equivalent, say so in `note`. "
    "Always answer by calling the log_item tool."
)

_TOOL = {
    "name": "log_item",
    "description": "Record the estimate for the food item.",
    "input_schema": {
        "type": "object",
        "properties": {
            "identified": {"type": "boolean"},
            "grams": {"type": "number", "description": "total grams (or ml) of the portion"},
            "kcal": {"type": "number"},
            "protein_g": {"type": "number"},
            "carbs_g": {"type": "number"},
            "fat_g": {"type": "number"},
            "note": {"type": "string", "description": "assumptions made, e.g. generic equivalent used"},
        },
        "required": ["identified"],
    },
}


class AnthropicEstimator:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-5-5",
        client: httpx.Client | None = None,
        base_url: str = "https://api.anthropic.com",
    ):
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.Client(timeout=60)
        self.base_url = base_url.rstrip("/")

    def estimate(self, chunk: str) -> AIEstimate:
        try:
            resp = self.client.post(
                f"{self.base_url}/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": self.model,
                    "max_tokens": 400,
                    "system": _SYSTEM,
                    "tools": [_TOOL],
                    "tool_choice": {"type": "tool", "name": "log_item"},
                    "messages": [{"role": "user", "content": chunk}],
                },
            )
        except httpx.HTTPError as e:
            raise AIError(f"AI request failed: {e}") from e
        if resp.status_code != 200:
            raise AIError(f"AI API returned {resp.status_code}: {resp.text[:200]}")
        try:
            block = next(b for b in resp.json()["content"] if b["type"] == "tool_use")
            i = block["input"]
            if not i.get("identified"):
                return AIEstimate(identified=False, note=i.get("note", ""))
            est = AIEstimate(
                identified=True, grams=float(i["grams"]), kcal=float(i["kcal"]),
                protein=float(i["protein_g"]), carbs=float(i["carbs_g"]), fat=float(i["fat_g"]),
                note=i.get("note", ""),
            )
        except (StopIteration, KeyError, TypeError, ValueError) as e:
            raise AIError(f"unexpected AI response shape: {e!r}") from e
        if est.grams <= 0 or min(est.kcal, est.protein, est.carbs, est.fat) < 0:
            return AIEstimate(identified=False, note="AI returned unusable numbers")
        return est
