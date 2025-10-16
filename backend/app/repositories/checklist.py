from collections.abc import Sequence

from entities.checklist.enums import ChecklistSessionStatus
from entities.checklist.models import (
    Checklist,
    ChecklistAnswer,
    ChecklistQuestion,
    ChecklistSession,
    Employee,
    Position,
)
from repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class PositionRepository(BaseRepository[Position]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Position, session)


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Employee, session)

    async def get_by_tab_number(self, tab_number: str) -> Employee | None:
        stmt = (
            select(Employee)
            .where(Employee.tab_number == tab_number)
            .options(selectinload(Employee.position))
        )
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()


class ChecklistRepository(BaseRepository[Checklist]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Checklist, session)

    async def get_active_for_position(
        self,
        position_id: int,
    ) -> Checklist | None:
        stmt = (
            select(Checklist)
            .where(
                Checklist.position_id == position_id,
                Checklist.is_active.is_(True),
            )
            .order_by(Checklist.created_at.desc())
            .options(selectinload(Checklist.questions))
            .limit(1)
        )
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()


class ChecklistQuestionRepository(BaseRepository[ChecklistQuestion]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ChecklistQuestion, session)

    async def list_for_checklist(
        self,
        checklist_id: int,
    ) -> Sequence[ChecklistQuestion]:
        stmt = (
            select(ChecklistQuestion)
            .where(ChecklistQuestion.checklist_id == checklist_id)
            .order_by(ChecklistQuestion.order)
        )
        scalar = await self.session.scalars(stmt)
        return scalar.all()


class ChecklistSessionRepository(BaseRepository[ChecklistSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ChecklistSession, session)

    async def get_in_progress_for_user(
        self,
        user_id: int,
    ) -> ChecklistSession | None:
        stmt = (
            select(ChecklistSession)
            .where(
                ChecklistSession.user_id == user_id,
                ChecklistSession.status == ChecklistSessionStatus.IN_PROGRESS,
            )
            .options(selectinload(ChecklistSession.answers))
        )
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()

    async def get_with_answers(
        self,
        session_id: int,
    ) -> ChecklistSession | None:
        stmt = select(ChecklistSession).where(ChecklistSession.id == session_id).options(
            selectinload(ChecklistSession.answers).selectinload(
                ChecklistAnswer.question,
            ),
            selectinload(ChecklistSession.checklist).selectinload(
                Checklist.questions,
            ),
        )
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()


class ChecklistAnswerRepository(BaseRepository[ChecklistAnswer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ChecklistAnswer, session)

    async def get_for_session_question(
        self,
        session_id: int,
        question_id: int,
    ) -> ChecklistAnswer | None:
        stmt = (
            select(ChecklistAnswer)
            .where(
                ChecklistAnswer.session_id == session_id,
                ChecklistAnswer.question_id == question_id,
            )
        )
        scalar = await self.session.scalars(stmt)
        return scalar.one_or_none()

    async def list_question_ids_for_session(self, session_id: int) -> set[int]:
        stmt = select(ChecklistAnswer.question_id).where(
            ChecklistAnswer.session_id == session_id,
        )
        scalar = await self.session.scalars(stmt)
        return set(scalar.all())
