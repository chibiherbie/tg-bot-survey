import asyncio
from pathlib import Path

from core.config import core_settings
from core.logs import logger
from granian.constants import Interfaces
from granian.server import Server as Granian


async def main():
    logger.info("Starting Backend Server")
    server = Granian(
        "asgi.app:create_app",
        interface=Interfaces.ASGI,
        address="0.0.0.0",  # noqa: S104
        port=core_settings.BACKEND_PORT,
        log_enabled=False,
        factory=True,
        reload=core_settings.DEBUG,
        workers=core_settings.WORKERS,
        reload_ignore_dirs=["__pycache__"],
        reload_ignore_patterns=[r".*\.pyc", r".*\.log"],
        reload_paths=[Path(__file__).resolve().parent],
    )
    server.serve()
    logger.info("Server Shutting Down")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
