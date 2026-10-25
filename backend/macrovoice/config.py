"""All configuration comes from environment variables (see README, "Configuration")."""
from __future__ import annotations

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Settings:
    db_path: str = "data/macrovoice.db"
    timezone: str = "Europe/Amsterdam"
    api_token: str | None = None
    anthropic_api_key: str | None = None
    ai_model: str = "claude-haiku-5-5"
    usda_api_key: str | None = None
    worker_jobs: tuple[str, ...] = ("off-api",)
    worker_interval_hours: float = 168.0
    off_pages: int = 50
    off_country: str = "netherlands"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        d = cls()
        return cls(
            db_path=e.get("MACROVOICE_DB", d.db_path),
            timezone=e.get("MACROVOICE_TZ", d.timezone),
            api_token=e.get("MACROVOICE_API_TOKEN") or None,
            anthropic_api_key=e.get("ANTHROPIC_API_KEY") or None,
            ai_model=e.get("MACROVOICE_AI_MODEL", d.ai_model),
            usda_api_key=e.get("USDA_API_KEY") or None,
            worker_jobs=tuple(j.strip() for j in e.get("WORKER_JOBS", ",".join(d.worker_jobs)).split(",") if j.strip()),
            worker_interval_hours=float(e.get("WORKER_INTERVAL_HOURS", d.worker_interval_hours)),
            off_pages=int(e.get("OFF_PAGES", d.off_pages)),
            off_country=e.get("OFF_COUNTRY", d.off_country),
        )
