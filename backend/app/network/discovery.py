"""Native UDP LAN discovery responder for HHMS."""
from __future__ import annotations

import json
import logging
import socket
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.config.runtime_paths import server_identity_path
from app.config.settings import get_settings

logger = logging.getLogger("hhms.discovery")
DISCOVERY_REQUEST = b"HHMS_DISCOVER_V1"


def server_id() -> str:
    path = server_identity_path()
    try:
        value = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        value = ""
    if value:
        return value
    value = str(uuid.uuid4())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    return value


@dataclass
class LanDiscoveryResponder:
    """Background UDP responder used by clients to locate HHMS servers."""

    _thread: threading.Thread | None = None
    _stop_event: threading.Event | None = None
    _socket: socket.socket | None = None

    def start(self) -> None:
        settings = get_settings()
        if not settings.DISCOVERY_ENABLED or self._thread is not None:
            return
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._serve,
            name="hhms-lan-discovery",
            daemon=True,
        )
        self._thread.start()
        logger.info("LAN discovery enabled on UDP port %s", settings.DISCOVERY_PORT)

    def stop(self) -> None:
        if self._stop_event is None:
            return
        self._stop_event.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        self._stop_event = None
        self._socket = None

    def _payload(self) -> bytes:
        settings = get_settings()
        return json.dumps(
            {
                "protocol": "hhms-lan-v1",
                "name": settings.DISCOVERY_NAME,
                "server_id": server_id(),
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "http_port": int(settings.SERVER_PORT),
                "api_base": settings.API_V1_PREFIX,
            },
            separators=(",", ":"),
        ).encode("utf-8")

    def _serve(self) -> None:
        settings = get_settings()
        stop_event = self._stop_event
        if stop_event is None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket = sock
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", int(settings.DISCOVERY_PORT)))
            sock.settimeout(0.5)
            while not stop_event.is_set():
                try:
                    data, address = sock.recvfrom(1024)
                except socket.timeout:
                    continue
                except OSError:
                    break
                if data.strip() != DISCOVERY_REQUEST:
                    continue
                try:
                    sock.sendto(self._payload(), address)
                except OSError:
                    break
        except OSError:
            logger.exception("Unable to bind HHMS LAN discovery UDP port %s", settings.DISCOVERY_PORT)
        finally:
            try:
                sock.close()
            except OSError:
                pass


lan_discovery = LanDiscoveryResponder()

__all__ = [
    "DISCOVERY_REQUEST",
    "LanDiscoveryResponder",
    "lan_discovery",
    "server_id",
]
