"""HHMS standalone server launcher for packaged and source deployments."""
from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
import urllib.request

import uvicorn

from app.app import app
from app.config.settings import get_settings
from app.network.discovery import lan_discovery
from app.release_version import release_version
from app.startup import prepare_runtime

logger = logging.getLogger("hhms.server")


def _first_run_problem(port: int, user_count: int) -> str | None:
    """Return why this build has no way in, or None when somebody can log in.

    A build with at least one account is fine.  A build with none is only fine if
    the setup wizard is open: that is the path a fresh install is meant to take.
    Without this check a portable build could ship with zero accounts, print a
    notice nobody reads, and pass its own smoke test - which is the definition of
    a test that proves nothing.
    """

    if user_count:
        return None
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/setup/status", timeout=5) as resp:
            status = json.loads(resp.read().decode())
    except Exception as exc:  # noqa: BLE001 - the answer is the finding
        return f"no administrator account and the setup gate is unreachable: {exc}"
    if status.get("setup_required") and not status.get("locked_out"):
        return None
    return (
        "no administrator account and the setup wizard is closed "
        f"(setup_required={status.get('setup_required')!r}, locked_out={status.get('locked_out')!r})"
    )


def _smoke_test() -> int:
    """Bootstrap the runtime in-process, serve briefly, probe /health.

    Used by CI (and operators) to validate a freshly built bundle without
    a manual start-and-poll cycle.  Exit code 0 means migrations ran, the
    server bound, and /health answered with the bundled release version.
    """
    parser = argparse.ArgumentParser(prog="HHMS-Server", add_help=True)
    parser.add_argument("--smoke-test", action="store_true", help="run first-build smoke probe and exit")
    args = parser.parse_args()

    if not args.smoke_test:
        print("unexpected arguments", file=sys.stderr)
        return 2

    prepare_runtime()
    # Mirror the real first-run path (run()) so the smoke probe validates
    # exactly what a portable build does on launch: bootstrap admin and seed
    # the demo dataset automatically.  Failures here must surface as a
    # non-zero smoke-test exit instead of silently shipping broken builds.
    #
    # "Bootstrap admin" is not a given: since F-01 the bootstrap creates an
    # account only when a password was supplied, so a build can ship with no
    # account at all.  The count is therefore checked below against the one
    # path that still lets somebody in - the setup wizard.
    from app.cli.create_admin import ensure_default_admin

    user_count = ensure_default_admin()
    from app.cli.seed_demo_data import seed_demo_on_first_run

    seed_demo_on_first_run()
    settings = get_settings()
    host, port = settings.SERVER_HOST, int(settings.SERVER_PORT)
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}/api/v1/health"
    deadline = time.time() + 30
    rc = 1
    while time.time() < deadline:
        if not server.started:
            time.sleep(0.2)
            continue
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                payload = json.loads(resp.read().decode())
            expected = release_version()
            reported = str(payload.get("version", ""))
            if reported != expected:
                print(f"smoke-test failed: health version {reported!r} != VERSION {expected!r}", file=sys.stderr)
                break
            problem = _first_run_problem(port, user_count)
            if problem:
                print(f"smoke-test failed: {problem}", file=sys.stderr)
                break
            print(f"smoke-test ok: health {reported}")
            rc = 0
            break
        except Exception as exc:  # noqa: BLE001 - retry until server up
            last = exc
            time.sleep(0.5)
    else:
        print(f"smoke-test timed out waiting for {url}: {last}", file=sys.stderr)

    server.should_exit = True
    thread.join(timeout=10)
    return rc


