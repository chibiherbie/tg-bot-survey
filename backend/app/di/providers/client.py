from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from dishka import Provider, Scope, provide
from telegram.config import telegram_settings


class ClientProvider(Provider):
    @provide(scope=Scope.APP)
    def bot_provider(self, session: AiohttpSession) -> Bot:
        return Bot(
            token=telegram_settings.TELEGRAM_BOT_TOKEN.get_secret_value(),
            session=session,
        )

    @provide(scope=Scope.APP)
    def dispatcher_provider(self) -> Dispatcher:
        return Dispatcher()


client_provider = ClientProvider(scope=Scope.REQUEST)
