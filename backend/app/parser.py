import ipaddress
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.config import Settings

KV_PATTERN = re.compile(r'(\w[\w\-./]*)=("[^"]*"|\'[^\']*\'|\S+)')
SYSLOG_PRI_PATTERN = re.compile(r"^<(?P<pri>\d{1,3})>")
SYSLOG_HEADER_PATTERN = re.compile(
    r"^(?:(?P<month>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\s+\d{4})?)|(?P<iso>\d{4}-\d{2}-\d{2}[T ][^ ]+))\s+(?P<hostname>\S+)\s*(?P<rest>.*)$"
)
IP_PORT_PATTERN = re.compile(r"^(?P<ip>\[[0-9a-fA-F:]+\]|[^:]+?)(?::(?P<port>\d+))?$")


@dataclass
class ParsedSyslog:
    timestamp: datetime
    source_ip: str | None
    destination_ip: str | None
    interface_in: str | None
    action: str | None
    message: str


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _normalize_ip(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return str(ipaddress.ip_address(str(value).strip().strip("[]")))
    except ValueError:
        return None


def _normalize_datetime(value: Any, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return fallback

    text = str(value).strip()
    for parser in (
        lambda candidate: datetime.fromisoformat(candidate.replace("Z", "+00:00")),
        lambda candidate: datetime.strptime(candidate, "%b %d %H:%M:%S %Y"),
        lambda candidate: datetime.strptime(candidate, "%b %d %H:%M:%S"),
    ):
        try:
            parsed = parser(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return fallback


def _maybe_parse_syslog_header(message: str) -> tuple[dict[str, Any], str]:
    diagnostics: dict[str, Any] = {}
    working = message.strip()
    pri = SYSLOG_PRI_PATTERN.match(working)
    if pri:
        working = working[pri.end() :].strip()
    match = SYSLOG_HEADER_PATTERN.match(working)
    if not match:
        return diagnostics, working
    if match.group("hostname"):
        diagnostics["hostname"] = match.group("hostname")
    diagnostics["header_timestamp"] = match.group("month") or match.group("iso")
    return diagnostics, match.group("rest").strip()


def _extract_tokens(message: str) -> tuple[dict[str, str], str]:
    key_values: dict[str, str] = {}
    consumed_spans: list[tuple[int, int]] = []
    for match in KV_PATTERN.finditer(message):
        key_values[match.group(1).lower()] = _strip_quotes(match.group(2))
        consumed_spans.append(match.span())
    if not consumed_spans:
        return key_values, message.strip()

    fragments: list[str] = []
    previous_end = 0
    for start, end in consumed_spans:
        if start > previous_end:
            fragments.append(message[previous_end:start].strip())
        previous_end = end
    if previous_end < len(message):
        fragments.append(message[previous_end:].strip())
    return key_values, " ".join(fragment for fragment in fragments if fragment)


def _split_ip_port(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    match = IP_PORT_PATTERN.match(text)
    if not match:
        return _normalize_ip(text)
    return _normalize_ip(match.group("ip"))


def _split_direction(value: Any) -> tuple[str | None, str | None]:
    if value in (None, ""):
        return None, None
    left, _, right = str(value).partition(":")
    interface_in = left.strip() or None
    interface_out = right.strip() or None
    return interface_in, interface_out


def parse_syslog_message(raw_message: str, received_at: datetime) -> ParsedSyslog | None:
    if not raw_message.strip():
        return None

    header_bits, payload_text = _maybe_parse_syslog_header(raw_message)
    key_values, free_text = _extract_tokens(payload_text)
    interface_in, _ = _split_direction(key_values.get("dir"))

    timestamp = _normalize_datetime(
        key_values.get("time")
        or key_values.get("timestamp")
        or key_values.get("date")
        or header_bits.get("header_timestamp"),
        received_at,
    )
    message = key_values.get("msg") or key_values.get("message") or free_text or raw_message

    return ParsedSyslog(
        timestamp=timestamp,
        source_ip=_split_ip_port(key_values.get("src") or key_values.get("srcip") or key_values.get("source") or key_values.get("source_ip")),
        destination_ip=_split_ip_port(
            key_values.get("dst") or key_values.get("dstip") or key_values.get("destination") or key_values.get("destination_ip")
        ),
        interface_in=key_values.get("inif") or key_values.get("interface_in") or key_values.get("srcif") or interface_in,
        action=(key_values.get("action") or key_values.get("act") or key_values.get("result") or "").strip().lower() or None,
        message=message,
    )


def is_inbound_wan_hit(parsed: ParsedSyslog | None, settings: Settings) -> bool:
    if parsed is None or not parsed.source_ip or not parsed.interface_in:
        return False
    interface_name = parsed.interface_in.lower()
    return any(keyword in interface_name for keyword in settings.wan_keywords)
