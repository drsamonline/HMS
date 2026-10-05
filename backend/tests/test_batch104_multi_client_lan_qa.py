"""Batch 104 (Milestone 6) — Multi-client LAN concurrency QA suite.

Reproduces the packaged LAN deployment in-process: several simulated
client machines issue simultaneous requests against one server stack
sharing a single file-based SQLite database (WAL journaling + busy
timeout, exactly as ``app.db.session`` configures for file URLs).

Covers:
* concurrent ``POST /auth/login`` fan-out with real Argon2 verification;
* concurrent bearer-token issuance and authenticated round-trips;
* concurrent patient registrations minting unique patient numbers
  through the row-locked ``NumberSequence`` service;
* the UDP LAN discovery handshake (``HHMS_DISCOVER_V1``) agreeing with
  the ``GET /health/discovery`` HTTP contract.
"""
from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from _qa_harness import (
    _QA_LAN_PASSWORD,
    concurrent_map,
    make_file_client,
    seed_client_user,
    seed_number_sequence,
    token_for_login,
)

CLIENT_COUNT = 6


@pytest.fixture()
def shared_db(tmp_path: Path) -> str:
    return str(tmp_path / "hhms-lan-shared.sqlite3")


def test_concurrent_logins_across_shared_file_db(shared_db: str) -> None:
    """N simultaneous logins from N client threads all succeed on one DB."""
    credentials = []
    with make_file_client(shared_db) as (make_client, dispose):
        for index in range(1, CLIENT_COUNT + 1):
            credentials.append(seed_client_user(index))

        def login(item):
            username, password = item
            client = make_client()
            return token_for_login(client, username, password)

        tokens = concurrent_map(login, credentials, workers=CLIENT_COUNT)
        dispose()

    assert len(tokens) == CLIENT_COUNT
    assert all(isinstance(t, str) and t.count(".") == 2 for t in tokens)
    # Each login mints an independent JWT — no token reuse/collision.
    assert len(set(tokens)) == CLIENT_COUNT


def test_concurrent_token_mints_and_authenticated_roundtrips(tmp_path: Path) -> None:
    """Each simulated client logs in then calls /auth/me concurrently.

    Uses its own shared DB file so user seeding from earlier tests in the
    module cannot leak into this fixture's schema.
    """
    with make_file_client(str(tmp_path / "hhms-lan-roundtrip.sqlite3")) as (
        make_client,
        dispose,
    ):
        credentials = [seed_client_user(i) for i in range(1, CLIENT_COUNT + 1)]

        def session_roundtrip(item):
            username, password = item
            client = make_client()
            token = token_for_login(client, username, password)
            response = client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200, response.text
            return response.json()["username"]

        names = concurrent_map(session_roundtrip, credentials, workers=CLIENT_COUNT)
        dispose()

    assert sorted(names) == sorted(u for u, _ in credentials)


def test_concurrent_patient_registrations_mint_unique_numbers(shared_db: str) -> None:
    """Simultaneous POST /patients never produce duplicate patient numbers."""
    REGISTRATIONS = 10
    with make_file_client(shared_db) as (make_client, dispose):
        username, password = seed_client_user(1)
        seed_number_sequence(sequence_name="patient_number", prefix="P-")

        admin_client = make_client()
        token = token_for_login(admin_client, username, _QA_LAN_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}

        def register(index: int):
            client = make_client()  # independent event loop per thread
            response = client.post(
                "/api/v1/patients",
                headers=headers,
                json={
                    "first_name": "Lan",
                    "last_name": f"Client{index:02d}",
                    "gender": "male",
                },
            )
            assert response.status_code == 201, response.text
            return response.json()["patient_number"]

        numbers = concurrent_map(register, list(range(REGISTRATIONS)), workers=8)
        dispose()

    assert len(numbers) == REGISTRATIONS
    assert len(set(numbers)) == REGISTRATIONS, f"duplicates: {numbers}"
    assert sorted(int(n.split("-")[1]) for n in numbers) == list(
        range(1, REGISTRATIONS + 1)
    )
    assert password  # seeded credential tuple fully consumed by flow


# ---------------------------------------------------------------------------
# UDP LAN discovery integration
# ---------------------------------------------------------------------------


def _udp_probe(port: int, request: bytes = b"HHMS_DISCOVER_V1", timeout: float = 3.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(request, ("127.0.0.1", port))
        data, _addr = sock.recvfrom(4096)
        return json.loads(data.decode("utf-8"))
    finally:
        sock.close()


def test_udp_discovery_handshake_matches_http_contract(monkeypatch, tmp_path):
    """Real HHMS_DISCOVER_V1 exchange agrees with GET /health/discovery."""
    from app.config import settings as settings_module
    from app.network.discovery import DISCOVERY_REQUEST, LanDiscoveryResponder

    monkeypatch.setenv("HHMS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DISCOVERY_ENABLED", "true")
    free_port = socket.socket()
    free_port.bind(("127.0.0.1", 0))
    _, udp_port = free_port.getsockname()
    free_port.close()
    monkeypatch.setenv("DISCOVERY_PORT", str(udp_port))
    settings_module.get_settings.cache_clear()

    responder = LanDiscoveryResponder()
    responder.start()
    try:
        payload = _udp_probe(udp_port, DISCOVERY_REQUEST)
        assert payload["protocol"] == "hhms-lan-v1"
        assert payload["server_id"]

        # Wrong magic token must be ignored (no reply within short window).
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        try:
            sock.sendto(b"NOT-HHMS", ("127.0.0.1", udp_port))
            with pytest.raises(socket.timeout):
                sock.recvfrom(4096)
        finally:
            sock.close()

        # HTTP contract consistency for the same fields.
        with make_file_client(str(tmp_path / "discovery.sqlite3")) as (
            make_client,
            dispose,
        ):
            client = make_client()
            info = client.get("/api/v1/health/discovery").json()
            dispose()

        assert info["server_id"] == payload["server_id"]
        assert info["protocol"] == payload["protocol"]
        assert info["http_port"] == payload["http_port"]
        assert info["api_base"] == payload["api_base"]
    finally:
        responder.stop()
        settings_module.get_settings.cache_clear()


def test_health_endpoints_respond_under_concurrent_clients(shared_db: str) -> None:
    """24 concurrent liveness probes across shared clients all stay healthy."""
    with make_file_client(shared_db) as (make_client, dispose):

        def probe(_: int):
            client = make_client()
            live = client.get("/api/v1/health/live")
            assert live.status_code == 200
            return live.json()["status"]

        results = concurrent_map(probe, range(24), workers=8)
        dispose()

    assert set(results) == {"healthy"}
    assert len(results) == 24
