from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka import FromDishka
from entities.user.models import User
from services.telegram import TelegramService
from shared.enums.group import Group
from telegram.keyboards.checklist import remove_keyboard
from telegram.middlewares.filters.chat import ChatTypeFilter
from telegram.middlewares.filters.permissions import GroupFilter
from telegram.states.checklist import ChecklistStates

router = Router()


@router.message(
    Command("start"),
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def start_command(
    message: Message,
    state: FSMContext,
    user: User,
    telegram_service: FromDishka[TelegramService],
):
    await state.clear()
    await state.set_state(ChecklistStates.waiting_tab_number)
    await telegram_service.send_message(
        chat_id=user.id,
        text=(
            "Привет! Давай начнем чеклист. "
            "Пожалуйста, отправь свой табельный номер."
        ),
        reply_markup=remove_keyboard(),
    )
