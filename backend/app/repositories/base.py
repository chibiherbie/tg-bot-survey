from collections.abc import Sequence
from typing import Any, TypeVar

from shared.models.base import DBModel
from sqlalchemy import ClauseElement, exists, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.dialects.postgresql import insert


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

    async def upsert(
        self,
        insert_values: dict[str, Any],
        update_values: dict[str, Any],
        conflict_target: list[str],
        where_condition: dict[str, Any] | None = None,
    ) -> T | None:
        """Добавляет новый report или обновляет существующий, используя upsert."""
        # Если передано условие where, добавляем его к запросу
        where = None
        if where_condition:
            where = and_(
                *[getattr(self.model, key) == value for key, value in where_condition.items()],
            )
        stmt = (
            insert(self.model)
            .values(**insert_values)
            .on_conflict_do_update(
                index_elements=conflict_target,
                set_=update_values,
                where=where,
            )
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        row = res.one()  # гарантируем, что есть одна строка
        obj_id = row.id
        created = bool(row.created)

        # 5) получаем ORM-объект и коммитим
        obj = await self.session.get(self.model, obj_id)
        await self.session.commit()

        return obj, created
        return result.scalar_one_or_none()

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
