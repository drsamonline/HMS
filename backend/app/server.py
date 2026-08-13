"""HHMS standalone server launcher for packaged and source deployments."""
from __future__ import annotations

import uvicorn

from app.app import app
from app.config.settings import get_settings


def run() -> None:
    """Start the HHMS FastAPI server using configured LAN settings."""
    settings = get_settings()
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
