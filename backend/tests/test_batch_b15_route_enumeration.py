"""Gate test for build-plan batch B15: every route declares a guard, forever.

B14 guarded 245 routes by hand. A test that only proves today's routes are guarded
would pass the day after a new endpoint is added without one, so this one is
written to fail on the next route that arrives unprotected, with a message that
names it.

It supersedes the lighter check that shipped inside B14's gate; there is one
place to look now, and it is here.
"""

from __future__ import annotations

from collections import defaultdict

from app.api.v1.api import api_router
from app.core.permissions import CODES
from app.dependencies.permissions import (
    AUTHENTICATED_ONLY_PATHS,
    AUTHENTICATED_ONLY_PREFIXES,
    PUBLIC_PATHS,
    SETUP_PREFIX,
    route_permission,
)


#: Methods FastAPI adds to every route that are not real endpoints.
IGNORED_METHODS = {"HEAD", "OPTIONS"}


def _routes():
    """Every mounted v1 route, with its full path and methods."""

    for route in api_router.routes:
        path = getattr(route, "path", "")
        full = path if path.startswith("/api/") else f"/api/v1{path}"
        methods = {
            method.upper()
            for method in (getattr(route, "methods", None) or set())
            if method.upper() not in IGNORED_METHODS
        }
        if not methods:
            continue
        yield full, methods, route


def test_every_route_is_guarded_or_named_public() -> None:
    """The one that matters: an unguarded route fails, and is named."""

    unguarded: list[str] = []
    for full, methods, route in _routes():
        # Two deliberate exemptions: routes that work before a login, and routes
        # that need a login but no particular permission (a user's own menu).
        if full in PUBLIC_PATHS or full in AUTHENTICATED_ONLY_PATHS:
            continue
        if full.startswith(AUTHENTICATED_ONLY_PREFIXES):
            continue
        # The setup wizard runs before a user exists; it carries its own gate,
        # the setup code exchanged for a scoped token.
        if full.startswith(SETUP_PREFIX):
            continue
        if route_permission(route) is None:
            for method in sorted(methods):
                unguarded.append(f"{method} {full}")

    assert not unguarded, (
        "These routes declare no permission guard and would be refused under "
        "PERMISSION_ENFORCEMENT=enforce:\n  "
        + "\n  ".join(sorted(unguarded))
        + "\nAdd dependencies=[Depends(require(\"<code>\"))] to the decorator, "
        "or add the path to PUBLIC_PATHS with a reason."
    )


def test_every_declared_code_exists_in_the_catalogue() -> None:
    """A guard on an undeclared code would refuse everybody, silently."""

    unknown: dict[str, list[str]] = defaultdict(list)
    for full, methods, route in _routes():
        code = route_permission(route)
        if code and code not in CODES:
            for method in sorted(methods):
                unknown[code].append(f"{method} {full}")

    assert not unknown, f"routes guarded by codes the catalogue does not declare: {dict(unknown)}"


def test_the_exemption_lists_contain_nothing_that_is_not_mounted() -> None:
    """A stale entry in either list is a hole nobody would notice."""

    mounted = {full for full, _methods, _route in _routes()}
    for name, paths in (
        ("PUBLIC_PATHS", PUBLIC_PATHS),
        ("AUTHENTICATED_ONLY_PATHS", AUTHENTICATED_ONLY_PATHS),
    ):
        missing = paths - mounted
        assert not missing, f"{name} names routes that do not exist: {sorted(missing)}"


def test_the_authenticated_only_list_stays_small() -> None:
    """Routes that need a login but no permission are rare and deliberate.

    The cap is a ratchet, not a rule of nature: it moves when a route genuinely
    belongs here, and the reason has to be written next to it. Each of these returns
    something about the caller - their menu, their home, their help, their first run -
    and none of them exposes hospital data.
    """

    expected = {
        "/api/v1/navigation",  # the caller's own menu
        "/api/v1/home",        # the caller's own landing screen
        "/api/v1/help",        # guidance for the caller
        "/api/v1/tutorial",    # the caller's own progress through the first run
    }
    assert set(AUTHENTICATED_ONLY_PATHS) <= expected, sorted(AUTHENTICATED_ONLY_PATHS)
    assert len(AUTHENTICATED_ONLY_PATHS) <= 4, sorted(AUTHENTICATED_ONLY_PATHS)


def test_no_route_is_public_and_guarded_at_once() -> None:
    """Contradictory intent is worse than either choice."""

    contradictions = []
    for full, _methods, route in _routes():
        exempt = (
            full in PUBLIC_PATHS
            or full in AUTHENTICATED_ONLY_PATHS
            or full.startswith(SETUP_PREFIX)
        )
        if exempt and route_permission(route) is not None:
            contradictions.append(full)
    assert not contradictions, (
        f"{sorted(contradictions)} are listed public but declare a guard. Pick one."
    )


def test_coverage_is_reported_by_prefix() -> None:
    """Not an assertion about behaviour: a shape check that the guard is spread.

    A single module accidentally left unguarded would already fail the first
    test. This one catches the subtler case where the guard exists but the whole
    of one prefix is missing, which the first test would also catch - so what it
    really asserts is that no prefix is *entirely* public by accident.
    """

    guarded: dict[str, int] = defaultdict(int)
    unguarded: dict[str, int] = defaultdict(int)
    for full, _methods, route in _routes():
        prefix = "/".join(full.split("/")[:4])
        if route_permission(route) is not None:
            guarded[prefix] += 1
        elif (
            full not in PUBLIC_PATHS
            and full not in AUTHENTICATED_ONLY_PATHS
            and not full.startswith(SETUP_PREFIX)
            and not full.startswith(AUTHENTICATED_ONLY_PREFIXES)
        ):
            unguarded[prefix] += 1

    assert sum(guarded.values()) >= 200, (
        f"only {sum(guarded.values())} guarded routes; the count collapsed, "
        "which means guards were lost rather than routes removed"
    )
    assert not unguarded, f"unguarded by prefix: {dict(unguarded)}"


def test_no_duplicate_path_and_method() -> None:
    """Two routes on the same path and verb: the first wins, the second is dead."""

    seen: dict[tuple[str, str], int] = {}
    duplicates = []
    for full, methods, _route in _routes():
        for method in methods:
            key = (full, method)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] == 2:
                duplicates.append(f"{method} {full}")
    assert not duplicates, f"duplicate routes: {sorted(duplicates)}"
