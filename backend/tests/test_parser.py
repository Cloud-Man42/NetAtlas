from datetime import datetime, timezone

from app.core.config import Settings
from app.parser import is_inbound_wan_hit, parse_syslog_message


def test_parse_syslog_message_returns_none_for_blank_message() -> None:
    assert parse_syslog_message("   ", datetime.now(timezone.utc)) is None


def test_parse_syslog_message_uses_fallback_time_when_timestamp_invalid() -> None:
    received_at = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
    parsed = parse_syslog_message("time=not-a-date src=198.51.100.20 srcif=wan1 msg=test", received_at)

    assert parsed is not None
    assert parsed.timestamp == received_at


def test_parse_syslog_message_normalizes_invalid_ips_to_none() -> None:
    parsed = parse_syslog_message("src=not-ip dst=also-not-ip srcif=wan1 msg=test", datetime.now(timezone.utc))

    assert parsed is not None
    assert parsed.source_ip is None
    assert parsed.destination_ip is None


def test_is_inbound_wan_hit_returns_false_for_missing_interface() -> None:
    parsed = parse_syslog_message("src=198.51.100.20 msg=test", datetime.now(timezone.utc))
    settings = Settings(WAN_INTERFACE_KEYWORDS="wan,internet")

    assert is_inbound_wan_hit(parsed, settings) is False


def test_parse_syslog_message_handles_iso_header_timestamp() -> None:
    parsed = parse_syslog_message(
        "<13>2026-04-21T12:00:00Z fw1 src=198.51.100.20 srcif=wan1 msg=test",
        datetime.now(timezone.utc),
    )

    assert parsed is not None
    assert parsed.timestamp.year == 2026
    assert parsed.timestamp.month == 4
    assert parsed.timestamp.day == 21
