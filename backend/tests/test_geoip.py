import json
from datetime import datetime, timedelta, timezone
from io import BytesIO
from urllib.error import URLError

from app.core.config import Settings
from app.geoip import GeoIpLookup
from app.models import GeoIpCache


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._stream = BytesIO(json.dumps(payload).encode("utf-8"))

    def read(self) -> bytes:
        return self._stream.read()

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_geoip_lookup_skips_private_and_invalid_ips(db_session) -> None:
    lookup = GeoIpLookup(db_session, Settings())

    assert lookup.lookup("192.168.1.10") == {}
    assert lookup.lookup("not-an-ip") == {}


def test_geoip_lookup_returns_cached_value_when_not_expired(db_session) -> None:
    cache = GeoIpCache(
        cache_key="geoip:8.8.8.8",
        country="Germany",
        country_code="DE",
        region="Berlin",
        city="Berlin",
        latitude=52.52,
        longitude=13.405,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(cache)
    db_session.commit()

    lookup = GeoIpLookup(db_session, Settings())
    result = lookup.lookup("8.8.8.8")

    assert result["country"] == "Germany"
    assert result["country_code"] == "DE"


def test_geoip_lookup_returns_empty_on_upstream_failure(db_session, monkeypatch) -> None:
    monkeypatch.setattr("app.geoip.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(URLError("down")))
    lookup = GeoIpLookup(db_session, Settings())

    assert lookup.lookup("8.8.8.8") == {}


def test_geoip_lookup_refreshes_expired_cache(db_session, monkeypatch) -> None:
    cache = GeoIpCache(
        cache_key="geoip:8.8.8.8",
        country="Old",
        country_code="OL",
        region="Old",
        city="Old",
        latitude=0.0,
        longitude=0.0,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(cache)
    db_session.commit()

    monkeypatch.setattr(
        "app.geoip.urlopen",
        lambda *args, **kwargs: _FakeResponse(
            {
                "success": True,
                "country": "Germany",
                "country_code": "DE",
                "region": "Berlin",
                "city": "Berlin",
                "latitude": 52.52,
                "longitude": 13.405,
            }
        ),
    )
    lookup = GeoIpLookup(db_session, Settings())
    result = lookup.lookup("8.8.8.8")

    assert result["country"] == "Germany"
    db_session.refresh(cache)
    assert cache.country == "Germany"


def test_geoip_lookup_returns_empty_for_unsuccessful_payload(db_session, monkeypatch) -> None:
    monkeypatch.setattr("app.geoip.urlopen", lambda *args, **kwargs: _FakeResponse({"success": False}))
    lookup = GeoIpLookup(db_session, Settings())

    assert lookup.lookup("8.8.8.8") == {}
