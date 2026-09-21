"""Academic catalog schema

Revision ID: 0002_academic
Revises: 0001_iam
Create Date: 2026-09-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_academic"
down_revision: Union[str, None] = "0001_iam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "careers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("modality", sa.String(64), nullable=False),
        sa.Column("duration_semesters", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("credits", sa.Numeric(5, 2), nullable=False),
        sa.Column("hours", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "subject_prerequisites",
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("prerequisite_subject_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["prerequisite_subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("subject_id", "prerequisite_subject_id"),
        sa.UniqueConstraint("subject_id", "prerequisite_subject_id", name="uq_subject_prereq"),
    )
    op.create_table(
        "curriculum",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("career_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["career_id"], ["careers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "curriculum_subjects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("curriculum_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("credits", sa.Numeric(5, 2), nullable=False),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curriculum.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("curriculum_id", "subject_id", name="uq_curriculum_subject"),
    )
    op.create_table(
        "academic_terms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("student_code", sa.String(32), nullable=False),
        sa.Column("career_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(32), nullable=True),
        sa.Column("admission_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["career_id"], ["careers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("student_code"),
    )
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("teacher_code", sa.String(32), nullable=False),
        sa.Column("specialty", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("teacher_code"),
    )


def downgrade() -> None:
    op.drop_table("teachers")
    op.drop_table("students")
    op.drop_table("academic_terms")
    op.drop_table("curriculum_subjects")
    op.drop_table("curriculum")
    op.drop_table("subject_prerequisites")
    op.drop_table("subjects")
    op.drop_table("careers")
