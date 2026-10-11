"""OpenAPI schema generation regression tests.

Guards against route definitions that break /openapi.json (e.g. an explicit
``response_class=None`` on a decorator), which surfaces in Swagger UI as
"Failed to load API definition".
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.app import create_application


def test_openapi_schema_generates_without_error():
    application = create_application()
    spec = application.openapi()  # must not raise
    assert spec["openapi"].startswith("3.")
    assert len(spec["paths"]) > 100


def test_openapi_json_endpoint_serves_spec():
    application = create_application()
    with TestClient(application) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        body = resp.json()
        assert "/api/v1/maintenance/report-schedules/{job_id}" in body["paths"]
        delete_op = body["paths"]["/api/v1/maintenance/report-schedules/{job_id}"]["delete"]
        assert "204" in delete_op["responses"]


def test_docs_page_available():
    application = create_application()
    with TestClient(application) as client:
        assert client.get("/docs").status_code == 200
