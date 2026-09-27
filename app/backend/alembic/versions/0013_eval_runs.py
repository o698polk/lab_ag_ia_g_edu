"""Experimental evaluation run tables.

Revision ID: 0013_eval_runs
Revises: 0012_impersonator_refresh
Create Date: 2026-09-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_eval_runs"
down_revision: Union[str, None] = "0012_impersonator_refresh"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("scenario", sa.String(8), nullable=False),
        sa.Column("policies_enforced", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("policy_version", sa.String(16), nullable=False, server_default="v1"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("case_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_eval_runs_run_id", "eval_runs", ["run_id"], unique=True)
    op.create_index("ix_eval_runs_user_id", "eval_runs", ["user_id"])
    op.create_table(
        "eval_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_pk", sa.Integer(), sa.ForeignKey("eval_runs.id"), nullable=False),
        sa.Column("case_id", sa.String(16), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("category", sa.String(8), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_tool", sa.String(64), nullable=False),
        sa.Column("expected_a", sa.String(8), nullable=False),
        sa.Column("expected_b", sa.String(8), nullable=False),
        sa.Column("observed_decision", sa.String(16), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("policy_id", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("match_expected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("technical_error", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reply", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_eval_results_run_pk", "eval_results", ["run_pk"])
    op.create_index("ix_eval_results_case_id", "eval_results", ["case_id"])


def downgrade() -> None:
    op.drop_table("eval_results")
    op.drop_table("eval_runs")
