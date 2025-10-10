from asyncio import wait_for

from aiogram import Bot
from aiohttp import ClientSession
from core.config import core_settings
from core.logs import logger
from fastapi import status
from openai import AsyncOpenAI
from services.base import BaseService
from services.telegram import TelegramService
from shared.enums.health import HealthStatus
from shared.schemas.health import HealthStatusResponse, ServiceHealthStatus
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from telegram.config import telegram_settings


class HealthCheckService(BaseService):
    def __init__(
        self,
        db_session: AsyncSession,
        openai_session: AsyncOpenAI,
        telegram_service: TelegramService,
        aiohttp_client_session: ClientSession,
        bot: Bot,
    ) -> None:
        self.db_session = db_session
        self.openai_session = openai_session
        self.telegram_service = telegram_service
        self.aiohttp_client_session = aiohttp_client_session
        self.bot = bot
        self._timeout = 5.0

    async def _check_db(self) -> tuple[HealthStatus, str | None]:
        try:
            await self.db_session.execute(text("SELECT 1"))
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Error checking database: {e}", exc_info=e)
            return HealthStatus.FAIL, None
        return HealthStatus.OK, None

    async def _check_openai(self) -> tuple[HealthStatus, str | None]:
        if core_settings.OPENAI_API_TOKEN is None:
            return HealthStatus.SHUTDOWN, "OpenAI API token is not set"
        try:
            await wait_for(
                self.openai_session.models.list(),
                timeout=self._timeout,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Error checking openai: {e}", exc_info=e)
            return HealthStatus.FAIL, None
        return HealthStatus.OK, None

    async def _check_frontend(self) -> tuple[HealthStatus, str | None]:
        try:
            response = await self.aiohttp_client_session.get(
                core_settings.frontend_url,
            )
            if response.status == status.HTTP_502_BAD_GATEWAY:
                return (
                    HealthStatus.FAIL,
                    f"Bad Gateway {core_settings.frontend_url}",
                )
            response.raise_for_status()
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Error checking frontend: {e}", exc_info=e)
            return HealthStatus.FAIL, None
        return HealthStatus.OK, None

    async def _check_telegram(self) -> tuple[HealthStatus, str | None]:
        if telegram_settings.TELEGRAM_BOT_TOKEN is None:
            return HealthStatus.SHUTDOWN, "Telegram bot token is not set"
        try:
            await wait_for(self.bot.get_me(), timeout=self._timeout)
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Error checking telegram: {e}", exc_info=e)
            return HealthStatus.FAIL, None
        return HealthStatus.OK, None

    @property
    def status_icon_map(self) -> dict[HealthStatus, str]:
        return {
            HealthStatus.OK: "🟢",
            HealthStatus.FAIL: "🔴",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.CRITICAL: "💀",
            HealthStatus.SHUTDOWN: "⚪️",
        }

    @property
    def overall_icon_map(self) -> dict[HealthStatus, str]:
        return {
            HealthStatus.OK: "⚡️",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.CRITICAL: "‼️",
        }

    async def process_health_overall(self) -> None:
        result_text = ""
        result = await self.check()
        for service in result.services:
            icon = self.status_icon_map.get(service.status, "❓")
            message = f"[{service.message}]" if service.message else ""
            result_text += "🔹 "
            result_text += (
                f"{service.name}: {icon} {service.status} {message}"
            ).strip()
            result_text += "\n"
        icon = self.status_icon_map[result.overall]
        overall_icon = self.overall_icon_map[result.overall]
        result_text += (
            f"\n{overall_icon} Общее состояние: {icon} {result.overall}"
        )
        await self.telegram_service.send_message(
            chat_id=telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
            text=result_text,
        )

    async def check(self) -> HealthStatusResponse:
        db_status, db_message = await self._check_db()
        openai_status, openai_message = await self._check_openai()
        telegram_status, telegram_message = await self._check_telegram()
        frontend_status, frontend_message = await self._check_frontend()
        return HealthStatusResponse(
            database=ServiceHealthStatus(
                status=db_status,
                message=db_message,
                name="Database",
            ),
            openai=ServiceHealthStatus(
                status=openai_status,
                message=openai_message,
                name="OpenAI",
            ),
            telegram=ServiceHealthStatus(
                status=telegram_status,
                message=telegram_message,
                name="Telegram",
            ),
            frontend=ServiceHealthStatus(
                status=frontend_status,
                message=frontend_message,
                name="Frontend",
            ),
        )
