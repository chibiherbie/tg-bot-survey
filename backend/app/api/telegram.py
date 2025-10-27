from typing import Annotated

from aiogram.types import Update
from asgi.dependence.security import TelegramWebhookSecretDependency
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Body, Response, status
from services.telegram import TelegramService

router = APIRouter(
    prefix="/telegram",
    tags=["telegram"],
    route_class=DishkaRoute,
)


@router.post("/webhook")
async def webhook(
    update: Annotated[Update, Body(...)],
    telegram_service: FromDishka[TelegramService],
    _: TelegramWebhookSecretDependency,
):
    await telegram_service.handle_webhook(update)
    return Response(status_code=status.HTTP_200_OK, content="OK")
