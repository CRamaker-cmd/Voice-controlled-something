"""HTTP API (FastAPI). `create_app` takes its collaborators so tests can inject fakes."""
from __future__ import annotations

import secrets
import uuid
from datetime import date, datetime
from typing import Callable, Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import db
from .ai import AIEstimator, AnthropicEstimator
from .config import Settings
from .entries import EntryService, NothingToLog
from .foods import FoodRecord, FoodRepo, tokenize
from .resolver import Resolver
from .stats import build_stats


class EntryIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    logged_at: datetime | None = None   # default: now. Naive values are read in the server timezone.


class ItemIn(BaseModel):
    name: str | None = None
    grams: float | None = Field(default=None, ge=0)
    kcal: float = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)


class FoodIn(BaseModel):
    name: str = Field(min_length=1)
    brand: str | None = None
    category: str | None = None
    kcal_100g: float = Field(ge=0)
    protein_100g: float = Field(ge=0)
    carbs_100g: float = Field(ge=0)
    fat_100g: float = Field(ge=0)
    serving_g: float | None = Field(default=None, gt=0)
    package_g: float | None = Field(default=None, gt=0)


def create_app(
    settings: Settings,
    ai: AIEstimator | None = None,
    clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    if ai is None and settings.anthropic_api_key:
        ai = AnthropicEstimator(settings.anthropic_api_key, settings.ai_model)
    now = clock or (lambda: datetime.now(settings.tz))
    app = FastAPI(title="MacroVoice")
    db.connect(settings.db_path).close()  # run migrations once at startup

    def get_conn() -> Iterator:
        conn = db.connect(settings.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def auth(authorization: str | None = Header(default=None)) -> None:
        if settings.api_token is None:
            return
        supplied = (authorization or "").removeprefix("Bearer ").strip()
        if not secrets.compare_digest(supplied, settings.api_token):
            raise HTTPException(401, "missing or wrong bearer token")

    def service(conn=Depends(get_conn)) -> EntryService:
        return EntryService(conn, Resolver(FoodRepo(conn), ai), settings.tz)

    secured = [Depends(auth)]

    @app.get("/health")
    def health():
        return {"status": "ok", "ai_enabled": ai is not None}

    @app.post("/entries", status_code=201, dependencies=secured)
    def log_entry(body: EntryIn, svc: EntryService = Depends(service)):
        at = body.logged_at or now()
        try:
            return svc.log(body.text, at)
        except NothingToLog as e:
            raise HTTPException(422, str(e))

    @app.get("/entries", dependencies=secured)
    def list_entries(day: date | None = Query(default=None, alias="date"), svc: EntryService = Depends(service)):
        d = day or now().date()
        entries = svc.list_day(d)
        return {"date": d.isoformat(), "entries": entries}

    @app.delete("/entries/{entry_id}", status_code=204, dependencies=secured)
    def delete_entry(entry_id: int, svc: EntryService = Depends(service)):
        if not svc.delete(entry_id):
            raise HTTPException(404, "entry not found")

    @app.put("/items/{item_id}", dependencies=secured)
    def set_item(item_id: int, body: ItemIn, svc: EntryService = Depends(service)):
        entry = svc.set_item(item_id, **body.model_dump())
        if entry is None:
            raise HTTPException(404, "item not found")
        return entry

    def _stats(kind: str, anchor: date | None, conn) -> dict:
        today = now().date()
        return build_stats(conn, kind, anchor or today, today)

    @app.get("/stats/day", dependencies=secured)
    def stats_day(day: date | None = Query(default=None, alias="date"), conn=Depends(get_conn)):
        return _stats("day", day, conn)

    @app.get("/stats/week", dependencies=secured)
    def stats_week(day: date | None = Query(default=None, alias="date"), conn=Depends(get_conn)):
        return _stats("week", day, conn)

    @app.get("/stats/month", dependencies=secured)
    def stats_month(day: date | None = Query(default=None, alias="date"), conn=Depends(get_conn)):
        return _stats("month", day, conn)

    @app.get("/foods/search", dependencies=secured)
    def search_foods(q: str = Query(min_length=1), limit: int = Query(default=10, le=50), conn=Depends(get_conn)):
        return [f.__dict__ for f in FoodRepo(conn).search(tokenize(q), limit)]

    @app.post("/foods", status_code=201, dependencies=secured)
    def add_food(body: FoodIn, conn=Depends(get_conn)):
        repo = FoodRepo(conn)
        fid = repo.upsert(FoodRecord(source="manual", source_id=uuid.uuid4().hex, **body.model_dump()))
        return repo.get(fid).__dict__

    return app
