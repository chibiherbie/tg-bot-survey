from aiogram.filters.callback_data import CallbackData


class AdminMenuCallback(CallbackData, prefix="adm"):
    action: str
