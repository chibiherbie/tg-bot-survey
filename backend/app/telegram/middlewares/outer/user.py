from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.middlewares.user_context import (
    EVENT_CONTEXT_KEY,
    EventContext,
)
from aiogram.types import TelegramObject
from di import container
from dishka import Scope
from services.telegram_auth import TelegramAuthService

USER_CONTEXT_KEY = "user"


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_context: EventContext = data[EVENT_CONTEXT_KEY]
        user = None
        if user_context.user is not None:
            async with container(scope=Scope.REQUEST) as request_container:
                user_service = await request_container.get(TelegramAuthService)
                user = await user_service.create_or_update_user_from_tg(
                    user_context.user,
                )
        if user is not None:
            data[USER_CONTEXT_KEY] = user
        return await handler(event, data)
