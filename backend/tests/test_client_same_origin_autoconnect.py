"""Regression: GUI served by HHMS must auto-connect to its own origin.

Problem fixed (session log F15): opening http://localhost:8000/ (or any
LAN/Wi-Fi address) previously ran only the native-bridge UDP discovery; in a
plain browser there is no bridge, so the app fell through to "Enter the server
address manually" even though the page itself was served BY the target server.
The client must treat its own location.origin as the server and connect with
zero prompts. This also makes dynamic/DHCP LAN IPs a non-issue: the bookmarked
URL always resolves to wherever the server currently lives.
"""

from pathlib import Path

CLIENT_DIR = Path(__file__).resolve().parents[2] / "frontend" / "js"


def _read(name: str) -> str:
    return (CLIENT_DIR / name).read_text(encoding="utf-8")


def test_discovery_exposes_same_origin_helper() -> None:
    source = _read("discovery.js")
    assert "export function sameOriginServer()" in source
    assert "location.origin" in source


def test_discover_server_falls_back_to_same_origin() -> None:
    source = _read("discovery.js")
    # The async discovery flow must consult the same-origin fallback instead
    # of returning null (which triggered the manual-IP prompt).
    assert "return sameOriginServer()" in source
    # A stale saved/manual URL takes precedence over re-probing, so users who
    # once connected keep connecting instantly.
    assert 'loadClientConfig().manualServerUrl' in source


def test_app_wires_same_origin_into_startup_and_discover() -> None:
    source = _read("app.js")
    assert "sameOriginServer" in source.splitlines()[0], (
        "app.js must import sameOriginServer from discovery.js"
    )
    # discover() failure path now attempts a same-origin connection rather
    # than leaving the user stuck at the offline/error state.
    assert "const same=sameOriginServer();if(same" in source


def test_saved_server_still_preferred_on_startup() -> None:
    # Preserve the documented startup contract (test_client_startup_restore)
    # while adding the same-origin fallback.
    source = _read("app.js")
    assert "await discover();" in source
    assert "c.manualServerUrl" in source
