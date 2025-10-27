from typing import Optional

from entities.user.enums.statuses import UserRegistrationStatus
from shared.config import shared_settings
from shared.models.base import DBModel
from shared.models.mixins import CreatedAtMixin, UpdatedAtMixin
from sqlalchemy import BigInteger, ForeignKey, String, sql
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "users"

    # Telegram native fields
    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    tg_username: Mapped[str | None] = mapped_column(String(200))
    tg_first_name: Mapped[str] = mapped_column(String(200))
    tg_last_name: Mapped[str | None] = mapped_column(String(200))
    tg_bio: Mapped[str | None] = mapped_column(String(500))
    tg_birthdate: Mapped[str | None] = mapped_column(String(50))

    utm: Mapped[str | None] = mapped_column(String(50))

    is_banned: Mapped[bool] = mapped_column(default=False)
    admin_flag: Mapped[bool] = mapped_column(default=False)

    registration_status: Mapped[UserRegistrationStatus] = mapped_column(
        default=UserRegistrationStatus.UNKNOWN,
        server_default=sql.text(repr(UserRegistrationStatus.UNKNOWN.value)),
    )

    referrals: Mapped[list["User"]] = relationship(back_populates="referrer")
    referrer: Mapped[Optional["User"]] = relationship(
        back_populates="referrals",
        remote_side="User.id",
    )

    referrer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    @property
    def is_admin(self) -> bool:
        return self.admin_flag or self.id in shared_settings.SUPER_ADMIN_IDS
