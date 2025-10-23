from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from telegram.callback_data.checklist import PositionConfirmCallback


def checklist_answer_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text="Да"),
            KeyboardButton(text="Нет"),
        ],
        [
            KeyboardButton(text="Нельзя выполнить"),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def position_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, всё верно",
                    callback_data=PositionConfirmCallback(action="confirm").pack(),
                ),
                InlineKeyboardButton(
                    text="Нет",
                    callback_data=PositionConfirmCallback(action="deny").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Отправить заявку на смену должности",
                    callback_data=PositionConfirmCallback(action="request_change").pack(),
                ),
            ],
        ],
    )
