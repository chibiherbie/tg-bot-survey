from datetime import datetime

from entities.checklist.enums import ChecklistAnswerValue, ChecklistSessionStatus
from shared.models.base import DBModel
from shared.models.mixins import CreatedAtMixin, UpdatedAtMixin
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    sql,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


position_group_table = Table(
    "position_checklist_groups",
    DBModel.metadata,
    Column("position_id", ForeignKey("positions.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", ForeignKey("checklist_groups.id", ondelete="CASCADE"), primary_key=True),
)


class Position(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "positions"

    name: Mapped[str] = mapped_column(String(255), unique=True)

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="position",
        cascade="all,delete",
    )
    groups: Mapped[list["ChecklistGroup"]] = relationship(
        back_populates="positions",
        secondary=position_group_table,
    )


class Employee(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "employees"

    tab_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)

    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="RESTRICT"),
    )
    position: Mapped[Position] = relationship(back_populates="employees")

    sessions: Mapped[list["ChecklistSession"]] = relationship(
        back_populates="employee",
        cascade="all,delete-orphan",
    )


class ChecklistGroup(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "checklist_groups"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text())

    positions: Mapped[list[Position]] = relationship(
        back_populates="groups",
        secondary=position_group_table,
    )
    checklists: Mapped[list["Checklist"]] = relationship(
        back_populates="group",
        cascade="all,delete-orphan",
    )


class Checklist(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "checklists"

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text())
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)

    is_default: Mapped[bool] = mapped_column(Boolean(), default=False)

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("checklist_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    group: Mapped[ChecklistGroup | None] = relationship(back_populates="checklists")

    questions: Mapped[list["ChecklistQuestion"]] = relationship(
        back_populates="checklist",
        cascade="all,delete-orphan",
        order_by="ChecklistQuestion.order",
    )

    sessions: Mapped[list["ChecklistSession"]] = relationship(back_populates="checklist")


class ChecklistQuestion(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "checklist_questions"
    __table_args__ = (
        UniqueConstraint(
            "checklist_id",
            "order",
            name="uq_checklist_questions_checklist_id_order",
        ),
    )

    text: Mapped[str] = mapped_column(Text())
    order: Mapped[int] = mapped_column(Integer())
    requires_photo: Mapped[bool] = mapped_column(Boolean(), default=False)

    checklist_id: Mapped[int] = mapped_column(
        ForeignKey("checklists.id", ondelete="CASCADE"),
    )
    checklist: Mapped[Checklist] = relationship(back_populates="questions")

    answers: Mapped[list["ChecklistAnswer"]] = relationship(
        back_populates="question",
        cascade="all,delete-orphan",
    )


class ChecklistSession(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "checklist_sessions"

    user_id: Mapped[int] = mapped_column(
        BigInteger(),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
    )
    checklist_id: Mapped[int] = mapped_column(
        ForeignKey("checklists.id", ondelete="CASCADE"),
    )
    status: Mapped[ChecklistSessionStatus] = mapped_column(
        SQLEnum(
            ChecklistSessionStatus,
            name="checklistsessionstatus",
        ),
        default=ChecklistSessionStatus.IN_PROGRESS,
        server_default=sql.text(
            repr(ChecklistSessionStatus.IN_PROGRESS.value),
        ),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )

    employee: Mapped[Employee] = relationship(back_populates="sessions")
    checklist: Mapped[Checklist] = relationship(back_populates="sessions")
    answers: Mapped[list["ChecklistAnswer"]] = relationship(
        back_populates="session",
        cascade="all,delete-orphan",
    )


class ChecklistAnswer(DBModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "checklist_answers"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "question_id",
            name="uq_checklist_answers_session_question",
        ),
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_sessions.id", ondelete="CASCADE"),
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_questions.id", ondelete="CASCADE"),
    )
    answer: Mapped[ChecklistAnswerValue] = mapped_column(
        SQLEnum(
            ChecklistAnswerValue,
            name="checklistanswervalue",
        ),
    )
    photo_file_id: Mapped[str | None] = mapped_column(String(512))
    photo_unique_id: Mapped[str | None] = mapped_column(String(255))

    session: Mapped[ChecklistSession] = relationship(back_populates="answers")
    question: Mapped[ChecklistQuestion] = relationship(back_populates="answers")
