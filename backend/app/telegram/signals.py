from aiogram import Bot, Dispatcher
from core.config import core_settings
from core.logs import logger
from di import container
from dishka import Scope
from dishka.integrations.aiogram import (
    inject_router as inject_router_aiogram,
)
from dishka.integrations.aiogram import (
    setup_dishka as setup_dishka_aiogram,
)
from services.telegram import TelegramService
from telegram.config import telegram_settings
from telegram.handlers import service_commands
from telegram.middlewares.outer.user import UserMiddleware


async def aiogram_startup() -> None:
    bot = await container.get(Bot)
    dispatcher = await container.get(Dispatcher)
    await bot.delete_webhook()
    logger.info(f"Setting webhook to {telegram_settings.webhook_url}")
    await bot.set_webhook(
        url=str(telegram_settings.webhook_url),
        secret_token=telegram_settings.TELEGRAM_SECRET_TOKEN.get_secret_value(),
    )
    logger.info("Setting up middlewares")
    dispatcher.update.outer_middleware.register(UserMiddleware())
    logger.info("Setting up routers and di")
    dispatcher.include_router(service_commands.router)
    setup_dishka_aiogram(container, dispatcher, auto_inject=True)
    inject_router_aiogram(dispatcher)
    if core_settings.DEBUG:
        return
    async with container(scope=Scope.REQUEST) as request_container:
        telegram_service = await request_container.get(TelegramService)
        await telegram_service.send_message(
            chat_id=telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
            text="Приложение запущено",
        )


async def aiogram_shutdown() -> None:
    logger.info("Shutting down aiogram")
    logger.info("Unregistering middlewares")
    if core_settings.DEBUG:
        return
    async with container(scope=Scope.REQUEST) as request_container:
        telegram_service = await request_container.get(TelegramService)
        await telegram_service.send_message(
            chat_id=telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
            text="Приложение остановлено",
        )
