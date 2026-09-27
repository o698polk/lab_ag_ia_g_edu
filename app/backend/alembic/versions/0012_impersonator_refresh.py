"""Store original admin on impersonation refresh tokens.

Revision ID: 0012_impersonator_refresh
Revises: 0011_lab_policy_guard
Create Date: 2026-09-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_impersonator_refresh"
down_revision: Union[str, None] = "0011_lab_policy_guard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column("impersonator_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_refresh_tokens_impersonator_id",
        "refresh_tokens",
        "users",
        ["impersonator_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_refresh_tokens_impersonator_id", "refresh_tokens", type_="foreignkey")
    op.drop_column("refresh_tokens", "impersonator_id")
