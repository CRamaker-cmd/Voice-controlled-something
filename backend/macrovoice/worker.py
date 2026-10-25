"""Ingestion worker CLI.

    python -m macrovoice.worker off-api            # one-off, Open Food Facts search API
    python -m macrovoice.worker off-dump FILE.gz   # one-off, Open Food Facts bulk dump
    python -m macrovoice.worker usda               # one-off, USDA FoodData Central
    python -m macrovoice.worker loop               # run WORKER_JOBS every WORKER_INTERVAL_HOURS
"""
from __future__ import annotations

import argparse
import logging
import time

import httpx

from . import db
from .config import Settings
from .ingest.off import OFFApiSource, OFFDumpSource
from .ingest.pipeline import IngestStats, ingest
from .ingest.usda import USDASource

log = logging.getLogger("macrovoice.worker")


def run_job(name: str, settings: Settings, client: httpx.Client | None = None,
            dump_path: str | None = None, sleep=time.sleep) -> IngestStats:
    client = client or httpx.Client(timeout=60, follow_redirects=True)
    conn = db.connect(settings.db_path)
    try:
        if name == "off-api":
            src = OFFApiSource(client, settings.off_country, settings.off_pages, sleep=sleep)
        elif name == "off-dump":
            if not dump_path:
                raise ValueError("off-dump needs a dump file path")
            src = OFFDumpSource(dump_path)
        elif name == "usda":
            if not settings.usda_api_key:
                raise ValueError("USDA_API_KEY is not set")
            src = USDASource(client, settings.usda_api_key, sleep=sleep)
        else:
            raise ValueError(f"unknown job: {name}")
        stats = ingest(conn, name, src.fetch())
        log.info("job %s: stored=%d skipped=%d", name, stats.stored, stats.skipped)
        return stats
    finally:
        conn.close()


def loop(settings: Settings) -> None:
    while True:
        for job in settings.worker_jobs:
            try:
                run_job(job, settings)
            except Exception:
                log.exception("job %s failed; continuing with the next one", job)
        time.sleep(settings.worker_interval_hours * 3600)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="macrovoice.worker")
    ap.add_argument("job", choices=["off-api", "off-dump", "usda", "loop"])
    ap.add_argument("file", nargs="?", help="dump file for off-dump")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env()
    if args.job == "loop":
        loop(settings)
    else:
        run_job(args.job, settings, dump_path=args.file)


if __name__ == "__main__":
    main()
