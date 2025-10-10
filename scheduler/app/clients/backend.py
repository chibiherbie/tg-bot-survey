from clients.base import BaseInnerClient
from core.config import core_settings
from core.logs import logger
from yarl import URL

from shared.enums.request import RequestMethod


class ProcessingClient(BaseInnerClient):
    client_id = core_settings.PROCESSING_CLIENT_ID
    base_url = (
        core_settings.processing_api_url.with_host(core_settings.BACKEND_HOST)
        .with_port(core_settings.BACKEND_PORT)
        .with_scheme("http")
    )

    @property
    def mailing_url(self) -> URL:
        return self.base_url / "mailings"

    @property
    def health_check_url(self) -> URL:
        return self.base_url / "health"

    async def health_check(self):
        logger.info("Start health check")
        await self.request(
            url=self.health_check_url,
            method=RequestMethod.POST,
        )
        logger.info("Health check completed")

    async def process_mailings(self):
        logger.info("Start process mailings")
        await self.request(
            url=self.mailing_url,
            method=RequestMethod.POST,
        )
        logger.info("Process mailings completed")
