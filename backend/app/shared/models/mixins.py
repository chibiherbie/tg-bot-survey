from datetime import UTC, datetime

from shared.models.base import Base
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class CreatedAtMixin(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
    )


class UpdatedAtMixin(Base):
    __abstract__ = True

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
    )
