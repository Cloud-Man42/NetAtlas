from datetime import datetime, timezone

from sqlalchemy import select

from app.core.config import Settings
from app.ingestion import ingest_syslog_message
from app.models import WanHit


def test_ingest_syslog_message_ignores_non_wan_hits(db_session) -> None:
    settings = Settings(WAN_INTERFACE_KEYWORDS="wan,internet")
    message = "src=198.51.100.20 dst=10.0.0.5 srcif=lan1 action=deny msg=ignored"

    result = ingest_syslog_message(db_session, settings, sender_ip="10.0.0.1", raw_message=message)

    assert result is None
    assert db_session.scalar(select(WanHit)) is None


def test_ingest_syslog_message_persists_hit_with_geo_fields(db_session, monkeypatch) -> None:
    settings = Settings(WAN_INTERFACE_KEYWORDS="wan", GEOIP_LOOKUP_ENABLED="false")
    message = "src=198.51.100.20 dst=10.0.0.5 srcif=wan1 action=deny msg=stored"

    monkeypatch.setattr(
        "app.ingestion.GeoIpLookup.lookup",
        lambda _self, _ip: {
            "country": "Germany",
            "country_code": "DE",
            "region": "Berlin",
            "city": "Berlin",
            "latitude": 52.52,
            "longitude": 13.405,
        },
    )

    result = ingest_syslog_message(
        db_session,
        settings,
        sender_ip="10.0.0.1",
        raw_message=message,
        received_at=datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc),
    )

    assert result is not None
    assert result.source_ip == "198.51.100.20"
    assert result.geo_country == "Germany"
    assert result.geo_country_code == "DE"
    persisted = db_session.scalar(select(WanHit))
    assert persisted is not None
    assert persisted.message == "stored"
