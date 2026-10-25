from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from ..foods import FoodRecord, FoodRepo

BATCH = 500


@dataclass
class IngestStats:
    stored: int = 0
    skipped: int = 0


def sane(r: FoodRecord) -> bool:
    """Reject obviously broken source data rather than store it."""
    vals = (r.kcal_100g, r.protein_100g, r.carbs_100g, r.fat_100g)
    return (
        bool(r.name.strip())
        and all(v == v and v >= 0 for v in vals)          # v == v rejects NaN
        and r.kcal_100g <= 900
        and max(vals[1:]) <= 100
        and sum(vals[1:]) <= 100.5
    )


def ingest(conn: sqlite3.Connection, source: str, records: Iterable[FoodRecord | None]) -> IngestStats:
    """Upsert records in batches and log the run in `ingest_runs`. `None` = source row unusable."""
    repo = FoodRepo(conn)
    stats = IngestStats()
    with conn:
        run_id = conn.execute(
            "INSERT INTO ingest_runs (source, started_at) VALUES (?,?) RETURNING id",
            (source, datetime.now(timezone.utc).isoformat()),
        ).fetchone()[0]
    error = None
    batch: list[FoodRecord] = []
    try:
        for rec in records:
            if rec is None or not sane(rec):
                stats.skipped += 1
                continue
            batch.append(rec)
            if len(batch) >= BATCH:
                stats.stored += repo.upsert_many(batch)
                batch = []
        if batch:
            stats.stored += repo.upsert_many(batch)
    except Exception as e:  # keep partial progress, record the failure, re-raise
        error = repr(e)
        raise
    finally:
        with conn:
            conn.execute(
                "UPDATE ingest_runs SET finished_at=?, stored=?, skipped=?, error=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), stats.stored, stats.skipped, error, run_id),
            )
    return stats
