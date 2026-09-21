# Ref: BL-O4-* | Skill: K-014/K-017 | Fase: F6
# Ref: A02 ERD | RF-ATT/EVL/GRD/KAR
"""Evaluation domain: attendance, evaluations, grades, kardex."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    session_date: Mapped[date] = mapped_column(Date)
    topic: Mapped[Optional[str]] = mapped_column(String(255))

    records: Mapped[List["AttendanceRecord"]] = relationship(back_populates="session")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_record"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("attendance_sessions.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    status: Mapped[str] = mapped_column(String(32))  # PRESENT|ABSENT|LATE|JUSTIFIED
    notes: Mapped[Optional[str]] = mapped_column(String(255))

    session: Mapped[AttendanceSession] = relationship(back_populates="records")


class EvaluationType(Base):
    __tablename__ = "evaluation_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    evaluation_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("evaluation_types.id")
    )
    name: Mapped[str] = mapped_column(String(128))
    weight_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")

    grades: Mapped[List["Grade"]] = relationship(back_populates="evaluation")


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "student_id", name="uq_grade_eval_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    comment: Mapped[Optional[str]] = mapped_column(Text)
    graded_by_teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id"))
    graded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    evaluation: Mapped[Evaluation] = relationship(back_populates="grades")


class KardexEntry(Base):
    __tablename__ = "kardex_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("academic_terms.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    final_grade: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    academic_status: Mapped[str] = mapped_column(
        String(32), default="IN_PROGRESS"
    )  # APPROVED|FAILED|IN_PROGRESS|WITHDRAWN
    credits: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
