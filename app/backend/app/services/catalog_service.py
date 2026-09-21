# Ref: BL-O2-004 | Skill: K-017 | Fase: F6
"""Catalog / academic domain service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AcademicTerm,
    Career,
    Curriculum,
    CurriculumSubject,
    Student,
    Subject,
    Teacher,
    User,
)


class TermClosedError(PermissionError):
    """RF-TRM-002 — periodo CLOSED no admite cambios académicos normales."""

    def __init__(self) -> None:
        super().__init__("TERM_CLOSED")


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Careers ---
    def list_careers(self) -> Sequence[Career]:
        return self.db.scalars(select(Career).order_by(Career.code)).all()

    def create_career(
        self,
        *,
        code: str,
        name: str,
        modality: str = "PRESENCIAL",
        duration_semesters: int = 10,
    ) -> Career:
        if self.db.scalar(select(Career).where(Career.code == code)):
            raise ValueError("CAREER_EXISTS")
        career = Career(
            code=code,
            name=name,
            modality=modality,
            duration_semesters=duration_semesters,
            status="ACTIVE",
        )
        self.db.add(career)
        self.db.commit()
        self.db.refresh(career)
        return career

    # --- Subjects ---
    def list_subjects(self) -> Sequence[Subject]:
        return self.db.scalars(select(Subject).order_by(Subject.code)).all()

    def create_subject(
        self,
        *,
        code: str,
        name: str,
        credits: Decimal = Decimal("0"),
        hours: int = 0,
        description: str | None = None,
        type_: str = "OBLIGATORIA",
    ) -> Subject:
        if self.db.scalar(select(Subject).where(Subject.code == code)):
            raise ValueError("SUBJECT_EXISTS")
        subject = Subject(
            code=code,
            name=name,
            credits=credits,
            hours=hours,
            description=description,
            type=type_,
            status="ACTIVE",
        )
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)
        return subject

    # --- Curriculum ---
    def create_curriculum(self, *, career_id: int, version: str) -> Curriculum:
        career = self.db.get(Career, career_id)
        if career is None:
            raise LookupError("CAREER_NOT_FOUND")
        cur = Curriculum(career_id=career_id, version=version, status="ACTIVE")
        self.db.add(cur)
        self.db.commit()
        self.db.refresh(cur)
        return cur

    def add_curriculum_subject(
        self,
        *,
        curriculum_id: int,
        subject_id: int,
        level: int,
        semester: int,
        credits: Decimal,
    ) -> CurriculumSubject:
        cur = self.db.get(Curriculum, curriculum_id)
        sub = self.db.get(Subject, subject_id)
        if cur is None:
            raise LookupError("CURRICULUM_NOT_FOUND")
        if sub is None:
            raise LookupError("SUBJECT_NOT_FOUND")
        item = CurriculumSubject(
            curriculum_id=curriculum_id,
            subject_id=subject_id,
            level=level,
            semester=semester,
            credits=credits,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_curricula(self) -> Sequence[Curriculum]:
        stmt = select(Curriculum).options(selectinload(Curriculum.items)).order_by(
            Curriculum.id
        )
        return self.db.scalars(stmt).all()

    # --- Terms ---
    def list_terms(self) -> Sequence[AcademicTerm]:
        return self.db.scalars(select(AcademicTerm).order_by(AcademicTerm.id)).all()

    def create_term(
        self,
        *,
        code: str,
        name: str,
        start_date: date,
        end_date: date,
        status: str = "PLANNED",
        is_current: bool = False,
    ) -> AcademicTerm:
        if self.db.scalar(select(AcademicTerm).where(AcademicTerm.code == code)):
            raise ValueError("TERM_EXISTS")
        if status not in {"PLANNED", "ACTIVE", "CLOSED", "CANCELLED"}:
            raise ValueError("INVALID_TERM_STATUS")
        if is_current:
            for t in self.list_terms():
                t.is_current = False
        term = AcademicTerm(
            code=code,
            name=name,
            start_date=start_date,
            end_date=end_date,
            status=status,
            is_current=is_current,
        )
        self.db.add(term)
        self.db.commit()
        self.db.refresh(term)
        return term

    def set_term_status(self, term_id: int, status: str) -> AcademicTerm:
        term = self.db.get(AcademicTerm, term_id)
        if term is None:
            raise LookupError("TERM_NOT_FOUND")
        if status not in {"PLANNED", "ACTIVE", "CLOSED", "CANCELLED"}:
            raise ValueError("INVALID_TERM_STATUS")
        term.status = status
        if status == "ACTIVE":
            for t in self.list_terms():
                if t.id != term.id:
                    t.is_current = False
            term.is_current = True
        self.db.commit()
        self.db.refresh(term)
        return term

    def assert_term_writable(self, term_id: int) -> AcademicTerm:
        term = self.db.get(AcademicTerm, term_id)
        if term is None:
            raise LookupError("TERM_NOT_FOUND")
        if term.is_closed:
            raise TermClosedError()
        return term

    # --- Students / Teachers ---
    def list_students(self) -> Sequence[Student]:
        stmt = (
            select(Student)
            .where(Student.deleted_at.is_(None))
            .order_by(Student.id)
        )
        return self.db.scalars(stmt).all()

    def create_student(
        self,
        *,
        user_id: int,
        student_code: str,
        career_id: Optional[int] = None,
        level: Optional[str] = None,
        admission_date: Optional[date] = None,
    ) -> Student:
        if self.db.get(User, user_id) is None:
            raise LookupError("USER_NOT_FOUND")
        if self.db.scalar(select(Student).where(Student.user_id == user_id)):
            raise ValueError("STUDENT_PROFILE_EXISTS")
        if self.db.scalar(select(Student).where(Student.student_code == student_code)):
            raise ValueError("STUDENT_CODE_EXISTS")
        if career_id is not None and self.db.get(Career, career_id) is None:
            raise LookupError("CAREER_NOT_FOUND")
        student = Student(
            user_id=user_id,
            student_code=student_code,
            career_id=career_id,
            level=level,
            admission_date=admission_date,
            status="ACTIVE",
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def list_teachers(self) -> Sequence[Teacher]:
        return self.db.scalars(
            select(Teacher).where(Teacher.deleted_at.is_(None)).order_by(Teacher.id)
        ).all()

    def create_teacher(
        self,
        *,
        user_id: int,
        teacher_code: str,
        specialty: Optional[str] = None,
    ) -> Teacher:
        if self.db.get(User, user_id) is None:
            raise LookupError("USER_NOT_FOUND")
        if self.db.scalar(select(Teacher).where(Teacher.user_id == user_id)):
            raise ValueError("TEACHER_PROFILE_EXISTS")
        if self.db.scalar(select(Teacher).where(Teacher.teacher_code == teacher_code)):
            raise ValueError("TEACHER_CODE_EXISTS")
        teacher = Teacher(
            user_id=user_id,
            teacher_code=teacher_code,
            specialty=specialty,
            status="ACTIVE",
        )
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher
