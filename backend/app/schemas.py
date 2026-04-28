from datetime import datetime
from typing import Literal

from pydantic import BaseModel

TimeRange = Literal["1h", "24h", "7d", "30d"]


class CountrySummary(BaseModel):
    country: str
    country_code: str | None = None
    count: int


class WanSourcePoint(BaseModel):
    source_ip: str
    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    event_count: int
    last_seen_at: datetime | None = None
    last_message: str | None = None


class WanSourceResponse(BaseModel):
    time_range: TimeRange
    total_hits: int
    items: list[WanSourcePoint]
    countries: list[CountrySummary]
