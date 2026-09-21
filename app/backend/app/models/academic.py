# Ref: BL-O2-001/002/003 | Skill: K-014/K-017 | Fase: F6
# Ref: A02 ERD | RF-STU/TCH/CAR/CUR/SUB/TRM
"""Academic catalog ORM models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    modality: Mapped[str] = mapped_column(String(64), default="PRESENCIAL")
    duration_semesters: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    students: Mapped[List["Student"]] = relationship(back_populates="career")
    curricula: Mapped[List["Curriculum"]] = relationship(back_populates="career")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    credits: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    hours: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String(64), default="OBLIGATORIA")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")


class SubjectPrerequisite(Base):
    __tablename__ = "subject_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "subject_id", "prerequisite_subject_id", name="uq_subject_prereq"
        ),
    )

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), primary_key=True)
    prerequisite_subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"), primary_key=True
    )


class Curriculum(Base):
    __tablename__ = "curriculum"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    career_id: Mapped[int] = mapped_column(ForeignKey("careers.id"), index=True)
    version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")

    career: Mapped[Career] = relationship(back_populates="curricula")
    items: Mapped[List["CurriculumSubject"]] = relationship(back_populates="curriculum")


class CurriculumSubject(Base):
    __tablename__ = "curriculum_subjects"
    __table_args__ = (
        UniqueConstraint(
            "curriculum_id", "subject_id", name="uq_curriculum_subject"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    curriculum_id: Mapped[int] = mapped_column(ForeignKey("curriculum.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    semester: Mapped[int] = mapped_column(Integer, default=1)
    credits: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    curriculum: Mapped[Curriculum] = relationship(back_populates="items")
    subject: Mapped[Subject] = relationship()


class AcademicTerm(Base):
    """Periodo académico — CLOSED bloquea cambios normales (RF-TRM-002)."""

    __tablename__ = "academic_terms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="PLANNED", index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def is_closed(self) -> bool:
        return self.status == "CLOSED"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    student_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    career_id: Mapped[Optional[int]] = mapped_column(ForeignKey("careers.id"))
    level: Mapped[Optional[str]] = mapped_column(String(32))
    admission_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    career: Mapped[Optional[Career]] = relationship(back_populates="students")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    teacher_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    specialty: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
