"""Gate tests for build-plan batch B01 and B02.

B01 - every response carries the security headers that
``docs/SECURITY_ARCHITECTURE.md`` section 8 has always specified.
B02 - no development origin ships in the default CORS configuration.

These tests assert behaviour on the real application, not on the middleware
class in isolation, because the failure they guard against is a middleware that
exists but is never mounted.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.app import create_application
from app.config.settings import Settings
from app.middleware.security_headers import SECURITY_HEADERS


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_application())


@pytest.mark.parametrize("header,value", sorted(SECURITY_HEADERS.items()))
def test_header_present_on_health(client: TestClient, header: str, value: str) -> None:
    response = client.get("/health")
    assert response.headers.get(header) == value


def test_headers_present_on_404(client: TestClient) -> None:
    """An error response is still framed and sniffed the same way."""
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    for header in SECURITY_HEADERS:
        assert header in response.headers


def test_headers_present_on_unauthenticated_request(client: TestClient) -> None:
    response = client.get("/api/v1/patients")
    assert response.status_code in (401, 403)
    for header in SECURITY_HEADERS:
        assert header in response.headers


def test_framing_is_denied(client: TestClient) -> None:
    """Clickjacking protection specifically: the GUI must not be framable."""
    response = client.get("/health")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_content_policy_does_not_allow_remote_script() -> None:
    """Inline is permitted for now; a remote origin never is."""
    policy = SECURITY_HEADERS["Content-Security-Policy"]
    assert "script-src 'self' 'unsafe-inline'" in policy
    assert "http://" not in policy
    assert "https://" not in policy


def test_no_development_origin_in_cors_default() -> None:
    """B02: a hospital install must not ship a localhost origin."""
    origins = Settings.model_fields["BACKEND_CORS_ORIGINS"].default_factory()
    assert origins == [], f"default CORS origins should be empty, found {origins}"


def test_no_localhost_anywhere_in_shipped_env_example() -> None:
    from pathlib import Path

    example = Path(__file__).resolve().parents[1] / ".env.example"
    text = example.read_text(encoding="utf-8")
    assert "localhost" not in text, ".env.example must not advertise localhost origins"
