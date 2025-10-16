from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka
from entities.user.models import User
from services.telegram import TelegramService
from shared.enums.group import Group
from telegram.middlewares.filters.chat import ChatTypeFilter
from telegram.middlewares.filters.permissions import GroupFilter

router = Router()


@router.message(
    Command("start"),
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def start_command(
    _: Message,
    user: User,
    telegram_service: FromDishka[TelegramService],
):
    await telegram_service.send_message(
        chat_id=user.id,
        text="Привет!",
    )
