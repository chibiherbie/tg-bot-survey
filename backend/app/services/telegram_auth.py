from datetime import UTC, datetime

from aiogram import Bot, types
from aiogram.utils.web_app import (
    WebAppInitData,
    WebAppUser,
    safe_parse_webapp_init_data,
)
from core.security.globals import WEBAPP_SESSION_EXPIRE_IN
from core.security.token import create_jwt_token
from entities.user.models import User
from entities.user.schemas.forms import UserPatchSchema, UserPutSchema
from fastapi import HTTPException
from services.base import BaseService
from services.user import UserService
from shared.enums.group import Group
from shared.schemas.token import TokenSchema
from starlette import status
from telegram.config import telegram_settings


class TelegramAuthService(BaseService):
    def __init__(self, user_service: UserService, bot: Bot):
        self.user_service = user_service
        self.bot = bot

    async def create_or_update_user_from_tg(
        self,
        tg_user: types.User | WebAppUser,
    ) -> User:
        user_full_info = await self.bot.get_chat(tg_user.id)
        user, created = await self.user_service.put_user(
            UserPutSchema(
                id=tg_user.id,
                tg_username=tg_user.username or None,
                tg_first_name=tg_user.first_name,
                tg_last_name=tg_user.last_name or None,
                tg_bio=user_full_info.bio or None,
                tg_birthdate=user_full_info.birthdate or None,
            ),
        )
        if not created:
            user = await self.patch_user_from_tg(user, tg_user)
        return user

    async def patch_user_from_tg(
        self,
        user: User,
        tg_user: types.User | WebAppUser,
    ) -> User:
        user_full_info = await self.bot.get_chat(tg_user.id)
        return await self.user_service.patch_user(
            user,
            UserPatchSchema(
                tg_username=tg_user.username or None,
                tg_first_name=tg_user.first_name,
                tg_last_name=tg_user.last_name or None,
                tg_bio=user_full_info.bio or None,
                tg_birthdate=user_full_info.birthdate or None,
            ),
        )

    async def login_user(self, init_data_raw: str) -> str:
        try:
            init_data: WebAppInitData = safe_parse_webapp_init_data(
                init_data=init_data_raw,
                token=telegram_settings.TELEGRAM_BOT_TOKEN.get_secret_value(),
            )
        except (ValueError, KeyError) as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST) from e
        if datetime.now(UTC) > init_data.auth_date + WEBAPP_SESSION_EXPIRE_IN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        if not init_data.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        user = await self.create_or_update_user_from_tg(init_data.user)
        groups = [Group.USER]
        if user.is_admin:
            groups.append(Group.ADMIN)
        return create_jwt_token(TokenSchema(user_id=user.id, groups=groups))
