from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from api import auth, debug, health, telegram, user
from api.processing import health as health_processing
from api.processing import mailings
from asgi.dependence.security import backend_token_depends
from asgi.middlewares.logs import LoggingMiddleware
from core.config import core_settings
from core.logs import logger
from di import container
from dishka.integrations.fastapi import (
    DishkaRoute,
)
from dishka.integrations.fastapi import (
    setup_dishka as setup_fastapi_dishka,
)
from fastapi import APIRouter, FastAPI
from shared.utils.process_runner import ProcessRunner
from telegram.signals import aiogram_shutdown, aiogram_startup


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting Application")
    await aiogram_startup()
    yield
    logger.info("Shutting down Application")
    await aiogram_shutdown()
    bg_process_runner = await container.get(ProcessRunner)
    await bg_process_runner.shutdown()


def init_routers(app: FastAPI) -> None:
    base_router = APIRouter(prefix="/api", route_class=DishkaRoute)
    v1_router = APIRouter(prefix="/v1", tags=["v1"], route_class=DishkaRoute)
    processing_router = APIRouter(
        prefix="/processing",
        tags=["processing"],
        route_class=DishkaRoute,
        dependencies=[backend_token_depends],
    )
    if core_settings.DEBUG:
        base_router.include_router(debug.router)
    v1_router.include_router(telegram.router)
    v1_router.include_router(auth.router)
    v1_router.include_router(user.router)
    processing_router.include_router(mailings.router)
    processing_router.include_router(health_processing.router)
    base_router.include_router(v1_router)
    base_router.include_router(health.router)
    base_router.include_router(processing_router)
    app.include_router(base_router)


def init_middlewares(app: FastAPI) -> None:
    setup_fastapi_dishka(container, app)
    app.add_middleware(LoggingMiddleware)


def create_app() -> FastAPI:
    app = FastAPI(
        debug=core_settings.DEBUG,
        root_path="/backend",
        redirect_slashes=False,
        lifespan=lifespan,
        include_in_schema=core_settings.DEBUG,
    )
    init_middlewares(app)
    init_routers(app)
    return app
