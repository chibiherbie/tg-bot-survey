from entities.settings.models import AppSetting
from repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AppSettingRepository(BaseRepository[AppSetting]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AppSetting, session)

    async def get_by_key(self, key: str) -> AppSetting | None:
        stmt = select(AppSetting).where(AppSetting.key == key)
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()
