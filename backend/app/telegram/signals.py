import asyncio
from contextlib import suppress

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
from telegram.handlers import service_commands, commands, checklist
from telegram.middlewares.outer.logging import TelegramLoggingMiddleware
from telegram.middlewares.outer.user import UserMiddleware


polling_task: asyncio.Task | None = None


async def aiogram_startup() -> None:
    global polling_task
    bot = await container.get(Bot)
    dispatcher = await container.get(Dispatcher)
    logger.info("Setting up middlewares")
    outer_middlewares = getattr(
        dispatcher.update.outer_middleware,
        "middlewares",
        [],
    )
    if not any(isinstance(middleware, TelegramLoggingMiddleware) for middleware in outer_middlewares):
        dispatcher.update.outer_middleware.register(TelegramLoggingMiddleware())
    if not any(isinstance(middleware, UserMiddleware) for middleware in outer_middlewares):
        dispatcher.update.outer_middleware.register(UserMiddleware())
    logger.info("Setting up routers and di")
    dispatcher.include_router(service_commands.router)
    dispatcher.include_router(commands.router)
    dispatcher.include_router(checklist.router)
    setup_dishka_aiogram(container, dispatcher, auto_inject=True)
    inject_router_aiogram(dispatcher)
    if telegram_settings.TELEGRAM_USE_WEBHOOK:
        logger.info("Configuring webhook mode for Telegram bot")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info(f"Setting webhook to {telegram_settings.webhook_url}")
        await bot.set_webhook(
            url=str(telegram_settings.webhook_url),
            secret_token=telegram_settings.TELEGRAM_SECRET_TOKEN.get_secret_value(),
        )
    else:
        logger.info("Starting polling mode for Telegram bot")
        await bot.delete_webhook(drop_pending_updates=True)
        polling_task = asyncio.create_task(dispatcher.start_polling(bot))
    if core_settings.DEBUG:
        return
    async with container(scope=Scope.REQUEST) as request_container:
        telegram_service = await request_container.get(TelegramService)
        await telegram_service.send_message(
            chat_id=telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
            text="Приложение запущено",
        )


async def aiogram_shutdown() -> None:
    global polling_task
    logger.info("Shutting down aiogram")
    if telegram_settings.TELEGRAM_USE_WEBHOOK:
        bot = await container.get(Bot)
        await bot.delete_webhook(drop_pending_updates=True)
    elif polling_task is not None:
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task
        polling_task = None
    if core_settings.DEBUG:
        return
    async with container(scope=Scope.REQUEST) as request_container:
        telegram_service = await request_container.get(TelegramService)
        await telegram_service.send_message(
            chat_id=telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
            text="Приложение остановлено",
        )
