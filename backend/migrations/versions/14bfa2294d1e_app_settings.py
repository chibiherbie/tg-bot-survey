"""app settings table

Revision ID: 14bfa2294d1e
Revises: 833cc99303a4
Create Date: 2025-08-18 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "14bfa2294d1e"
down_revision: Union[str, None] = "833cc99303a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_IMPORT_CONFIG = {
    "sheet_name": None,
    "columns": {
        "tab_number": "Табельный номер",
        "position": "Должность",
    },
}

DEFAULT_POSITION_CHANGE_CONFIG = {
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "use_tls": True,
    "from_email": "no-reply@example.com",
    "to_emails": ["hr@example.com"],
    "subject": "Запрос на смену должности",
}


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
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
        sa.UniqueConstraint("key", name="uq_app_settings_key"),
    )

    settings_table = sa.table(
        "app_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.JSON),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        settings_table,
        [
            {
                "key": "employee_import_config",
                "value": DEFAULT_IMPORT_CONFIG,
                "description": "Настройки импорта сотрудников из XLSX",
            },
            {
                "key": "position_change_notification",
                "value": DEFAULT_POSITION_CHANGE_CONFIG,
                "description": "Почтовые настройки для заявок на смену должности",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("app_settings")
