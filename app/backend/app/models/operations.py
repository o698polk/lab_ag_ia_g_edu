# Ref: BL-O3-* | Skill: K-014/K-017 | Fase: F6
# Ref: A02 ERD operación | RF-CRS/ASN/ENR/SCH
"""Academic operations ORM: courses, assignments, enrollments, schedules."""

from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Course(Base):
    """Paralelo / curso ofertado en un periodo."""

    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("subject_id", "term_id", "parallel_code", name="uq_course_parallel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("academic_terms.id"), index=True)
    parallel_code: Mapped[str] = mapped_column(String(16), default="A")
    capacity: Mapped[int] = mapped_column(Integer, default=40)
    hours_theory: Mapped[int] = mapped_column(Integer, default=0)
    hours_practical: Mapped[int] = mapped_column(Integer, default=0)
    hours_autonomous: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    assignments: Mapped[List["TeachingAssignment"]] = relationship(back_populates="course")
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="course")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="course")


class TeachingAssignment(Base):
    """Base ABAC: teacher_id + course_id + term_id."""

    __tablename__ = "teaching_assignments"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id", "course_id", "term_id", name="uq_teaching_assignment"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("academic_terms.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")

    course: Mapped[Course] = relationship(back_populates="assignments")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "term_id", name="uq_enrollment_active_pair"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("academic_terms.id"), index=True)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # ACTIVE|CANCELLED|COMPLETED

    course: Mapped[Course] = relationship(back_populates="enrollments")


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    capacity: Mapped[int] = mapped_column(Integer, default=40)


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), index=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("academic_terms.id"), index=True)
    day_of_week: Mapped[str] = mapped_column(String(16))  # MON..SUN
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    course: Mapped[Course] = relationship(back_populates="schedules")
