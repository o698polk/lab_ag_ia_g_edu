"""Lab toggle for least-privilege AI gateway enforcement.

Revision ID: 0011_lab_policy_guard
Revises: 0010_ai_provider_settings
Create Date: 2026-09-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_lab_policy_guard"
down_revision: Union[str, None] = "0010_ai_provider_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_provider_settings",
        sa.Column("policies_enforced", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("ai_provider_settings", "policies_enforced")
