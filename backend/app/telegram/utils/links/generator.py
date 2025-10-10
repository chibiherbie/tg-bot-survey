from aiogram import Bot
from aiogram.types import WebAppInfo
from core.config import core_settings
from di.container import container
from telegram.config import telegram_settings
from telegram.utils.links.schemas import StartParamSchema


def get_web_app(start_param: StartParamSchema) -> WebAppInfo:
    url = core_settings.frontend_url
    return str(
        WebAppInfo(url=url.with_query(start_param.model_dump(mode="json"))),
    )


async def get_bot_web_app_link(start_param: StartParamSchema) -> str:
    bot = await container.get(Bot)
    bot_me = await bot.get_me()
    url = telegram_settings.telegram_url / bot_me.username / "menu"
    return str(url.with_query({"startapp": start_param.get_start_param()}))
