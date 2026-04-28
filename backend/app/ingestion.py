from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.geoip import GeoIpLookup
from app.models import WanHit
from app.parser import is_inbound_wan_hit, parse_syslog_message


def ingest_syslog_message(
    session: Session,
    settings: Settings,
    *,
    sender_ip: str,
    raw_message: str,
    received_at: datetime | None = None,
) -> WanHit | None:
    timestamp = received_at or datetime.now(timezone.utc)
    parsed = parse_syslog_message(raw_message, timestamp)
    if not is_inbound_wan_hit(parsed, settings):
        return None

    geo = GeoIpLookup(session, settings).lookup(parsed.source_ip)
    hit = WanHit(
        received_at=parsed.timestamp,
        sender_ip=sender_ip,
        source_ip=parsed.source_ip,
        destination_ip=parsed.destination_ip,
        interface_in=parsed.interface_in,
        action=parsed.action,
        message=parsed.message,
        raw_message=raw_message,
        geo_country=geo.get("country"),
        geo_country_code=geo.get("country_code"),
        geo_region=geo.get("region"),
        geo_city=geo.get("city"),
        geo_latitude=geo.get("latitude"),
        geo_longitude=geo.get("longitude"),
    )
    session.add(hit)
    session.commit()
    session.refresh(hit)
    return hit
