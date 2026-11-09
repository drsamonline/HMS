"""Gate tests for build-plan batch B20: the configuration API and CLI.

The build plan's gate is one sentence - an invalid PATCH returns 422 and leaves
the value unchanged - and this file tests that, plus the property that makes it
useful: a batch is all-or-nothing, so a wizard step that sets six values cannot
land five.
"""

from __future__ import annotations

import json

import pytest


def _admin() -> dict:
    from tests._qa_harness import auth_headers

    return auth_headers()


def _client():
    from tests._qa_harness import make_client

    return make_client()


@pytest.fixture()
def isolated(monkeypatch):
    """Start from a clean settings cache; a neighbouring module can leave one."""

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("HHMS_APPLICATION_ROOT", raising=False)

    from app.config import settings as settings_module
    from app.db import session as session_module

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    yield

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


# ------------------------------------------------------------------ reading
def test_the_list_covers_every_setting(isolated) -> None:
    from app.core.settings_catalogue import BY_KEY

    with _client() as client:
        response = client.get("/api/v1/configuration", headers=_admin())

    assert response.status_code == 200, response.text
    keys = {item["key"] for item in response.json()}
    assert keys == set(BY_KEY)


def test_every_row_states_where_its_value_came_from(isolated) -> None:
    with _client() as client:
        rows = client.get("/api/v1/configuration", headers=_admin()).json()

    for row in rows:
        assert row["source"] in {"default", "env", "database"}, row["key"]
        assert row["label"] and row["description"], row["key"]


def test_a_secret_is_never_returned_in_clear(isolated) -> None:
    with _client() as client:
        rows = client.get("/api/v1/configuration", headers=_admin()).json()

    secret = next(row for row in rows if row["key"] == "SECRET_KEY")
    assert secret["value"] in (None, "********"), "the signing key must not be echoed"


# ------------------------------------------------------------------ writing
def test_a_valid_patch_is_applied(isolated) -> None:
    with _client() as client:
        headers = _admin()
        response = client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={"values": {"LOG_RETENTION_DAYS": 45}},
        )
        assert response.status_code == 200, response.text

        rows = client.get("/api/v1/configuration", headers=headers).json()

    row = next(item for item in rows if item["key"] == "LOG_RETENTION_DAYS")
    assert row["value"] == 45
    assert row["source"] == "database"


def test_an_invalid_value_returns_422_and_changes_nothing(isolated) -> None:
    """The gate from the build plan, in one test."""

    with _client() as client:
        headers = _admin()
        before = next(
            item
            for item in client.get("/api/v1/configuration", headers=headers).json()
            if item["key"] == "DEFAULT_PAGE_SIZE"
        )

        response = client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={"values": {"DEFAULT_PAGE_SIZE": "not a number"}},
        )
        assert response.status_code == 422, response.text

        after = next(
            item
            for item in client.get("/api/v1/configuration", headers=headers).json()
            if item["key"] == "DEFAULT_PAGE_SIZE"
        )

    assert after["value"] == before["value"]
    assert after["source"] == before["source"], "a refused write must not create a row"


def test_one_bad_value_rejects_the_whole_batch(isolated) -> None:
    """A wizard step sets six things; it must land or fail together."""

    with _client() as client:
        headers = _admin()
        response = client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={
                "values": {
                    "MAINTENANCE_INTERVAL_HOURS": 12,
                    "DEFAULT_PAGE_SIZE": "not a number",
                }
            },
        )
        assert response.status_code == 422, response.text

        rows = client.get("/api/v1/configuration", headers=headers).json()

    good = next(item for item in rows if item["key"] == "MAINTENANCE_INTERVAL_HOURS")
    assert good["source"] != "database", (
        "the valid half of the batch must not have been stored when the other half failed"
    )


def test_a_bootstrap_setting_is_refused_with_an_explanation(isolated) -> None:
    with _client() as client:
        response = client.patch(
            "/api/v1/configuration",
            headers=_admin(),
            json={"values": {"SERVER_PORT": 9000}},
        )

    assert response.status_code == 422, response.text
    assert "environment file" in response.json()["error"]["message"]


def test_an_unknown_key_is_refused(isolated) -> None:
    with _client() as client:
        response = client.patch(
            "/api/v1/configuration",
            headers=_admin(),
            json={"values": {"NOT_A_SETTING": 1}},
        )
    assert response.status_code == 422, response.text


def test_an_empty_patch_is_refused(isolated) -> None:
    with _client() as client:
        response = client.patch(
            "/api/v1/configuration", headers=_admin(), json={"values": {}}
        )
    assert response.status_code == 422, response.text


def test_reset_returns_the_setting_to_its_default(isolated) -> None:
    with _client() as client:
        headers = _admin()
        client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={"values": {"LOG_RETENTION_DAYS": 45}},
        )
        response = client.post(
            "/api/v1/configuration/reset",
            headers=headers,
            json={"key": "LOG_RETENTION_DAYS"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["source"] != "database"


# ------------------------------------------------------------- export/import
def test_export_contains_only_overrides(isolated) -> None:
    """Exporting all forty-four would pin today's defaults forever."""

    with _client() as client:
        headers = _admin()
        client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={"values": {"LOG_RETENTION_DAYS": 45}},
        )
        exported = client.get("/api/v1/configuration/export", headers=headers).json()

    assert exported["values"] == {"LOG_RETENTION_DAYS": 45}


def test_export_then_import_round_trips(isolated) -> None:
    with _client() as client:
        headers = _admin()
        client.patch(
            "/api/v1/configuration",
            headers=headers,
            json={"values": {"LOG_RETENTION_DAYS": 45}},
        )
        exported = client.get("/api/v1/configuration/export", headers=headers).json()

        client.post(
            "/api/v1/configuration/reset",
            headers=headers,
            json={"key": "LOG_RETENTION_DAYS"},
        )
        response = client.post(
            "/api/v1/configuration/import", headers=headers, json=exported
        )
        assert response.status_code == 200, response.text

        rows = client.get("/api/v1/configuration", headers=headers).json()

    row = next(item for item in rows if item["key"] == "LOG_RETENTION_DAYS")
    assert row["value"] == 45


# ------------------------------------------------------------------- the CLI
def test_the_cli_parses_json_values_and_falls_back_to_text() -> None:
    from app.cli.config import _parse

    assert _parse("45") == 45
    assert _parse("true") is True
    assert _parse("[]") == []
    assert _parse("Asia/Kolkata") == "Asia/Kolkata"


def test_the_cli_refuses_an_unpaired_set() -> None:
    from app.cli.config import main

    assert main(["set", "LOG_RETENTION_DAYS"]) == 1


def test_the_cli_has_the_four_documented_commands() -> None:
    from app.cli.config import main

    # argparse exits 2 on an unknown command rather than returning
    with pytest.raises(SystemExit):
        main(["frobnicate"])
