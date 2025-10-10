from dishka import FromDishka
from dto.mailings import MailingDTO
from interactors.base import BaseInteractor
from services.mailing import MailingService


class MailingsInteractor(BaseInteractor):
    def __init__(
        self,
        mailing_service: FromDishka[MailingService],
    ):
        self.mailing_service = mailing_service

    async def execute(self, dto: MailingDTO) -> None:
        await self.mailing_service.process_mailing(dto.mailing_id)
