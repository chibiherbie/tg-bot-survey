from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import Message, TelegramObject


class ChatTypeFilter(BaseFilter):
    def __init__(self, *chat_type: ChatType):
        self.chat_type = set(chat_type)

    async def __call__(self, event: TelegramObject) -> bool:
        return isinstance(event, Message) and event.chat.type in self.chat_type


class ChatIdFilter(BaseFilter):
    def __init__(self, *chat_id: int):
        self.chat_id = set(chat_id)

    async def __call__(self, event: TelegramObject) -> bool:
        return isinstance(event, Message) and event.chat.id in self.chat_id
