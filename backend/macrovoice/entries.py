"""Diary: logging a text, listing a day, correcting and deleting."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from .parser import parse_chunk, split_chunks
from .resolver import Resolver


class NothingToLog(ValueError):
    pass


def _item_dict(r: sqlite3.Row) -> dict:
    return {k: r[k] for k in ("id", "name", "amount_text", "grams", "kcal", "protein", "carbs", "fat",
                              "source", "status", "note", "food_id")}


def _sum(items: list[dict]) -> dict:
    out = {}
    for k in ("kcal", "protein", "carbs", "fat"):
        out[k] = round(sum(i[k] or 0 for i in items if i["status"] == "resolved"), 1)
    out["unresolved_items"] = sum(1 for i in items if i["status"] == "unresolved")
    return out


class EntryService:
    def __init__(self, conn: sqlite3.Connection, resolver: Resolver, tz: ZoneInfo):
        self.conn, self.resolver, self.tz = conn, resolver, tz

    def log(self, text: str, at: datetime) -> dict:
        chunks = split_chunks(text)
        if not chunks:
            raise NothingToLog("no food found in the text")
        items = [self.resolver.resolve(parse_chunk(c)) for c in chunks]
        if at.tzinfo is None:
            at = at.replace(tzinfo=self.tz)
        with self.conn:
            entry_id = self.conn.execute(
                "INSERT INTO entries (logged_at, local_date, raw_text) VALUES (?,?,?) RETURNING id",
                (at.astimezone(timezone.utc).isoformat(), at.astimezone(self.tz).date().isoformat(), text.strip()),
            ).fetchone()[0]
            for pos, it in enumerate(items):
                self.conn.execute(
                    """INSERT INTO entry_items (entry_id, position, food_id, name, amount_text, grams,
                       kcal, protein, carbs, fat, source, status, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (entry_id, pos, it.food_id, it.name, it.amount_text, it.grams, it.kcal, it.protein,
                     it.carbs, it.fat, it.source, it.status, it.note),
                )
        return self.get(entry_id)

    def get(self, entry_id: int) -> dict | None:
        e = self.conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if e is None:
            return None
        items = [_item_dict(r) for r in self.conn.execute(
            "SELECT * FROM entry_items WHERE entry_id = ? ORDER BY position", (entry_id,))]
        return {"id": e["id"], "logged_at": e["logged_at"], "local_date": e["local_date"],
                "raw_text": e["raw_text"], "items": items, "totals": _sum(items)}

    def list_day(self, day: date) -> list[dict]:
        ids = [r[0] for r in self.conn.execute(
            "SELECT id FROM entries WHERE local_date = ? ORDER BY logged_at, id", (day.isoformat(),))]
        return [self.get(i) for i in ids]

    def delete(self, entry_id: int) -> bool:
        with self.conn:
            return self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,)).rowcount > 0

    def set_item(self, item_id: int, *, name: str | None, grams: float | None,
                 kcal: float, protein: float, carbs: float, fat: float) -> dict | None:
        """Manual correction; also the way to resolve an 'unresolved' item."""
        row = self.conn.execute("SELECT entry_id, name FROM entry_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            return None
        with self.conn:
            self.conn.execute(
                """UPDATE entry_items SET name=?, grams=?, kcal=?, protein=?, carbs=?, fat=?,
                   source='manual', status='resolved', note='manually set' WHERE id=?""",
                (name or row["name"], grams, kcal, protein, carbs, fat, item_id),
            )
        return self.get(row["entry_id"])
