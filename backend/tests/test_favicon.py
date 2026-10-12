"""Favicon regression tests.

Guards against the browser 404 noise caused by a missing icon handler:
browsers automatically request ``/favicon.ico`` when the HHMS GUI is
opened, and the bundled SVG shield must be served with a valid media
type both through the explicit route and through the static frontend
mount.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.app import create_application


def test_favicon_ico_route_serves_icon():
    application = create_application()
    with TestClient(application) as client:
        resp = client.get("/favicon.ico")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/svg+xml")
        assert b"<svg" in resp.content
        assert "max-age" in resp.headers.get("cache-control", "")


def test_favicon_svg_available_via_frontend_mount():
    application = create_application()
    with TestClient(application) as client:
        resp = client.get("/favicon.svg")
        assert resp.status_code == 200
        assert b"<svg" in resp.content


def test_index_html_links_the_favicon():
    application = create_application()
    with TestClient(application) as client:
        html = client.get("/").text
        assert 'rel="icon"' in html
        assert "favicon.svg" in html
        assert "/favicon.ico" in html


def test_favicon_route_excluded_from_openapi_schema():
    application = create_application()
    spec = application.openapi()
    assert "/favicon.ico" not in spec["paths"]
