from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.callback_data.admin import AdminMenuCallback


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(  # inline admin action
                    text="Посмотреть отчёт",
                    callback_data=AdminMenuCallback(action="report").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Импорт сотрудников",
                    callback_data=AdminMenuCallback(action="import").pack(),
                ),
            ],
        ],
    )
