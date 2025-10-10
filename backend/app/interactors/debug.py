from core.logs import logger
from dishka import FromDishka
from dto.debug import DebugDTO
from interactors.base import BaseInteractor
from services.telegram import TelegramService
from services.user import UserService


class DebugInteractor(BaseInteractor):
    def __init__(
        self,
        user_service: FromDishka[UserService],
        telegram_service: FromDishka[TelegramService],
    ):
        self.user_service = user_service
        self.telegram_service = telegram_service

    async def execute(self, dto: DebugDTO) -> None:
        logger.info(f"DebugDTO: {dto}")
        for user_put_schema in dto.users:
            user, _ = await self.user_service.put_user(user_put_schema)
            logger.info(f"User updated: {user.id}")
            await self.telegram_service.send_message(
                chat_id=user.id,
                text=dto.message,
            )
