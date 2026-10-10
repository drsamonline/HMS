from __future__ import annotations

import json

from app.network.discovery import DISCOVERY_REQUEST, LanDiscoveryResponder


def test_discovery_request_constant() -> None:
    assert DISCOVERY_REQUEST == b"HHMS_DISCOVER_V1"


def test_discovery_payload_is_json(monkeypatch) -> None:
    from app.network import discovery

    monkeypatch.setattr(discovery, "get_settings", lambda: type("S", (), {
        "DISCOVERY_NAME": "HHMS",
        "APP_NAME": "Hospital Homoeopathic Management System",
        "APP_VERSION": "0.1.0",
        "SERVER_PORT": 8000,
        "API_V1_PREFIX": "/api/v1",
    })())
    responder = LanDiscoveryResponder()
    payload = json.loads(responder._payload().decode("utf-8"))
    assert payload["protocol"] == "hhms-lan-v1"
    assert payload["name"] == "HHMS"
    assert payload["http_port"] == 8000
