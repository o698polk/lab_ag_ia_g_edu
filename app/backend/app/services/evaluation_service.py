# Ref: BL-O4-* | Skill: K-017/K-016 | Fase: F6
"""Grading & attendance service with ABAC teaching_assignment."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AttendanceRecord,
    AttendanceSession,
    Course,
    Enrollment,
    Evaluation,
    EvaluationType,
    Grade,
    KardexEntry,
    Student,
    Teacher,
    User,
)
from app.services.catalog_service import CatalogService, TermClosedError
from app.services.operations_service import OperationsService
from app.services.role_service import AuthorizationError


class EvaluationService:
    VALID_ATTENDANCE = {"PRESENT", "ABSENT", "LATE", "JUSTIFIED"}
    VALID_KARDEX = {"APPROVED", "FAILED", "IN_PROGRESS", "WITHDRAWN"}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.ops = OperationsService(db)
        self.catalog = CatalogService(db)

    def _course(self, course_id: int) -> Course:
        course = self.db.get(Course, course_id)
        if course is None:
            raise LookupError("COURSE_NOT_FOUND")
        return course

    def _require_teacher_assignment(self, teacher: Teacher, course: Course) -> None:
        self.catalog.assert_term_writable(course.term_id)
        if not self.ops.teaching_assignment_exists(
            teacher_id=teacher.id, course_id=course.id, term_id=course.term_id
        ):
            raise AuthorizationError("CONTEXT_MISMATCH")

    def teacher_for_user(self, user_id: int) -> Teacher:
        teacher = self.ops.get_teacher_by_user_id(user_id)
        if teacher is None:
            raise AuthorizationError("TEACHER_PROFILE_REQUIRED")
        return teacher

    def student_for_user(self, user_id: int) -> Student:
        student = self.db.scalar(
            select(Student).where(
                Student.user_id == user_id, Student.deleted_at.is_(None)
            )
        )
        if student is None:
            raise LookupError("STUDENT_PROFILE_NOT_FOUND")
        return student

    # --- Evaluation types / evaluations ---
    def ensure_default_types(self) -> None:
        defaults = [
            ("PARTIAL", "Parcial"),
            ("PRACTICE", "Práctica"),
            ("PROJECT", "Proyecto"),
            ("EXAM", "Examen"),
            ("FINAL", "Final"),
        ]
        for code, name in defaults:
            if not self.db.scalar(select(EvaluationType).where(EvaluationType.code == code)):
                self.db.add(EvaluationType(code=code, name=name))
        self.db.commit()

    def create_evaluation(
        self,
        *,
        teacher: Optional[Teacher] = None,
        course_id: int,
        name: str,
        weight_percent: Decimal,
        evaluation_type_code: Optional[str] = None,
        due_date: Optional[date] = None,
        as_admin: bool = False,
    ) -> Evaluation:
        course = self._course(course_id)
        if as_admin:
            self.catalog.assert_term_writable(course.term_id)
        else:
            if teacher is None:
                raise AuthorizationError("TEACHER_PROFILE_REQUIRED")
            self._require_teacher_assignment(teacher, course)
        if weight_percent <= 0:
            raise ValueError("INVALID_WEIGHT")
        current = self.db.scalar(
            select(func.coalesce(func.sum(Evaluation.weight_percent), 0)).where(
                Evaluation.course_id == course_id,
                Evaluation.status == "ACTIVE",
            )
        ) or Decimal("0")
        if Decimal(str(current)) + weight_percent > Decimal("100"):
            raise ValueError("WEIGHT_SUM_EXCEEDS_100")

        type_id = None
        if evaluation_type_code:
            et = self.db.scalar(
                select(EvaluationType).where(EvaluationType.code == evaluation_type_code)
            )
            if et is None:
                raise LookupError("EVALUATION_TYPE_NOT_FOUND")
            type_id = et.id

        ev = Evaluation(
            course_id=course_id,
            evaluation_type_id=type_id,
            name=name,
            weight_percent=weight_percent,
            due_date=due_date,
            status="ACTIVE",
        )
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)
        return ev

    def list_evaluations(self, course_id: int) -> Sequence[Evaluation]:
        return self.db.scalars(
            select(Evaluation)
            .where(Evaluation.course_id == course_id)
            .order_by(Evaluation.id)
        ).all()

    # --- Grades ---
    def upsert_grade(
        self,
        *,
        teacher: Optional[Teacher] = None,
        evaluation_id: int,
        student_id: int,
        score: Decimal,
        comment: Optional[str] = None,
        as_admin: bool = False,
    ) -> Grade:
        ev = self.db.get(Evaluation, evaluation_id)
        if ev is None:
            raise LookupError("EVALUATION_NOT_FOUND")
        course = self._course(ev.course_id)
        if as_admin:
            self.catalog.assert_term_writable(course.term_id)
        else:
            if teacher is None:
                raise AuthorizationError("TEACHER_PROFILE_REQUIRED")
            self._require_teacher_assignment(teacher, course)

        enrolled = self.db.scalar(
            select(Enrollment).where(
                Enrollment.course_id == course.id,
                Enrollment.student_id == student_id,
                Enrollment.status == "ACTIVE",
            )
        )
        if enrolled is None:
            raise ValueError("STUDENT_NOT_ENROLLED")
        if score < 0 or score > 100:
            raise ValueError("INVALID_SCORE")

        grade = self.db.scalar(
            select(Grade).where(
                Grade.evaluation_id == evaluation_id,
                Grade.student_id == student_id,
            )
        )
        if grade is None:
            grade = Grade(
                evaluation_id=evaluation_id,
                student_id=student_id,
                score=score,
                comment=comment,
                graded_by_teacher_id=teacher.id if teacher else None,
                graded_at=datetime.now(timezone.utc),
            )
            self.db.add(grade)
        else:
            grade.score = score
            grade.comment = comment
            grade.graded_by_teacher_id = teacher.id if teacher else None
            grade.graded_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(grade)
        return grade

    def list_grades_for_course(self, course_id: int) -> Sequence[Grade]:
        stmt = (
            select(Grade)
            .join(Evaluation)
            .where(Evaluation.course_id == course_id)
            .options(selectinload(Grade.evaluation))
            .order_by(Grade.id)
        )
        return self.db.scalars(stmt).all()

    def list_grades_for_student(self, student_id: int) -> Sequence[Grade]:
        return self.db.scalars(
            select(Grade)
            .where(Grade.student_id == student_id)
            .options(selectinload(Grade.evaluation))
            .order_by(Grade.id)
        ).all()

    def gradebook(self, course_id: int, evaluation_id: Optional[int] = None) -> dict:
        self._course(course_id)
        grades = {}
        if evaluation_id:
            for g in self.db.scalars(
                select(Grade).where(Grade.evaluation_id == evaluation_id)
            ).all():
                grades[g.student_id] = g
        students = []
        for row in self.ops.course_roster(course_id):
            g = grades.get(row["student_id"])
            students.append(
                {
                    "student_id": row["student_id"],
                    "student_code": row["student_code"],
                    "name": row["name"],
                    "attendance_pct": self.attendance_percentage(
                        course_id=course_id, student_id=row["student_id"]
                    ),
                    "score": g.score if g else None,
                    "grade_id": g.id if g else None,
                }
            )
        return {
            "course_id": course_id,
            "evaluation_id": evaluation_id,
            "students": students,
        }

    # --- Attendance ---
    def _student_label(self, student_id: int) -> tuple[str, str]:
        student = self.db.get(Student, student_id)
        if student is None:
            return "", f"Estudiante {student_id}"
        user = self.db.get(User, student.user_id)
        return student.student_code, (user.full_name if user else student.student_code)

    def _hours_available(self, course: Course) -> list[int]:
        n = (course.hours_theory or 0) + (course.hours_practical or 0)
        if n < 1:
            n = 1
        return list(range(1, n + 1))

    def _authorize_course_write(
        self, *, teacher: Optional[Teacher], course: Course, as_admin: bool
    ) -> None:
        if as_admin:
            self.catalog.assert_term_writable(course.term_id)
            return
        if teacher is None:
            raise AuthorizationError("TEACHER_PROFILE_REQUIRED")
        self._require_teacher_assignment(teacher, course)

    def create_attendance_session(
        self,
        *,
        teacher: Optional[Teacher] = None,
        course_id: int,
        session_date: date,
        topic: Optional[str] = None,
        hour_slot: int = 1,
        as_admin: bool = False,
    ) -> AttendanceSession:
        course = self._course(course_id)
        self._authorize_course_write(teacher=teacher, course=course, as_admin=as_admin)
        existing = self.db.scalar(
            select(AttendanceSession).where(
                AttendanceSession.course_id == course_id,
                AttendanceSession.session_date == session_date,
                AttendanceSession.hour_slot == hour_slot,
            )
        )
        if existing:
            if topic:
                existing.topic = topic
                self.db.commit()
                self.db.refresh(existing)
            return existing
        session = AttendanceSession(
            course_id=course_id,
            session_date=session_date,
            hour_slot=hour_slot,
            topic=topic,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def attendance_roster(
        self, *, course_id: int, session_date: date, hour_slot: int = 1
    ) -> dict:
        course = self._course(course_id)
        session = self.db.scalar(
            select(AttendanceSession).where(
                AttendanceSession.course_id == course_id,
                AttendanceSession.session_date == session_date,
                AttendanceSession.hour_slot == hour_slot,
            )
        )
        records = {}
        if session:
            for rec in self.db.scalars(
                select(AttendanceRecord).where(AttendanceRecord.session_id == session.id)
            ).all():
                records[rec.student_id] = rec
        students = []
        for row in self.ops.course_roster(course_id):
            rec = records.get(row["student_id"])
            status = rec.status if rec else None
            students.append(
                {
                    "student_id": row["student_id"],
                    "student_code": row["student_code"],
                    "name": row["name"],
                    "status": status,
                    "notes": rec.notes if rec else None,
                    "present": status in {"PRESENT", "LATE", "JUSTIFIED"} if status else False,
                }
            )
        return {
            "course_id": course_id,
            "session_id": session.id if session else None,
            "session_date": session_date,
            "hour_slot": hour_slot,
            "hours_available": self._hours_available(course),
            "students": students,
        }

    def save_attendance_bulk(
        self,
        *,
        teacher: Optional[Teacher] = None,
        course_id: int,
        session_date: date,
        hour_slot: int,
        records: list[dict],
        as_admin: bool = False,
    ) -> dict:
        session = self.create_attendance_session(
            teacher=teacher,
            course_id=course_id,
            session_date=session_date,
            hour_slot=hour_slot,
            as_admin=as_admin,
        )
        saved = []
        for item in records:
            saved.append(
                self.mark_attendance(
                    teacher=teacher,
                    session_id=session.id,
                    student_id=item["student_id"],
                    status=item.get("status") or "PRESENT",
                    notes=item.get("notes"),
                    as_admin=as_admin,
                )
            )
        return self.attendance_roster(
            course_id=course_id, session_date=session_date, hour_slot=hour_slot
        )

    def mark_attendance(
        self,
        *,
        teacher: Optional[Teacher] = None,
        session_id: int,
        student_id: int,
        status: str,
        notes: Optional[str] = None,
        as_admin: bool = False,
    ) -> AttendanceRecord:
        session = self.db.get(AttendanceSession, session_id)
        if session is None:
            raise LookupError("ATTENDANCE_SESSION_NOT_FOUND")
        course = self._course(session.course_id)
        self._authorize_course_write(teacher=teacher, course=course, as_admin=as_admin)
        if status not in self.VALID_ATTENDANCE:
            raise ValueError("INVALID_ATTENDANCE_STATUS")
        enrolled = self.db.scalar(
            select(Enrollment).where(
                Enrollment.course_id == course.id,
                Enrollment.student_id == student_id,
                Enrollment.status == "ACTIVE",
            )
        )
        if enrolled is None:
            raise ValueError("STUDENT_NOT_ENROLLED")

        rec = self.db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.student_id == student_id,
            )
        )
        if rec is None:
            rec = AttendanceRecord(
                session_id=session_id,
                student_id=student_id,
                status=status,
                notes=notes,
            )
            self.db.add(rec)
        else:
            rec.status = status
            rec.notes = notes
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def attendance_percentage(self, *, course_id: int, student_id: int) -> float:
        sessions = self.db.scalars(
            select(AttendanceSession).where(AttendanceSession.course_id == course_id)
        ).all()
        if not sessions:
            return 0.0
        session_ids = [s.id for s in sessions]
        presentish = self.db.scalar(
            select(func.count()).select_from(AttendanceRecord).where(
                AttendanceRecord.session_id.in_(session_ids),
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.status.in_(["PRESENT", "LATE", "JUSTIFIED"]),
            )
        ) or 0
        return round((presentish / len(sessions)) * 100.0, 2)

    # --- Kardex ---
    def upsert_kardex(
        self,
        *,
        student_id: int,
        term_id: int,
        subject_id: int,
        course_id: Optional[int],
        final_grade: Optional[Decimal],
        academic_status: str,
        credits: Decimal,
    ) -> KardexEntry:
        if academic_status not in self.VALID_KARDEX:
            raise ValueError("INVALID_KARDEX_STATUS")
        self.catalog.assert_term_writable(term_id)
        entry = self.db.scalar(
            select(KardexEntry).where(
                KardexEntry.student_id == student_id,
                KardexEntry.term_id == term_id,
                KardexEntry.subject_id == subject_id,
            )
        )
        if entry is None:
            entry = KardexEntry(
                student_id=student_id,
                term_id=term_id,
                subject_id=subject_id,
                course_id=course_id,
                final_grade=final_grade,
                academic_status=academic_status,
                credits=credits,
            )
            self.db.add(entry)
        else:
            entry.course_id = course_id
            entry.final_grade = final_grade
            entry.academic_status = academic_status
            entry.credits = credits
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_kardex(self, student_id: int) -> Sequence[KardexEntry]:
        return self.db.scalars(
            select(KardexEntry)
            .where(KardexEntry.student_id == student_id)
            .order_by(KardexEntry.id)
        ).all()
