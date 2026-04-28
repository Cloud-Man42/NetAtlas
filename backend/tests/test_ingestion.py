from datetime import datetime, timezone

from app.core.config import Settings
from app.parser import is_inbound_wan_hit, parse_syslog_message


def test_parse_syslog_extracts_source_ip_and_interface() -> None:
    message = '<13>2026-04-21T12:00:00 fw1 src=198.51.100.20 dst=10.0.0.5 srcif=wan1 action=deny msg="Blocked inbound connection"'
    parsed = parse_syslog_message(message, datetime.now(timezone.utc))

    assert parsed is not None
    assert parsed.source_ip == "198.51.100.20"
    assert parsed.destination_ip == "10.0.0.5"
    assert parsed.interface_in == "wan1"
    assert parsed.action == "deny"


def test_inbound_wan_hit_requires_wan_interface_keyword() -> None:
    settings = Settings(WAN_INTERFACE_KEYWORDS="wan,internet")
    parsed = parse_syslog_message(
        'src=198.51.100.20 dst=10.0.0.5 srcif=lan1 action=deny msg="Should be ignored"',
        datetime.now(timezone.utc),
    )

    assert parsed is not None
    assert is_inbound_wan_hit(parsed, settings) is False
