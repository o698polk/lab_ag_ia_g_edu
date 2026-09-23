"""Functional standardization fields

Revision ID: 0007_functional_std
Revises: 0006_zero_trust
Create Date: 2026-09-22
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_functional_std"
down_revision: Union[str, None] = "0006_zero_trust"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(80), server_default=""))
    op.add_column("users", sa.Column("last_name", sa.String(80), server_default=""))
    op.add_column("users", sa.Column("phone", sa.String(32), server_default=""))
    op.add_column("roles", sa.Column("description", sa.String(255), server_default=""))
    op.add_column("permissions", sa.Column("is_active", sa.Boolean(), server_default=sa.true()))
    op.add_column("courses", sa.Column("hours_theory", sa.Integer(), server_default="0"))
    op.add_column("courses", sa.Column("hours_practical", sa.Integer(), server_default="0"))
    op.add_column("courses", sa.Column("hours_autonomous", sa.Integer(), server_default="0"))
    op.add_column("attendance_sessions", sa.Column("hour_slot", sa.Integer(), server_default="1"))


def downgrade() -> None:
    op.drop_column("attendance_sessions", "hour_slot")
    op.drop_column("courses", "hours_autonomous")
    op.drop_column("courses", "hours_practical")
    op.drop_column("courses", "hours_theory")
    op.drop_column("permissions", "is_active")
    op.drop_column("roles", "description")
    op.drop_column("users", "phone")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
