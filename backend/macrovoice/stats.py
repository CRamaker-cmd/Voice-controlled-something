"""Day / week / month aggregates computed from the diary tables."""
from __future__ import annotations

import calendar
import sqlite3
from datetime import date, timedelta

MACROS = ("kcal", "protein", "carbs", "fat")


def period_bounds(kind: str, anchor: date) -> tuple[date, date]:
    if kind == "day":
        return anchor, anchor
    if kind == "week":  # ISO week: Monday..Sunday
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=6)
    if kind == "month":
        return anchor.replace(day=1), anchor.replace(day=calendar.monthrange(anchor.year, anchor.month)[1])
    raise ValueError(f"unknown period kind: {kind}")


def _r(x: float) -> float:
    return round(x, 1)


def _split(p: float, c: float, f: float) -> dict | None:
    total = p * 4 + c * 4 + f * 9
    if total <= 0:
        return None
    return {"protein_pct": _r(p * 4 / total * 100), "carbs_pct": _r(c * 4 / total * 100),
            "fat_pct": _r(f * 9 / total * 100)}


def build_stats(conn: sqlite3.Connection, kind: str, anchor: date, today: date) -> dict:
    start, end = period_bounds(kind, anchor)
    rows = conn.execute(
        """
        SELECT e.local_date AS d,
               COALESCE(SUM(CASE WHEN i.status='resolved' THEN i.kcal END), 0)    AS kcal,
               COALESCE(SUM(CASE WHEN i.status='resolved' THEN i.protein END), 0) AS protein,
               COALESCE(SUM(CASE WHEN i.status='resolved' THEN i.carbs END), 0)   AS carbs,
               COALESCE(SUM(CASE WHEN i.status='resolved' THEN i.fat END), 0)     AS fat,
               COALESCE(SUM(i.status='unresolved'), 0)                            AS unresolved
        FROM entries e JOIN entry_items i ON i.entry_id = e.id
        WHERE e.local_date BETWEEN ? AND ?
        GROUP BY e.local_date
        """,
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    by_day = {r["d"]: r for r in rows}

    per_day = []
    d = start
    while d <= end:
        r = by_day.get(d.isoformat())
        per_day.append({
            "date": d.isoformat(), "logged": r is not None,
            **{m: _r(r[m]) if r else 0.0 for m in MACROS},
            "unresolved_items": int(r["unresolved"]) if r else 0,
        })
        d += timedelta(days=1)

    totals = {m: _r(sum(r[m] for r in rows)) for m in MACROS}
    days_logged = len(rows)
    days_elapsed = max(0, (min(end, today) - start).days + 1)
    logged_days = [p for p in per_day if p["logged"]]

    def avg(divisor: int) -> dict | None:
        return {m: _r(totals[m] / divisor) for m in MACROS} if divisor else None

    return {
        "kind": kind,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "days_in_period": (end - start).days + 1,
        "days_elapsed": days_elapsed,
        "days_logged": days_logged,
        "totals": totals,
        "avg_per_logged_day": avg(days_logged),
        "avg_per_day": avg(days_elapsed),
        "macro_split": _split(totals["protein"], totals["carbs"], totals["fat"]),
        "highest_day": max(logged_days, key=lambda p: p["kcal"]) if logged_days else None,
        "lowest_day": min(logged_days, key=lambda p: p["kcal"]) if logged_days else None,
        "unresolved_items": sum(p["unresolved_items"] for p in per_day),
        "per_day": per_day,
    }
