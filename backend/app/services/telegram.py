from functools import lru_cache

from aiogram import Bot, Dispatcher
from aiogram.enums import (
    ChatMemberStatus,
    ParseMode,
)
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    ForceReply,
    InlineKeyboardMarkup,
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ResultChatMemberUnion,
    Update,
)
from core.logs import logger
from lxml import html
from lxml_html_clean import Cleaner
from services.base import BaseService
from telegram.config import telegram_settings

type InputMedia = (
    InputMediaAudio
    | InputMediaDocument
    | InputMediaPhoto
    | InputMediaVideo
    | InputMediaAnimation
)
type ReplyMarkup = (
    InlineKeyboardMarkup
    | ReplyKeyboardMarkup
    | ReplyKeyboardRemove
    | ForceReply
)


class TelegramService(BaseService):
    def __init__(self, bot: Bot, dp: Dispatcher):
        self.bot = bot
        self.dp = dp

    async def handle_webhook(self, update: Update) -> None:
        logger.info(f"Received event ({update.event_type}): {update.event}")
        await self.dp.feed_webhook_update(self.bot, update)

    async def check_user_subscription(
        self,
        user_id: int,
        chat_id: int,
    ) -> bool:
        result: ResultChatMemberUnion = await self.bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )
        return result.status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.CREATOR,
        ]

    @staticmethod
    @lru_cache
    def shrink_html(text: str, limit: int = 4096) -> str:
        if not text:
            return text

        suffix = ""
        if len(text) > limit:
            suffix = "..."

        broken_html = f"<root>{text[: limit - 3]}</root>"

        parser = html.HTMLParser(remove_blank_text=True, recover=True)
        tree = html.fromstring(broken_html, parser=parser)

        allowed_tags = {
            "b",
            "strong",
            "i",
            "em",
            "u",
            "ins",
            "s",
            "strike",
            "del",
            "tg-spoiler",
            "a",
            "tg-emoji",
            "code",
            "pre",
            "root",
        }

        cleaner = Cleaner(allow_tags=allowed_tags)
        cleaned_tree = cleaner.clean_html(tree)

        cleaned_html = html.tostring(
            cleaned_tree,
            with_tail=False,
            method="xml",
            encoding="unicode",
        )

        for tag in allowed_tags:
            cleaned_html = cleaned_html.replace(f"<{tag}/>", "")

        return (
            cleaned_html.replace("<root>", "").replace("</root>", "") + suffix
        )

    async def save_messages_to_service_chat(
        self,
        chat_id: int,
        message_ids: list[int],
    ) -> list[int]:
        messages = await self.bot.copy_messages(
            chat_id=telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
            from_chat_id=chat_id,
            message_ids=message_ids,
        )
        return [message.message_id for message in messages]

    async def forward_messages(
        self,
        chat_id: int,
        message_ids: list[int],
    ) -> None:
        await self.bot.forward_messages(
            chat_id=chat_id,
            from_chat_id=telegram_settings.TELEGRAM_SERVICE_CHAT_ID,
            message_ids=message_ids,
        )

    async def send_message(  # noqa: PLR0913
        self,
        *,
        message: Message | None = None,
        chat_id: int | None = None,
        text: str | None = None,
        media: InputMedia | None = None,
        reply_markup: ReplyMarkup | None = None,
        parse_mode: ParseMode = ParseMode.HTML,
    ) -> Message | None:
        chat_id, message_id = self._validate_params(
            message,
            chat_id,
            text,
            media,
        )
        if message_id:
            try:
                return await self._edit_message(
                    chat_id,
                    message_id,
                    text or "",
                    media,
                    reply_markup,
                    parse_mode,
                )
            except TelegramAPIError as e:
                if "message is not modified" in str(e):
                    return message
                if "message can't be edited" not in str(e):
                    logger.exception(f"Telegram API error: {e}", exc_info=e)
                    return None
        try:
            return await self._send_message(
                chat_id,
                text or "",
                media,
                reply_markup,
                parse_mode,
            )
        except TelegramAPIError as e:
            logger.exception(f"Telegram API error: {e}", exc_info=e)
            return None

    def _validate_params(
        self,
        message: Message | None,
        chat_id: int | None,
        text: str | None,
        media: InputMedia | None,
    ) -> tuple[int, int | None]:
        if (message is None) == (chat_id is None):
            raise ValueError("Only chat_id or message should be provided")  # noqa: TRY003
        if media is None and text is None:
            raise ValueError("text or media should be provided")  # noqa: TRY003
        if message:
            return message.chat.id, message.message_id
        if chat_id is None:
            raise ValueError("chat_id is required")  # noqa: TRY003
        return chat_id, None

    async def _edit_message(  # noqa: PLR0913
        self,
        chat_id: int,
        message_id: int,
        text: str,
        media: InputMedia | None,
        reply_markup: ReplyMarkup | None,
        parse_mode: ParseMode,
    ) -> Message:
        if not media:
            return await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=self.shrink_html(text, 4096),
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        media.caption = self.shrink_html(text, 1024) or None
        media.parse_mode = parse_mode
        return await self.bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=media,
            reply_markup=reply_markup,
        )

    async def _send_message(
        self,
        chat_id: int,
        text: str,
        media: InputMedia | None,
        reply_markup: ReplyMarkup | None,
        parse_mode: ParseMode,
    ) -> Message:
        if not media:
            return await self.bot.send_message(
                chat_id=chat_id,
                text=self.shrink_html(text, 4096),
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        kwargs = {
            "chat_id": chat_id,
            "caption": self.shrink_html(text, 1024) or None,
            "parse_mode": parse_mode,
            "reply_markup": reply_markup,
        }
        match media:
            case InputMediaPhoto():
                return await self.bot.send_photo(photo=media.media, **kwargs)
            case InputMediaVideo():
                return await self.bot.send_video(video=media.media, **kwargs)
            case InputMediaDocument():
                return await self.bot.send_document(
                    document=media.media,
                    **kwargs,
                )
            case InputMediaAudio():
                return await self.bot.send_audio(audio=media.media, **kwargs)
            case InputMediaAnimation():
                return await self.bot.send_animation(
                    animation=media.media,
                    **kwargs,
                )
            case _:
                raise NotImplementedError
