"""Encrypted DeepSeek API key for the internal assistant.

Revision ID: 0010_ai_provider_settings
Revises: 0009_course_grades
Create Date: 2026-09-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_ai_provider_settings"
down_revision: Union[str, None] = "0009_course_grades"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_provider_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("key_hint", sa.String(16), nullable=True),
        sa.Column("model", sa.String(64), nullable=False, server_default="deepseek-chat"),
        sa.Column("base_url", sa.String(255), nullable=False, server_default="https://api.deepseek.com"),
        sa.Column("status", sa.String(32), nullable=False, server_default="EMPTY"),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", name="uq_ai_provider"),
    )
    op.create_index("ix_ai_provider_settings_provider", "ai_provider_settings", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_ai_provider_settings_provider", table_name="ai_provider_settings")
    op.drop_table("ai_provider_settings")
