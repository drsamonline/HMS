"""HHMS standalone server launcher for packaged and source deployments."""
from __future__ import annotations

import logging

import uvicorn

from app.app import app
from app.config.settings import get_settings
from app.startup import prepare_runtime

logger = logging.getLogger("hhms.server")


def run() -> None:
    """Prepare the runtime and start the HHMS FastAPI server."""
    prepare_runtime()
    settings = get_settings()
    logger.info("Starting HHMS server on %s:%s", settings.SERVER_HOST, settings.SERVER_PORT)
    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=int(settings.SERVER_PORT),
        log_level=settings.LOG_LEVEL.lower(),
        reload=False,
    )


if __name__ == "__main__":
    run()

__all__ = ["run"]