def run() -> None:
    """Prepare the runtime and start the HHMS FastAPI server."""
    if "--smoke-test" in sys.argv:
        raise SystemExit(_smoke_test())
    if len(sys.argv) > 1 and sys.argv[1] == "create-admin":
        from app.cli.create_admin import main as create_admin_main

        raise SystemExit(create_admin_main(sys.argv[2:]))
    if len(sys.argv) > 1 and sys.argv[1] == "seed-demo-data":
        # OOBE shortcut: bootstrap migrations + the first administrator (only
        # when HHMS_ADMIN_INITIAL_PASSWORD is set), then seed the demo dataset
        # (idempotent; refuses to touch databases with real data unless --force
        # is given).
        prepare_runtime()
        try:
            from app.cli.create_admin import ensure_default_admin

            ensure_default_admin()
        except Exception:  # pragma: no cover - never block seeding on bootstrap
            logger.exception("default admin bootstrap failed (continuing)")
        from app.cli.seed_demo_data import main as seed_demo_main

        raise SystemExit(seed_demo_main(sys.argv[2:]))
    prepare_runtime()
    # First-run convenience: create the administrator from
    # HHMS_ADMIN_INITIAL_PASSWORD so a fresh build is testable out of the box.
    # No default password is ever created (F-01); with no password configured
    # the bootstrap leaves the account to the /setup wizard and says so. No-op
    # once any user exists; disable with HHMS_BOOTSTRAP_DEFAULT_ADMIN=false.
    try:
        from app.cli.create_admin import ensure_default_admin

        ensure_default_admin()
    except Exception:  # pragma: no cover - never block boot on bootstrap
        logger.exception("default admin bootstrap failed (continuing startup)")
    # Out-of-the-box demo dataset (year 2025) for portable builds: seeds
    # automatically on a pristine database so the GUI is populated without
    # any commands.  Databases that already contain real data are never
    # touched; disable with HHMS_SEED_DEMO_DATA=false.
    try:
        import os as _os

        _flag = _os.environ.get("HHMS_SEED_DEMO_DATA", "").strip().lower()
        if _flag not in {"false", "0", "no"}:
            from app.cli.seed_demo_data import seed_demo_on_first_run

            if seed_demo_on_first_run():
                logger.info("Demo data (year 2025) seeded automatically on first run.")
    except Exception:  # pragma: no cover - never block boot on demo seeding
        logger.exception("demo data seeding failed (continuing startup)")
    try:
        from app.cli.seed_demo_data import maybe_seed_from_env

        maybe_seed_from_env()
    except Exception:  # pragma: no cover - never block boot on demo seeding
        logger.exception("demo data env seeding failed (continuing startup)")
    settings = get_settings()
    lan_discovery.start()
    logger.info("Starting HHMS server on %s:%s", settings.SERVER_HOST, settings.SERVER_PORT)

    # Packaged Windows builds: hide the raw command window and replace it
    # with the tray + live-log desktop console (close → minimise to tray,
    # right-click "Exit Server" → graceful shutdown + data draft saver).
    from app.desktop_console import maybe_start_desktop_console, save_draft_on_exit

    desktop = maybe_start_desktop_console()
    config = uvicorn.Config(
        app,
        host=settings.SERVER_HOST,
        port=int(settings.SERVER_PORT),
        log_level=settings.LOG_LEVEL.lower(),
        reload=False,
    )
    server = uvicorn.Server(config)

    if desktop is not None:
        def _graceful_exit() -> None:
            # 1. Ask uvicorn to stop accepting work and shut down cleanly.
            try:
                server.should_exit = True
            except Exception:  # pragma: no cover - defensive
                pass
            # 2. Wait (bounded) for the serve loop to unwind so in-flight
            #    writes commit before we snapshot the database.
            deadline = time.time() + 8
            while time.time() < deadline and server.started:
                time.sleep(0.2)
            # 3. Data draft saver: rolling backup of the live DB on exit.
            save_draft_on_exit()
            # 4. Stop the UDP discovery responder.
            lan_discovery.stop()

        desktop.on_exit = _graceful_exit
        threading.Thread(
            target=desktop.start, name="hhms-desktop-console", daemon=True
        ).start()

    try:
        server.run()
    finally:
        lan_discovery.stop()
        if desktop is not None:
            # Process is exiting by other means (Ctrl+C, service stop):
            # still save a final data draft so nothing entered is lost.
            save_draft_on_exit()


if __name__ == "__main__":
    run()

__all__ = ["run"]
