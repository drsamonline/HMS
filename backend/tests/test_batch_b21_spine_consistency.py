"""Gate test for build-plan batch B21: the configuration spine holds together.

B12, B13, B16, B18 and B19 each added a catalogue and each tested itself. This
file tests them against each other, because the failure that matters is not a
broken catalogue - it is two correct catalogues that disagree.

Four questions, each of which has a wrong answer that no single catalogue could
detect:

1. Does every permission a route declares exist?
2. Does every permission a module claims exist, and is it used by something?
3. Does every navigation entry name a module and a permission that exist?
4. Is every setting reachable through the API the wizard will call?

A green run here is the gate for wave 3. The wizard is built on this, and a
disagreement would surface as a settings screen that silently omits a value or a
menu entry that opens nothing.
"""

from __future__ import annotations

import pytest

from app.api.v1.api import MODULE_ROUTERS, api_router
from app.core.permissions import CODES
from app.core.settings_catalogue import BY_KEY
from app.dependencies.permissions import (
    AUTHENTICATED_ONLY_PATHS,
    PUBLIC_PATHS,
    route_permission,
)
from app.modules.navigation import NAV_ITEMS
from app.modules.registry import BY_CODE, MODULES


# --------------------------------------------------------- 1. routes -> codes
def test_every_route_permission_exists() -> None:
    unknown = []
    for route in api_router.routes:
        code = route_permission(route)
        if code and code not in CODES:
            unknown.append((getattr(route, "path", "?"), code))
    assert not unknown, f"routes guarded by codes the catalogue does not declare: {unknown}"


def test_every_imported_router_is_in_the_module_map() -> None:
    """An endpoint file that is written and never mounted is dead code.

    Checked by reading the import list in ``api.py`` rather than by comparing
    route objects: FastAPI copies routes into the parent router, so identity does
    not survive the include.
    """

    import re
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "api.py"
    ).read_text(encoding="utf-8")

    imported = set(
        re.findall(
            r"from app\.api\.v1\.endpoints\.[a-z_0-9]+ import router as (\w+)",
            source,
        )
    )
    # APIRouter carries no __name__, so the map is rebuilt from the import list:
    # a router is mounted if its variable name appears in the module map's source.
    map_source = (
        Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "api.py"
    ).read_text(encoding="utf-8")
    block = map_source[map_source.index("MODULE_ROUTERS") :]
    block = block[: block.index("for module_code, routers in MODULE_ROUTERS")]
    mounted = set(re.findall(r"\b(\w+_router)\b", block))

    missing = imported - mounted
    assert not missing, (
        f"these routers are imported but belong to no module, so no gate or switch "
        f"applies to them: {sorted(missing)}"
    )


# ------------------------------------------------------- 2. modules -> codes
def test_every_module_permission_exists() -> None:
    for module in MODULES:
        unknown = [code for code in module.permissions if code not in CODES]
        assert not unknown, f"{module.code} claims undeclared permissions: {unknown}"


def test_every_module_owns_at_least_one_permission() -> None:
    """A module with no permissions is a switch that changes nothing."""

    for module in MODULES:
        assert module.permissions, f"{module.code} declares no permissions"


def test_no_permission_is_orphaned() -> None:
    """Every code is either checked by a route or owned by a module.

    An orphan is a permission an administrator can grant that opens nothing - the
    most confusing thing a permission screen can contain.
    """

    owned = {code for module in MODULES for code in module.permissions}
    routed = {
        code
        for route in api_router.routes
        if (code := route_permission(route)) is not None
    }
    orphans = set(CODES) - owned - routed
    assert not orphans, f"permissions nothing checks and no module owns: {sorted(orphans)}"


# ----------------------------------------------------- 3. navigation -> both
def test_every_navigation_entry_names_a_module_and_a_permission() -> None:
    for item in NAV_ITEMS:
        assert item.module in BY_CODE, f"{item.view} names unknown module {item.module}"
        if item.permission is not None:
            assert item.permission in CODES, (
                f"{item.view} requires {item.permission}, which does not exist"
            )


def test_every_navigation_permission_is_owned_by_its_module() -> None:
    """A menu entry should not need a permission its own module does not grant."""

    for item in NAV_ITEMS:
        if item.permission is None:
            continue
        owned = set(BY_CODE[item.module].permissions)
        if item.permission not in owned:
            # core owns the cross-cutting read codes; anything else is a smell
            assert item.module == "core", (
                f"{item.view} sits under {item.module} but needs {item.permission}, "
                "which that module does not grant"
            )


# --------------------------------------------- 4. settings reachable via API
def _admin() -> dict:
    from tests._qa_harness import auth_headers

    return auth_headers()


@pytest.fixture()
def isolated(monkeypatch):
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


def test_every_setting_is_reachable_through_the_api(isolated) -> None:
    from tests._qa_harness import make_client

    with make_client() as client:
        response = client.get("/api/v1/configuration", headers=_admin())

    assert response.status_code == 200, response.text
    returned = {row["key"] for row in response.json()}
    assert returned == set(BY_KEY), (
        f"the API omits {sorted(set(BY_KEY) - returned)} and invents "
        f"{sorted(returned - set(BY_KEY))}"
    )


def test_every_setting_the_wizard_can_offer_is_writable(isolated) -> None:
    """Bootstrap keys are excluded by design; everything else must accept a write."""

    from app.core.settings_catalogue import editable_in_database
    from tests._qa_harness import make_client

    writable = {spec.key for spec in editable_in_database()}

    with make_client() as client:
        response = client.get("/api/v1/configuration", headers=_admin())
        rows = {row["key"]: row for row in response.json()}

    for key in writable:
        assert rows[key]["bootstrap"] is False, f"{key} is writable but flagged bootstrap"

    bootstrap = {spec.key for spec in BY_KEY.values() if spec.bootstrap}
    assert bootstrap & writable == set(), "a bootstrap key leaked into the writable set"
