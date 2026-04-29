import os
from pathlib import Path
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import Base, engine, get_db
from app.models import WanHit
from app.receiver import UdpSyslogReceiver
from app.schemas import CountrySummary, TimeRange, WanSourcePoint, WanSourceResponse

TIME_RANGE_WINDOWS: dict[TimeRange, timedelta] = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

settings = get_settings()
receiver = UdpSyslogReceiver(settings) if settings.syslog_enabled else None
frontend_dir = Path(os.environ["NETATLAS_STATIC_DIR"]).resolve() if os.environ.get("NETATLAS_STATIC_DIR") else None


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _window_start(time_range: TimeRange) -> datetime:
    return datetime.now(timezone.utc) - TIME_RANGE_WINDOWS[time_range]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if receiver is not None:
        receiver.start()
    try:
        yield
    finally:
        if receiver is not None:
            receiver.stop()


app = FastAPI(title="NetAtlas API", version="0.2.1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "https_enabled": settings.https_enabled,
        "https_port": settings.https_port if settings.https_enabled else None,
        "syslog_enabled": settings.syslog_enabled,
        "syslog_bind_host": settings.syslog_bind_host,
        "syslog_bind_port": settings.syslog_bind_port,
    }


@app.get("/api/wan-sources", response_model=WanSourceResponse)
def get_wan_sources(
    time_range: TimeRange = Query(default="24h"),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> WanSourceResponse:
    start = _window_start(time_range)
    rows = list(db.scalars(select(WanHit).where(WanHit.received_at >= start).order_by(WanHit.received_at.desc())).all())

    total_hits = len(rows)
    by_source: dict[str, WanSourcePoint] = {}
    country_counts: Counter[str] = Counter()
    country_codes: dict[str, str | None] = {}

    for row in rows:
        country = row.geo_country or "Unknown"
        country_counts[country] += 1
        country_codes.setdefault(country, row.geo_country_code)
        if country_codes[country] is None and row.geo_country_code:
            country_codes[country] = row.geo_country_code

        existing = by_source.get(row.source_ip)
        if existing is None:
            by_source[row.source_ip] = WanSourcePoint(
                source_ip=row.source_ip,
                country=row.geo_country,
                country_code=row.geo_country_code,
                region=row.geo_region,
                city=row.geo_city,
                latitude=row.geo_latitude,
                longitude=row.geo_longitude,
                event_count=1,
                last_seen_at=_as_utc(row.received_at),
                last_message=row.message,
            )
            continue

        existing.event_count += 1
        if existing.last_seen_at is None or _as_utc(row.received_at) > existing.last_seen_at:
            existing.last_seen_at = _as_utc(row.received_at)
            existing.last_message = row.message

    items = sorted(
        by_source.values(),
        key=lambda item: (
            -item.event_count,
            -(item.last_seen_at.timestamp() if item.last_seen_at is not None else 0),
            item.source_ip,
        ),
    )[:limit]
    countries = [
        CountrySummary(country=country, country_code=country_codes.get(country), count=count)
        for country, count in country_counts.most_common()
    ]
    return WanSourceResponse(time_range=time_range, total_hits=total_hits, items=items, countries=countries)


if frontend_dir and frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
