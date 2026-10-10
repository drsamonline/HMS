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
            if reported == expected:
                print(f"smoke-test ok: health {reported}")
                rc = 0
            else:
                print(f"smoke-test failed: health version {reported!r} != VERSION {expected!r}", file=sys.stderr)
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
    prepare_runtime()
    settings = get_settings()
    lan_discovery.start()
    logger.info("Starting HHMS server on %s:%s", settings.SERVER_HOST, settings.SERVER_PORT)
    try:
        uvicorn.run(
            app,
            host=settings.SERVER_HOST,
            port=int(settings.SERVER_PORT),
            log_level=settings.LOG_LEVEL.lower(),
            reload=False,
        )
    finally:
        lan_discovery.stop()


if __name__ == "__main__":
    run()

__all__ = ["run"]
