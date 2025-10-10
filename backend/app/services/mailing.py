import asyncio
from datetime import UTC, datetime

from asyncio_redis_rate_limit import RateLimiter, RateSpec
from core.logs import logger
from dto.mailings import MailingDTO
from entities.mailings.enums.statuses import MailingStatus
from entities.mailings.models import MailingRecipient
from redis.asyncio import Redis
from repositories.mailings import MailingRepository
from services.base import BaseService
from services.telegram import TelegramService
from shared.config import mailing_settings
from shared.schemas.bot import BotInfoSchema
from shared.utils.process_runner import ProcessRunner


class MailingService(BaseService):
    def __init__(
        self,
        mailing_repository: MailingRepository,
        telegram_service: TelegramService,
        process_runner: ProcessRunner,
        bot_info: BotInfoSchema,
        redis: Redis,
    ):
        self.mailing_repository = mailing_repository
        self.telegram_service = telegram_service
        self.process_runner = process_runner
        self.redis = redis
        self.bot_info = bot_info

    async def process_mailings(self) -> None:
        from interactors.mailings import (  # noqa: PLC0415
            MailingsInteractor,
        )

        logger.info("Acquiring pending mailings...")
        mailing_ids = await self.mailing_repository.acquire_pending_mailings(
            datetime.now(UTC),
        )
        if not mailing_ids:
            logger.info("No mailings to process.")
            return

        logger.info(f"Acquired {len(mailing_ids)} mailings: {mailing_ids}")

        for mailing_id in mailing_ids:
            try:
                self.process_runner.queue_interactor(
                    MailingsInteractor,
                    MailingDTO(mailing_id=mailing_id),
                )
                logger.info(f"Queued mailing #{mailing_id} for processing.")
            except Exception as e:  # noqa: BLE001
                logger.exception(
                    f"Failed to queue mailing #{mailing_id}. "
                    f"Reverting status to {MailingStatus.CREATED!r}.",
                    exc_info=e,
                )
                await self.mailing_repository.set_status(
                    mailing_id,
                    MailingStatus.CREATED,
                )

    async def process_mailing(self, mailing_id: int) -> None:
        if await self._validate_mailing(mailing_id) is False:
            logger.warning(f"Mailing #{mailing_id} validating failed.")
            await self.mailing_repository.finish_sending(
                mailing_id,
                success=False,
            )
            logger.info(f"Finished mailing: #{mailing_id}")
            return
        try:
            await self.mailing_repository.start_sending(mailing_id)
            mailing = await self.mailing_repository.get(mailing_id)
            async for recipients in self._yield_recipients(mailing_id):
                current_status = await self.mailing_repository.get_status(
                    mailing_id,
                )
                if current_status != MailingStatus.SENDING:
                    await self.mailing_repository.update_end_time(mailing_id)
                    return
                success_ids, failed_ids = await self._send_batch(
                    mailing.message_ids,
                    recipients,
                )
                if success_ids:
                    await self.mailing_repository.update_recipient_statuses(
                        success_ids,
                        MailingStatus.SENT,
                    )
                if failed_ids:
                    await self.mailing_repository.update_recipient_statuses(
                        failed_ids,
                        MailingStatus.FAILED,
                    )
        except Exception as e:  # noqa: BLE001
            logger.exception(e, exc_info=e)
            await self.mailing_repository.finish_sending(
                mailing_id,
                success=False,
            )
            return
        await self.mailing_repository.finish_sending(mailing_id, success=True)

    async def _validate_mailing(self, mailing_id: int) -> bool:
        mailing = await self.mailing_repository.get(mailing_id)
        return (
            mailing
            and mailing.status == MailingStatus.PENDING
            and mailing.message_ids
        )

    async def _yield_recipients(self, mailing_id: int, batch_size: int = 20):
        offset = 0
        while True:
            recipients = await self.mailing_repository.get_ready_recipients(
                mailing_id,
                limit=batch_size,
                offset=offset,
            )
            if not recipients:
                break
            yield recipients
            offset += len(recipients)

    async def _send_batch(
        self,
        message_ids: list[int],
        recipients: list[MailingRecipient],
    ) -> tuple[list[int], list[int]]:
        tasks = [self._send_message(message_ids, rec) for rec in recipients]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_ids: list[int] = []
        failed_ids: list[int] = []

        for recipient, result in zip(recipients, results, strict=False):
            if isinstance(result, Exception):
                failed_ids.append(recipient.id)
            else:
                success_ids.append(recipient.id)

        return success_ids, failed_ids

    async def _send_message(
        self,
        message_ids: list[int],
        recipient: MailingRecipient,
    ) -> None:
        async with RateLimiter(
            unique_key=str(self.bot_info.id),
            rate_spec=RateSpec(
                requests=mailing_settings.THROTTLER_RATE_LIMIT,
                seconds=1,
            ),
            backend=self.redis,
            cache_prefix="mailing:send:",
        ):
            await self.telegram_service.forward_messages(
                recipient.recipient_id,
                message_ids,
            )
