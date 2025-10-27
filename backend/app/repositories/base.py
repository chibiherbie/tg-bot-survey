from collections.abc import Sequence
from typing import Any, TypeVar

from shared.models.base import DBModel
from sqlalchemy import ClauseElement, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

T = TypeVar("T", bound=DBModel)


class BaseRepository[T]:
    def __init__(self, model: type[T], session: AsyncSession) -> None:
        self.session = session
        self.model = model

    async def get(
        self,
        target_id: int,
        options: Sequence[ExecutableOption] | None = None,
    ) -> T | None:
        options = options or []
        stmt = (
            select(self.model)
            .options(*options)
            .where(self.model.id == target_id)
        )
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()

    async def list(
        self,
        *clause: ClauseElement[bool],
        options: Sequence[ExecutableOption] | None = None,
    ) -> Sequence[T]:
        options = options or []
        stmt = select(self.model).where(*clause).options(*options)
        scalar = await self.session.scalars(stmt)
        return scalar.all()

    async def exists(self, target_id: int) -> bool:
        stmt = select(exists().where(self.model.id == target_id))
        scalar = await self.session.scalars(stmt)
        return scalar.one()

    async def create(self, obj_in: dict[str, Any]) -> T:
        obj = self.model(**obj_in)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T, obj_in: dict[str, Any]) -> T:
        for key, value in obj_in.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def put(self, target_id: int, obj_in: dict[str, Any]) -> T:
        if not (obj := await self.get(target_id)):
            return await self.create(obj_in)
        return await self.update(obj, obj_in)

    async def delete(self, target_id: int) -> None:
        obj = await self.get(target_id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
        return obj

    async def refresh(self, obj: T) -> T:
        await self.session.refresh(obj)
        return obj
