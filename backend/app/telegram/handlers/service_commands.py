from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka
from entities.user.models import User
from services.telegram import TelegramService
from services.user import UserService
from shared.enums.group import Group
from telegram.config import telegram_settings
from telegram.middlewares.filters.chat import ChatIdFilter, ChatTypeFilter
from telegram.middlewares.filters.permissions import GroupFilter

router = Router()


@router.message(
    Command("reset"),
    GroupFilter(Group.ADMIN),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def reset_command(
    _: Message,
    user: User,
    user_service: FromDishka[UserService],
    telegram_service: FromDishka[TelegramService],
):
    user = await user_service.reset_user(user)
    await telegram_service.send_message(chat_id=user.id, text="Вы сброшены!")


@router.message(
    Command("im_admin"),
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.GROUP, ChatType.SUPERGROUP),
    ChatIdFilter(
        telegram_settings.TELEGRAM_ADMIN_CHAT_ID,
        telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
    ),
)
async def im_admin_command(
    _: Message,
    user: User,
    user_service: FromDishka[UserService],
    telegram_service: FromDishka[TelegramService],
):
    user = await user_service.update_user_admin_flag(user, True)
    await telegram_service.send_message(
        chat_id=user.id,
        text="Теперь вы админ!",
    )
