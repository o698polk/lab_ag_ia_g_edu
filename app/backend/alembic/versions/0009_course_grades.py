"""Two partials, recovery grade and computed course status.

Revision ID: 0009_course_grades
Revises: 0008_user_cedula
Create Date: 2026-09-23
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_course_grades"
down_revision: Union[str, None] = "0008_user_cedula"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kardex_entries", sa.Column("first_partial", sa.Numeric(5, 2), nullable=True))
    op.add_column("kardex_entries", sa.Column("second_partial", sa.Numeric(5, 2), nullable=True))
    op.add_column("kardex_entries", sa.Column("recovery_grade", sa.Numeric(5, 2), nullable=True))
    op.alter_column(
        "kardex_entries",
        "academic_status",
        existing_type=sa.String(32),
        type_=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "kardex_entries",
        "academic_status",
        existing_type=sa.String(64),
        type_=sa.String(32),
        existing_nullable=False,
    )
    op.drop_column("kardex_entries", "recovery_grade")
    op.drop_column("kardex_entries", "second_partial")
    op.drop_column("kardex_entries", "first_partial")
