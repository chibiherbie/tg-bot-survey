from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from services.mailing import MailingService

router = APIRouter(
    prefix="/mailings",
    tags=["mailings"],
    route_class=DishkaRoute,
)


@router.post("")
async def process_mailings(mailing_service: FromDishka[MailingService]):
    await mailing_service.process_mailings()
