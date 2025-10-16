from datetime import datetime

from entities.checklist.enums import (
    ChecklistAnswerValue,
    ChecklistSessionStatus,
)
from shared.schemas.base import FormModel


class ChecklistSessionCreateSchema(FormModel):
    user_id: int
    employee_id: int
    checklist_id: int


class ChecklistSessionUpdateSchema(FormModel):
    status: ChecklistSessionStatus | None = None
    completed_at: datetime | None = None


class ChecklistAnswerCreateSchema(FormModel):
    session_id: int
    question_id: int
    answer: ChecklistAnswerValue
    photo_file_id: str | None = None
    photo_unique_id: str | None = None
