import ipaddress
import json
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import GeoIpCache


class GeoIpLookup:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def lookup(self, ip_address: str | None) -> dict[str, object]:
        if not self.settings.geoip_lookup_enabled or not ip_address:
            return {}
        try:
            if ipaddress.ip_address(ip_address).is_private:
                return {}
        except ValueError:
            return {}

        cache_key = f"geoip:{ip_address}"
        cached = self.session.scalar(select(GeoIpCache).where(GeoIpCache.cache_key == cache_key))
        now = datetime.now(timezone.utc)
        if cached is not None and cached.expires_at is not None:
            expires_at = cached.expires_at if cached.expires_at.tzinfo else cached.expires_at.replace(tzinfo=timezone.utc)
            if expires_at >= now:
                return {
                    "country": cached.country,
                    "country_code": cached.country_code,
                    "region": cached.region,
                    "city": cached.city,
                    "latitude": cached.latitude,
                    "longitude": cached.longitude,
                }

        url = self.settings.geoip_lookup_url.format(ip=ip_address)
        try:
            with urlopen(url, timeout=self.settings.geoip_lookup_timeout_seconds) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError):
            return {}

        if payload.get("success") is False or not payload.get("country"):
            return {}

        result = {
            "country": payload.get("country"),
            "country_code": payload.get("country_code"),
            "region": payload.get("region"),
            "city": payload.get("city"),
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
        }
        if cached is None:
            cached = GeoIpCache(cache_key=cache_key)
            self.session.add(cached)
        cached.country = result["country"]
        cached.country_code = result["country_code"]
        cached.region = result["region"]
        cached.city = result["city"]
        cached.latitude = result["latitude"]
        cached.longitude = result["longitude"]
        cached.expires_at = now + timedelta(days=7)
        self.session.flush()
        return result
