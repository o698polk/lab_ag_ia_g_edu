"""Zero Trust / AI schema

Revision ID: 0006_zero_trust
Revises: 0005_platform
Create Date: 2026-09-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_zero_trust"
down_revision: Union[str, None] = "0005_platform"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(64), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("module", sa.String(64), nullable=False),
        sa.Column("resource", sa.String(64), nullable=True),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tool_registry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("parameters_schema", sa.Text(), nullable=True),
        sa.Column("required_permissions", sa.Text(), nullable=True),
        sa.Column("allowed_roles", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tool_name"),
    )
    op.create_table(
        "tool_invocations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=True),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("parameters", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("policy_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tool_id"], ["tool_registry.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["ai_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tool_invocations")
    op.drop_table("tool_registry")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
    op.drop_table("security_events")
    op.drop_table("audit_events")
