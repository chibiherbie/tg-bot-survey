from datetime import UTC, date, datetime

from core.logs import logger
from entities.checklist.enums import (
    ChecklistAnswerValue,
    ChecklistSessionStatus,
)
from entities.checklist.models import (
    Checklist,
    ChecklistAnswer,
    ChecklistQuestion,
    ChecklistSession,
    Employee,
)
from entities.checklist.schemas.forms import (
    ChecklistAnswerCreateSchema,
    ChecklistSessionCreateSchema,
    ChecklistSessionUpdateSchema,
)
from repositories.checklist import (
    ChecklistAnswerRepository,
    ChecklistQuestionRepository,
    ChecklistRepository,
    ChecklistSessionRepository,
    EmployeeRepository,
)
from services.base import BaseService


class ChecklistFlowService(BaseService):
    def __init__(
        self,
        employee_repository: EmployeeRepository,
        checklist_repository: ChecklistRepository,
        question_repository: ChecklistQuestionRepository,
        session_repository: ChecklistSessionRepository,
        answer_repository: ChecklistAnswerRepository,
    ) -> None:
        self.employee_repository = employee_repository
        self.checklist_repository = checklist_repository
        self.question_repository = question_repository
        self.session_repository = session_repository
        self.answer_repository = answer_repository

    async def get_employee_by_tab_number(
        self,
        tab_number: str,
    ) -> Employee | None:
        return await self.employee_repository.get_by_tab_number(tab_number)

    async def get_active_checklist_for_employee(
        self,
        employee: Employee,
    ) -> Checklist | None:
        position = employee.position
        if position is not None and position.groups:
            for group in position.groups:
                checklist = (
                    await self.checklist_repository.get_active_for_group(
                        group.id,
                    )
                )
                if checklist:
                    logger.info(
                        "Checklist selected by group",
                        employee_id=employee.id,
                        group_id=group.id,
                        checklist_id=checklist.id,
                    )
                    return checklist
        checklist = await self.checklist_repository.get_default()
        if checklist:
            logger.info(
                "Default checklist selected",
                employee_id=employee.id,
                checklist_id=checklist.id,
            )
        else:
            logger.warning(
                "No checklist available",
                employee_id=employee.id,
                position_id=employee.position_id,
            )
        return checklist

    async def start_or_get_session(
        self,
        *,
        user_id: int,
        employee: Employee,
        checklist: Checklist,
    ) -> tuple[ChecklistSession, bool]:
        if existing := await self.session_repository.get_in_progress_for_user(
            user_id,
        ):
            logger.info(
                "Checklist session resumed",
                user_id=user_id,
                session_id=existing.id,
            )
            return existing, False
        employee_id = employee.id
        checklist_id = checklist.id
        create_schema = ChecklistSessionCreateSchema(
            user_id=user_id,
            employee_id=employee_id,
            checklist_id=checklist_id,
        )
        session = await self.session_repository.create(
            create_schema.model_dump(exclude_unset=True),
        )
        logger.info(
            "Checklist session created",
            user_id=user_id,
            session_id=session.id,
            employee_id=employee_id,
            checklist_id=checklist_id,
        )
        return session, True

    async def load_session(self, session_id: int) -> ChecklistSession | None:
        return await self.session_repository.get_with_answers(session_id)

    async def list_questions(
        self,
        checklist_id: int,
    ) -> list[ChecklistQuestion]:
        return list(
            await self.question_repository.list_for_checklist(checklist_id),
        )

    async def get_completed_session_for_employee_on_date(
        self,
        *,
        employee_id: int,
        target_date: date,
    ) -> ChecklistSession | None:
        return (
            await self.session_repository.get_completed_for_employee_on_date(
                employee_id,
                target_date,
            )
        )

    async def save_answer(
        self,
        *,
        session: ChecklistSession,
        question: ChecklistQuestion,
        answer: ChecklistAnswerValue,
        photo_file_id: str | None = None,
        photo_unique_id: str | None = None,
    ) -> ChecklistAnswer:
        create_schema = ChecklistAnswerCreateSchema(
            session_id=session.id,
            question_id=question.id,
            answer=answer,
            photo_file_id=photo_file_id,
            photo_unique_id=photo_unique_id,
        )
        if existing := await self.answer_repository.get_for_session_question(
            session.id,
            question.id,
        ):
            payload = create_schema.model_dump(
                exclude={"session_id", "question_id"},
                exclude_unset=True,
            )
            saved = await self.answer_repository.update(existing, payload)
            logger.info(
                "Checklist answer updated",
                session_id=session.id,
                question_id=question.id,
                answer=answer.value,
                has_photo=bool(saved.photo_file_id),
            )
            return saved

        saved = await self.answer_repository.create(
            create_schema.model_dump(exclude_unset=True),
        )
        logger.info(
            "Checklist answer saved",
            session_id=session.id,
            question_id=question.id,
            answer=answer.value,
            has_photo=bool(saved.photo_file_id),
        )
        return saved

    async def complete_session(
        self,
        session: ChecklistSession,
    ) -> ChecklistSession:
        update_schema = ChecklistSessionUpdateSchema(
            status=ChecklistSessionStatus.COMPLETED,
            completed_at=datetime.now(UTC),
        )
        updated = await self.session_repository.update(
            session,
            update_schema.model_dump(exclude_unset=True),
        )
        logger.info(
            "Checklist session completed",
            session_id=session.id,
        )
        return updated

    async def save_feedback(
        self,
        *,
        session: ChecklistSession,
        feedback_text: str | None = None,
        feedback_voice_file_id: str | None = None,
        feedback_voice_unique_id: str | None = None,
    ) -> ChecklistSession:
        payload = {
            "feedback_text": feedback_text,
            "feedback_voice_file_id": feedback_voice_file_id,
            "feedback_voice_unique_id": feedback_voice_unique_id,
            "feedback_submitted_at": datetime.now(UTC),
        }
        session = await self.session_repository.update(session, payload)
        logger.info(
            "Checklist feedback saved",
            session_id=session.id,
            has_text=bool(feedback_text),
            has_voice=bool(feedback_voice_file_id),
        )
        return session

    async def get_next_unanswered_question(
        self,
        session_id: int,
        questions: list[ChecklistQuestion],
    ) -> ChecklistQuestion | None:
        answered_ids = (
            await self.answer_repository.list_question_ids_for_session(
                session_id,
            )
        )
        for question in questions:
            if question.id not in answered_ids:
                return question
        return None
