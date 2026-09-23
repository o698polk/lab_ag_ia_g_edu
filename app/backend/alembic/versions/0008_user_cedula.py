"""Required unique user cedula

Revision ID: 0008_user_cedula
Revises: 0007_functional_std
Create Date: 2026-09-22
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_user_cedula"
down_revision: Union[str, None] = "0007_functional_std"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("cedula", sa.String(16), nullable=True))
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id FROM users")).fetchall()
    for (user_id,) in rows:
        bind.execute(
            sa.text("UPDATE users SET cedula = :cedula WHERE id = :id"),
            {"cedula": f"{int(user_id):010d}", "id": user_id},
        )
    op.alter_column(
        "users",
        "cedula",
        existing_type=sa.String(16),
        nullable=False,
    )
    op.create_index("ix_users_cedula", "users", ["cedula"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_cedula", table_name="users")
    op.drop_column("users", "cedula")
