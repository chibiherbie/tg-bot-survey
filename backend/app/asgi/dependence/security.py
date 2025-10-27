from typing import Annotated

from core.security.globals import (
    HEADER_TOKEN_KEY,
    TELEGRAM_WEBHOOK_SECRET_HEADER,
)
from core.security.token import get_token
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from entities.user.models import User
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from services.user import UserService
from shared.enums.group import Group
from shared.schemas.token import TokenSchema
from starlette import status
from telegram.config import telegram_settings

HeaderTokenSec = Annotated[
    str,
    Security(APIKeyHeader(name=HEADER_TOKEN_KEY, auto_error=False)),
]

TelegramWebhookSecretSec = Annotated[
    str,
    Security(
        APIKeyHeader(name=TELEGRAM_WEBHOOK_SECRET_HEADER, auto_error=False),
    ),
]


class TelegramWebhookApiSecretDepends:
    def __call__(self, secret_token: TelegramWebhookSecretSec) -> str:
        if not secret_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        expected_token = (
            telegram_settings.TELEGRAM_SECRET_TOKEN.get_secret_value()
        )
        if secret_token != expected_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return secret_token


class TokenDepends:
    def __init__(self, group: Group):
        self.group = group

    def __call__(self, jwt_token: HeaderTokenSec) -> TokenSchema:
        schema = get_token(jwt_token)
        match self.group:
            case Group.ADMIN:
                if not all([schema.user_id, Group.ADMIN in schema.groups]):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                    )
                return schema
            case Group.USER:
                if not all([schema.user_id, Group.USER in schema.groups]):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                    )
                return schema
            case _:
                raise NotImplementedError


TokenDependency = Annotated[TokenSchema, Depends(TokenDepends(Group.USER))]


@inject
async def get_current_user(
    token: TokenDependency,
    user_service: FromDishka[UserService],
) -> User:
    if Group.USER not in token.groups:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if not token.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if not (
        user := await user_service.get_user_or_none(user_id=token.user_id)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


CurrentUserDependency = Annotated[User, Depends(get_current_user)]

TelegramWebhookSecretDependency = Annotated[
    str,
    Depends(TelegramWebhookApiSecretDepends()),
]
