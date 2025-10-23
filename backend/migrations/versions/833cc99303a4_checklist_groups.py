"""introduce checklist groups

Revision ID: 833cc99303a4
Revises: 456bf91b33de
Create Date: 2025-08-18 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "833cc99303a4"
down_revision: Union[str, None] = "456bf91b33de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checklist_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_checklist_groups_name"),
    )

    op.create_table(
        "position_checklist_groups",
        sa.Column("position_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["checklist_groups.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["position_id"],
            ["positions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("position_id", "group_id"),
    )

    op.add_column(
        "checklists",
        sa.Column(
            "group_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "checklists",
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.alter_column("checklists", "is_default", server_default=None)

    op.create_foreign_key(
        "fk_checklists_group_id",
        "checklists",
        "checklist_groups",
        ["group_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("checklists_position_id_fkey", "checklists", type_="foreignkey")
    op.drop_column("checklists", "position_id")


def downgrade() -> None:
    op.add_column(
        "checklists",
        sa.Column("position_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        "checklists_position_id_fkey",
        "checklists",
        "positions",
        ["position_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_checklists_group_id", "checklists", type_="foreignkey")
    op.drop_column("checklists", "is_default")
    op.drop_column("checklists", "group_id")

    op.drop_table("position_checklist_groups")
    op.drop_table("checklist_groups")
