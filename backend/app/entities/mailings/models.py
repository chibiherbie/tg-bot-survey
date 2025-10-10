from datetime import datetime

from entities.mailings.enums.statuses import MailingStatus
from shared.models.base import DBModel
from shared.models.mixins import CreatedAtMixin, UpdatedAtMixin
from sqlalchemy import (
    ARRAY,
    BigInteger,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    sql,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Mailing(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "mailings"

    message_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger()))
    status: Mapped[MailingStatus] = mapped_column(
        default=MailingStatus.CREATED,
        server_default=sql.text(repr(MailingStatus.CREATED.value)),
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recipients: Mapped[list["MailingRecipient"]] = relationship(
        back_populates="mailing",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MailingRecipient(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "mailing_recipients"
    __table_args__ = (
        UniqueConstraint(
            "mailing_id",
            "recipient_id",
            name="uq_mailing_recipient",
        ),
    )

    mailing_id: Mapped[int] = mapped_column(
        ForeignKey("mailings.id", ondelete="CASCADE"),
    )
    recipient_id: Mapped[int] = mapped_column(BigInteger())

    status: Mapped[MailingStatus] = mapped_column(
        default=MailingStatus.CREATED,
        server_default=sql.text(repr(MailingStatus.CREATED.value)),
    )
    mailing: Mapped["Mailing"] = relationship(back_populates="recipients")
