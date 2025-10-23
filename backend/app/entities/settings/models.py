from __future__ import annotations

from shared.models.base import DBModel
from shared.models.mixins import CreatedAtMixin, UpdatedAtMixin
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AppSetting(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(200), unique=True)
    value: Mapped[dict] = mapped_column(JSONB)
    description: Mapped[str | None] = mapped_column(String(500))


__all__ = ["AppSetting"]
