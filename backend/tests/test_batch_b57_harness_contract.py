"""The harness's own contract.

Two things were expensive and one of them was dangerous, so both are pinned here:

* **Isolation.** Every ``make_client()`` block must start from an empty database. The
  optimisation reuses one engine and empties the tables, which is only safe if the
  emptying actually happens - a block that inherited the previous block's rows would
  produce tests that pass in isolation and fail in company, or worse, the reverse.
* **The application is reused.** That is where four seconds per block went, and the one
  piece of state that made reuse unsafe - the login throttle's counters - is reset per
  block. A test asserts that too, because a suite that starts refusing honest logins
  would look like a security bug in the product.
"""

from __future__ import annotations

# Imported as a module, not as names: these are set when the application is first
# built, which is after this file is imported.
from tests import _qa_harness
from tests._qa_harness import make_client


def test_a_block_starts_from_an_empty_database() -> None:
    """The property the optimisation must not break."""

    from tests._qa_harness import auth_headers, seed_number_sequence

    with make_client() as client:
        seed_number_sequence(sequence_name="patient_number", prefix="P-")
        headers = auth_headers()
        created = client.post(
            "/api/v1/patients",
            headers=headers,
            json={"first_name": "Isolation", "last_name": "Check", "gender": "female"},
        )
        assert created.status_code in {200, 201}, created.text
        assert client.get("/api/v1/patients", headers=headers).json()

    with make_client() as client:
        headers = auth_headers()
        # The previous block's patient must be gone.
        assert client.get("/api/v1/patients", headers=headers).json() == []


def test_the_application_is_built_once() -> None:
    """Four seconds a block was the second half of this suite's fixed cost."""

    from tests import _qa_harness

    with make_client() as client:
        first = client.app

    with make_client() as client:
        second = client.app

    assert first is second
    assert _qa_harness._APPLICATION is first


def test_the_login_throttle_starts_clean_in_every_block() -> None:
    """A reused application would accumulate every login the suite ever made."""

    from tests._qa_harness import auth_headers

    with make_client() as client:
        headers = auth_headers()
        for _ in range(5):
            assert client.get("/api/v1/patients", headers=headers).status_code == 200

    assert _qa_harness._LIMITER is not None
    # The counter is emptied at the start of each block, so anything left here is
    # from *this* block only - not an accumulation across the suite.
    with make_client():
        pass
    assert not _qa_harness._LIMITER._hits, "the throttle carried hits into the next block"


def test_a_block_after_a_file_backed_one_still_works(tmp_path) -> None:
    """The failure that made the first attempt at this unshippable.

    ``make_file_client`` points the application at its own database and puts it back
    afterwards. A shared engine that no longer matches what the application resolves
    leaves the harness preparing a database nothing is looking at.
    """

    from tests._qa_harness import auth_headers, make_file_client

    db_path = str(tmp_path / "lan.sqlite3")
    with make_file_client(db_path) as (client_factory, dispose):
        client = client_factory()
        assert client.get("/api/v1/patients", headers=auth_headers()).status_code == 200
        dispose()

    with make_client() as client:
        response = client.get("/api/v1/patients", headers=auth_headers())

    assert response.status_code == 200, response.text
    assert response.json() == []


def test_the_schema_is_rebuilt_when_a_table_is_missing() -> None:
    """A schema built before every model was imported is a schema with a hole in it."""

    from tests import _qa_harness

    with make_client():
        pass

    # Pretend a model was registered after the schema was built.
    _qa_harness._SHARED["ready"] = False
    with make_client() as client:
        from tests._qa_harness import auth_headers

        assert client.get("/api/v1/patients", headers=auth_headers()).status_code == 200
    assert _qa_harness._SHARED["ready"] is True
