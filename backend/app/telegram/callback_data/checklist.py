from aiogram.filters.callback_data import CallbackData


class PositionConfirmCallback(CallbackData, prefix="pos"):
    action: str


class FeedbackCallback(CallbackData, prefix="fb"):
    action: str
