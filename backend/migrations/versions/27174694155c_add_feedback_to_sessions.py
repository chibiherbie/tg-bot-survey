"""add feedback fields to checklist_sessions

Revision ID: 27174694155c
Revises: 14bfa2294d1e
Create Date: 2025-08-18 00:32:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "27174694155c"
down_revision: Union[str, None] = "14bfa2294d1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("checklist_sessions", sa.Column("feedback_text", sa.Text(), nullable=True))
    op.add_column(
        "checklist_sessions",
        sa.Column("feedback_voice_file_id", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "checklist_sessions",
        sa.Column("feedback_voice_unique_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "checklist_sessions",
        sa.Column("feedback_submitted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("checklist_sessions", "feedback_submitted_at")
    op.drop_column("checklist_sessions", "feedback_voice_unique_id")
    op.drop_column("checklist_sessions", "feedback_voice_file_id")
    op.drop_column("checklist_sessions", "feedback_text")
