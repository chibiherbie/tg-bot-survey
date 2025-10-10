from aiogram import Bot
from dishka import Provider, Scope, provide
from shared.schemas.bot import BotInfoSchema
from shared.utils.bg_runner import BgRunner
from shared.utils.process_runner import ProcessRunner


class ToolsProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_bot_info(self, bot: Bot) -> BotInfoSchema:
        bot_me = await bot.get_me()
        return BotInfoSchema(id=bot_me.id, username=bot_me.username)


tools_provider = ToolsProvider(scope=Scope.APP)
tools_provider.provide_all(
    BgRunner,
    ProcessRunner,
)
