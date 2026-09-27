"""Per-user least-privilege lab guard.

Revision ID: 0014_user_policy_guard
Revises: 0013_eval_runs
Create Date: 2026-09-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_user_policy_guard"
down_revision: Union[str, None] = "0013_eval_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("policies_enforced", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("users", "policies_enforced")
