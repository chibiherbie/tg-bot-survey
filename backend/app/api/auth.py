from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Body
from services.telegram_auth import TelegramAuthService

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)


@router.post("/telegram/login/web-app")
async def telegram_login_via_web_app(
    telegram_auth_service: FromDishka[TelegramAuthService],
    init_data_raw: Annotated[str, Body(...)],
) -> str:
    return await telegram_auth_service.login_user(init_data_raw)
