import logging
import socket
import threading
from datetime import datetime, timezone

from app.core.config import Settings
from app.core.db import SessionLocal
from app.ingestion import ingest_syslog_message

logger = logging.getLogger(__name__)


class UdpSyslogReceiver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._sock: socket.socket | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._serve, name="udp-syslog-receiver", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _serve(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock = sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.settings.syslog_bind_host, self.settings.syslog_bind_port))
        sock.settimeout(0.5)
        logger.info("UDP syslog receiver listening on %s:%s", self.settings.syslog_bind_host, self.settings.syslog_bind_port)

        while not self._stop_event.is_set():
            try:
                data, address = sock.recvfrom(self.settings.syslog_max_message_size)
            except socket.timeout:
                continue
            except OSError:
                if self._stop_event.is_set():
                    break
                logger.exception("Syslog receiver socket error")
                continue

            sender_ip = address[0]
            raw_message = data.decode("utf-8", errors="replace").strip()
            if not raw_message:
                continue

            try:
                with SessionLocal() as session:
                    ingest_syslog_message(
                        session,
                        self.settings,
                        sender_ip=sender_ip,
                        raw_message=raw_message,
                        received_at=datetime.now(timezone.utc),
                    )
            except Exception:
                logger.exception("Failed to ingest syslog datagram", extra={"sender_ip": sender_ip})
