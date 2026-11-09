"""Gate tests for build-plan batch B19: the settings catalogue.

The gate the build plan names is reflection: every field the settings model
declares must appear in the catalogue, and every catalogue entry must be a real
field. A wizard built on a catalogue that has drifted from the model would offer a
setting the server ignores, or hide one it reads.

The precedence rule is tested too, because "where did this value come from" is the
question an administrator actually asks.
"""

from __future__ import annotations

import pytest

from app.config.settings import Settings
from app.core.settings_catalogue import (
    BY_KEY,
    GROUPS,
    SETTINGS,
    SOURCE_DATABASE,
    SOURCE_DEFAULT,
    SOURCE_ENV,
    editable_in_database,
    in_group,
)

FIELDS = set(Settings.model_fields)


# ------------------------------------------------------------- the reflection
def test_every_settings_field_is_in_the_catalogue() -> None:
    missing = FIELDS - set(BY_KEY)
    assert not missing, (
        f"these settings exist but are not described, so no wizard can offer "
        f"them: {sorted(missing)}"
    )


def test_every_catalogue_entry_is_a_real_settings_field() -> None:
    extra = set(BY_KEY) - FIELDS
    assert not extra, (
        f"the catalogue describes settings the server does not read: {sorted(extra)}"
    )


def test_keys_are_unique() -> None:
    keys = [spec.key for spec in SETTINGS]
    assert len(keys) == len(set(keys))


# --------------------------------------------------------------- the metadata
def test_every_setting_is_in_a_known_group() -> None:
    for spec in SETTINGS:
        assert spec.group in GROUPS, f"{spec.key} has group {spec.group!r}"


def test_every_setting_has_a_label_and_a_description() -> None:
    for spec in SETTINGS:
        assert spec.label.strip(), spec.key
        assert spec.description.strip(), spec.key
        assert len(spec.description) >= 15, (
            f"{spec.key} needs a description an administrator can act on, "
            f"not {spec.description!r}"
        )


def test_every_setting_has_a_known_type() -> None:
    allowed = {"string", "integer", "boolean", "decimal", "list", "secret"}
    for spec in SETTINGS:
        assert spec.type in allowed, f"{spec.key} has type {spec.type!r}"


def test_choices_are_only_declared_where_they_apply() -> None:
    for spec in SETTINGS:
        if spec.choices:
            assert spec.type in {"string", "integer"}, (
                f"{spec.key} declares choices on a {spec.type} setting"
            )
            assert spec.default is None or str(spec.default) in spec.choices, (
                f"{spec.key} defaults to {spec.default!r}, which is not one of its choices"
            )


def test_secrets_are_marked_as_such() -> None:
    """A secret typed into a settings screen must not be echoed back."""

    for key in ("SECRET_KEY", "WHO_ICD11_CLIENT_SECRET"):
        assert BY_KEY[key].type == "secret", f"{key} must be typed as a secret"


def test_bootstrap_settings_are_declared_and_few() -> None:
    """These are read before the database opens; the wizard cannot store them."""

    bootstrap = {spec.key for spec in SETTINGS if spec.bootstrap}
    assert bootstrap == {
        "SERVER_PORT",
        "DISCOVERY_ENABLED",
        "DISCOVERY_PORT",
        "DISCOVERY_NAME",
        "SECRET_KEY",
        "DATABASE_URL",
    }, sorted(bootstrap)
    for key in bootstrap:
        assert BY_KEY[key].restart_required, (
            f"{key} is bootstrap and must be marked restart-required"
        )


def test_editable_in_database_excludes_bootstrap() -> None:
    editable = {spec.key for spec in editable_in_database()}
    assert not (editable & {spec.key for spec in SETTINGS if spec.bootstrap})


def test_grouping_covers_every_setting_exactly_once() -> None:
    grouped = [spec.key for group in GROUPS for spec in in_group(group)]
    assert sorted(grouped) == sorted(BY_KEY)


def test_an_unknown_group_is_refused() -> None:
    with pytest.raises(KeyError):
        in_group("dentistry")


# ------------------------------------------------------------- the precedence
@pytest.fixture()
def database(tmp_path, monkeypatch):
    import asyncio

    import app.models  # noqa: F401
    from app.config import settings as settings_module
    from app.db import session as session_module
    from app.db.base import Base
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    path = tmp_path / "hhms-b19.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{path.as_posix()}")
    monkeypatch.setenv("ENVIRONMENT", "test")
    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")

    async def _create() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_create())
    finally:
        loop.close()

    yield async_sessionmaker(engine, expire_on_commit=False)

    settings_module.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()


def _run(coro):
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_an_untouched_setting_reports_where_its_value_came_from(database) -> None:
    """With no override, the value is the environment's or the catalogue default.

    Asserted against whatever this machine actually resolves rather than against
    the hardcoded default: a committed ``.env`` or a developer's shell can set any
    key, and the property under test is precedence, not the value on one machine.
    """

    from app.config.settings import get_settings
    from app.services.settings_store import effective

    async def _go():
        async with database() as db:
            return await effective(db, "DEFAULT_PAGE_SIZE")

    result = _run(_go())
    assert result.source in {SOURCE_DEFAULT, SOURCE_ENV}
    assert result.source != SOURCE_DATABASE
    assert result.value == get_settings().DEFAULT_PAGE_SIZE


def test_a_stored_value_wins_and_is_coerced(database) -> None:
    from app.services.settings_store import effective, set_value

    async def _go():
        async with database() as db:
            await set_value(db, "DEFAULT_PAGE_SIZE", 25, actor_id=1)
            await db.commit()
            return await effective(db, "DEFAULT_PAGE_SIZE")

    result = _run(_go())
    assert result.value == 25
    assert isinstance(result.value, int), "an integer setting must come back an int"
    assert result.source == SOURCE_DATABASE


def test_a_bad_value_is_refused_before_it_is_stored(database) -> None:
    from app.core.exceptions import BusinessRuleException
    from app.services.settings_store import set_value

    async def _go():
        async with database() as db:
            await set_value(db, "DEFAULT_PAGE_SIZE", "twenty-five")

    with pytest.raises(BusinessRuleException):
        _run(_go())


def test_a_choice_outside_the_list_is_refused(database) -> None:
    from app.core.exceptions import BusinessRuleException
    from app.services.settings_store import set_value

    async def _go():
        async with database() as db:
            await set_value(db, "PERMISSION_ENFORCEMENT", "sometimes")

    with pytest.raises(BusinessRuleException):
        _run(_go())


def test_a_bootstrap_setting_cannot_be_stored(database) -> None:
    """It is read before the database is open, so storing it would be a lie."""

    from app.core.exceptions import BusinessRuleException
    from app.services.settings_store import set_value

    async def _go():
        async with database() as db:
            await set_value(db, "SERVER_PORT", 9000)

    with pytest.raises(BusinessRuleException):
        _run(_go())


def test_resetting_returns_the_default(database) -> None:
    from app.services.settings_store import effective, reset_value, set_value

    async def _go():
        async with database() as db:
            await set_value(db, "LOG_RETENTION_DAYS", 90)
            await db.commit()
            await reset_value(db, "LOG_RETENTION_DAYS")
            await db.commit()
            return await effective(db, "LOG_RETENTION_DAYS")

    result = _run(_go())
    assert result.source == SOURCE_DEFAULT
    assert result.value == BY_KEY["LOG_RETENTION_DAYS"].default
