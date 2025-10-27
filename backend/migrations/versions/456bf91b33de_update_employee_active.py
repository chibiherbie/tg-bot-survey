"""drop employee full_name add is_active

Revision ID: 456bf91b33de
Revises: 9c249c26a9a4
Create Date: 2025-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "456bf91b33de"
down_revision: Union[str, None] = "9c249c26a9a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.alter_column("employees", "is_active", server_default=None)
    op.drop_column("employees", "full_name")


def downgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("full_name", sa.String(length=255), nullable=True),
    )
    op.drop_column("employees", "is_active")
