from datetime import UTC, datetime

from entities.mailings.enums.statuses import MailingStatus
from entities.mailings.models import Mailing, MailingRecipient
from repositories.base import BaseRepository
from sqlalchemy import ClauseElement, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class MailingRepository(BaseRepository[Mailing]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Mailing, session)

    def status_clauses(
        self,
        *include_statuses: MailingStatus,
        exclude_statuses: list[MailingStatus] | None = None,
    ) -> list[ClauseElement]:
        status_clauses = []
        if include_statuses:
            status_clauses.append(Mailing.status.in_(include_statuses))
        if exclude_statuses:
            status_clauses.append(Mailing.status.not_in(exclude_statuses))
        return status_clauses

    async def acquire_pending_mailings(
        self,
        timestamp: datetime,
        limit: int = 100,
    ) -> list[int]:
        select_stmt = (
            select(Mailing.id)
            .where(
                *self.status_clauses(
                    MailingStatus.CREATED,
                    MailingStatus.PENDING,
                    MailingStatus.RESUME,
                ),
                Mailing.scheduled_at <= timestamp,
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        locked_mailing_ids = (await self.session.scalars(select_stmt)).all()

        if not locked_mailing_ids:
            return []

        update_stmt = (
            update(Mailing)
            .where(Mailing.id.in_(locked_mailing_ids))
            .values(status=MailingStatus.PENDING)
            .returning(Mailing.id)
        )
        updated_ids = (await self.session.scalars(update_stmt)).all()
        await self.session.commit()
        return updated_ids

    async def update_statuses_batch(
        self,
        mailing_ids: list[int],
        status: MailingStatus,
    ) -> None:
        stmt = (
            update(Mailing)
            .where(Mailing.id.in_(mailing_ids))
            .values(status=status)
        )
        await self.session.execute(stmt)

    async def set_status(self, mailing_id: int, status: MailingStatus) -> None:
        await self.update_statuses_batch([mailing_id], status)
        await self.session.commit()

    async def update_recipient_statuses(
        self,
        recipient_ids: list[int],
        status: MailingStatus,
    ) -> None:
        stmt = (
            update(MailingRecipient)
            .where(MailingRecipient.id.in_(recipient_ids))
            .values(status=status)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_ready_recipients(
        self,
        mailing_id: int,
        limit: int,
        offset: int,
    ) -> list[MailingRecipient]:
        stmt = (
            select(MailingRecipient)
            .where(
                MailingRecipient.mailing_id == mailing_id,
                MailingRecipient.status.in_(
                    [MailingStatus.CREATED, MailingStatus.FAILED],
                ),
            )
            .limit(limit)
            .offset(offset)
        )
        scalar = await self.session.scalars(stmt)
        return scalar.all()

    async def start_sending(self, mailing_id: int) -> None:
        stmt = (
            update(Mailing)
            .where(Mailing.id == mailing_id)
            .values(
                status=MailingStatus.SENDING,
                started_at=datetime.now(UTC),
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def finish_sending(self, mailing_id: int, success: bool) -> None:
        status = MailingStatus.SENT if success else MailingStatus.FAILED
        stmt = (
            update(Mailing)
            .where(Mailing.id == mailing_id)
            .values(
                status=status,
                ended_at=datetime.now(UTC),
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_status(self, mailing_id: int):
        stmt = select(Mailing.status).where(Mailing.id == mailing_id)
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()

    async def update_end_time(self, mailing_id: int) -> None:
        stmt = (
            update(Mailing)
            .where(Mailing.id == mailing_id)
            .values(ended_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.commit()
