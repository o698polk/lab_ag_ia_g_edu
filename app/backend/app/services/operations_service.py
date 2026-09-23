# Ref: BL-O3-* | Skill: K-017/K-016 | Fase: F6
"""Operations service: courses, assignments, enrollments, schedules + ABAC helper."""

from __future__ import annotations

from datetime import time
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Classroom,
    Course,
    Enrollment,
    Schedule,
    Student,
    Subject,
    Teacher,
    TeachingAssignment,
    User,
)
from app.services.catalog_service import CatalogService, TermClosedError


class CapacityError(ValueError):
    def __init__(self) -> None:
        super().__init__("COURSE_CAPACITY_FULL")


class ScheduleConflictError(ValueError):
    def __init__(self, reason: str = "SCHEDULE_CONFLICT") -> None:
        super().__init__(reason)


class OperationsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.catalog = CatalogService(db)

    # --- ABAC ---
    def teaching_assignment_exists(
        self, *, teacher_id: int, course_id: int, term_id: int
    ) -> bool:
        row = self.db.scalar(
            select(TeachingAssignment).where(
                TeachingAssignment.teacher_id == teacher_id,
                TeachingAssignment.course_id == course_id,
                TeachingAssignment.term_id == term_id,
                TeachingAssignment.status == "ACTIVE",
            )
        )
        return row is not None

    def get_teacher_by_user_id(self, user_id: int) -> Optional[Teacher]:
        return self.db.scalar(
            select(Teacher).where(
                Teacher.user_id == user_id, Teacher.deleted_at.is_(None)
            )
        )

    # --- Courses ---
    def list_courses(self, term_id: Optional[int] = None) -> Sequence[Course]:
        stmt = select(Course).order_by(Course.id)
        if term_id is not None:
            stmt = stmt.where(Course.term_id == term_id)
        return self.db.scalars(stmt).all()

    def create_course(
        self,
        *,
        subject_id: int,
        term_id: int,
        parallel_code: str = "A",
        capacity: int = 40,
        hours_theory: int = 0,
        hours_practical: int = 0,
        hours_autonomous: int = 0,
    ) -> Course:
        self.catalog.assert_term_writable(term_id)
        if self.db.get(Subject, subject_id) is None:
            raise LookupError("SUBJECT_NOT_FOUND")
        existing = self.db.scalar(
            select(Course).where(
                Course.subject_id == subject_id,
                Course.term_id == term_id,
                Course.parallel_code == parallel_code,
            )
        )
        if existing:
            raise ValueError("COURSE_EXISTS")
        course = Course(
            subject_id=subject_id,
            term_id=term_id,
            parallel_code=parallel_code,
            capacity=capacity,
            hours_theory=hours_theory,
            hours_practical=hours_practical,
            hours_autonomous=hours_autonomous,
            status="ACTIVE",
        )
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def update_course(
        self,
        course_id: int,
        *,
        parallel_code: Optional[str] = None,
        capacity: Optional[int] = None,
        hours_theory: Optional[int] = None,
        hours_practical: Optional[int] = None,
        hours_autonomous: Optional[int] = None,
        status: Optional[str] = None,
        teacher_id: Optional[int] = None,
    ) -> Course:
        course = self.db.get(Course, course_id)
        if course is None:
            raise LookupError("COURSE_NOT_FOUND")
        if parallel_code is not None:
            course.parallel_code = parallel_code
        if capacity is not None:
            course.capacity = capacity
        if hours_theory is not None:
            course.hours_theory = hours_theory
        if hours_practical is not None:
            course.hours_practical = hours_practical
        if hours_autonomous is not None:
            course.hours_autonomous = hours_autonomous
        if status is not None:
            course.status = status
        if teacher_id is not None:
            existing = self.db.scalar(
                select(TeachingAssignment).where(
                    TeachingAssignment.course_id == course.id,
                    TeachingAssignment.teacher_id == teacher_id,
                    TeachingAssignment.term_id == course.term_id,
                )
            )
            if existing is None:
                self.db.add(
                    TeachingAssignment(
                        teacher_id=teacher_id,
                        course_id=course.id,
                        term_id=course.term_id,
                        status="ACTIVE",
                    )
                )
            else:
                existing.status = "ACTIVE"
        self.db.commit()
        self.db.refresh(course)
        return course

    def course_teacher_id(self, course_id: int) -> Optional[int]:
        row = self.db.scalar(
            select(TeachingAssignment).where(
                TeachingAssignment.course_id == course_id,
                TeachingAssignment.status == "ACTIVE",
            )
        )
        return row.teacher_id if row else None

    def course_roster(self, course_id: int) -> list[dict]:
        if self.db.get(Course, course_id) is None:
            raise LookupError("COURSE_NOT_FOUND")
        ens = self.db.scalars(
            select(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.status == "ACTIVE",
            )
        ).all()
        out = []
        for en in ens:
            student = self.db.get(Student, en.student_id)
            user = self.db.get(User, student.user_id) if student else None
            name = user.full_name if user else f"Estudiante {en.student_id}"
            out.append(
                {
                    "student_id": en.student_id,
                    "student_code": student.student_code if student else "",
                    "name": name,
                    "enrollment_id": en.id,
                    "status": en.status,
                }
            )
        return out

    def set_course_status(self, course_id: int, status: str) -> Course:
        course = self.db.get(Course, course_id)
        if course is None:
            raise LookupError("COURSE_NOT_FOUND")
        course.status = status
        self.db.commit()
        self.db.refresh(course)
        return course

    def set_assignment_status(self, assignment_id: int, status: str) -> TeachingAssignment:
        row = self.db.get(TeachingAssignment, assignment_id)
        if row is None:
            raise LookupError("ASSIGNMENT_NOT_FOUND")
        row.status = status
        self.db.commit()
        self.db.refresh(row)
        return row

    # --- Teaching assignments ---
    def list_assignments(self, course_id: Optional[int] = None) -> Sequence[TeachingAssignment]:
        stmt = select(TeachingAssignment).order_by(TeachingAssignment.id)
        if course_id is not None:
            stmt = stmt.where(TeachingAssignment.course_id == course_id)
        return self.db.scalars(stmt).all()

    def assign_teacher(
        self, *, teacher_id: int, course_id: int, term_id: int
    ) -> TeachingAssignment:
        self.catalog.assert_term_writable(term_id)
        teacher = self.db.get(Teacher, teacher_id)
        course = self.db.get(Course, course_id)
        if teacher is None or teacher.deleted_at is not None:
            raise LookupError("TEACHER_NOT_FOUND")
        if course is None:
            raise LookupError("COURSE_NOT_FOUND")
        if course.term_id != term_id:
            raise ValueError("TERM_COURSE_MISMATCH")
        if self.teaching_assignment_exists(
            teacher_id=teacher_id, course_id=course_id, term_id=term_id
        ):
            raise ValueError("ASSIGNMENT_EXISTS")
        row = TeachingAssignment(
            teacher_id=teacher_id,
            course_id=course_id,
            term_id=term_id,
            status="ACTIVE",
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    # --- Enrollments ---
    def list_enrollments(self, course_id: Optional[int] = None) -> Sequence[Enrollment]:
        stmt = select(Enrollment).order_by(Enrollment.id)
        if course_id is not None:
            stmt = stmt.where(Enrollment.course_id == course_id)
        return self.db.scalars(stmt).all()

    def enroll_student(
        self, *, student_id: int, course_id: int, term_id: int
    ) -> Enrollment:
        self.catalog.assert_term_writable(term_id)
        student = self.db.get(Student, student_id)
        course = self.db.get(Course, course_id)
        if student is None or student.deleted_at is not None:
            raise LookupError("STUDENT_NOT_FOUND")
        if course is None:
            raise LookupError("COURSE_NOT_FOUND")
        if course.term_id != term_id:
            raise ValueError("TERM_COURSE_MISMATCH")

        active_count = self.db.scalar(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.status == "ACTIVE",
            )
        ) or 0
        if active_count >= course.capacity:
            raise CapacityError()

        existing = self.db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
                Enrollment.term_id == term_id,
            )
        )
        if existing and existing.status == "ACTIVE":
            raise ValueError("ENROLLMENT_EXISTS")
        if existing:
            existing.status = "ACTIVE"
            self.db.commit()
            self.db.refresh(existing)
            return existing

        enr = Enrollment(
            student_id=student_id,
            course_id=course_id,
            term_id=term_id,
            status="ACTIVE",
        )
        self.db.add(enr)
        self.db.commit()
        self.db.refresh(enr)
        return enr

    def cancel_enrollment(self, enrollment_id: int) -> Enrollment:
        enr = self.db.get(Enrollment, enrollment_id)
        if enr is None:
            raise LookupError("ENROLLMENT_NOT_FOUND")
        self.catalog.assert_term_writable(enr.term_id)
        enr.status = "CANCELLED"
        self.db.commit()
        self.db.refresh(enr)
        return enr

    # --- Classrooms / Schedules ---
    def create_classroom(self, *, code: str, name: str, capacity: int = 40) -> Classroom:
        if self.db.scalar(select(Classroom).where(Classroom.code == code)):
            raise ValueError("CLASSROOM_EXISTS")
        room = Classroom(code=code, name=name, capacity=capacity)
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def list_classrooms(self) -> Sequence[Classroom]:
        return self.db.scalars(select(Classroom).order_by(Classroom.code)).all()

    @staticmethod
    def _overlaps(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
        return a_start < b_end and b_start < a_end

    def create_schedule(
        self,
        *,
        course_id: int,
        teacher_id: int,
        classroom_id: int,
        term_id: int,
        day_of_week: str,
        start_time: time,
        end_time: time,
    ) -> Schedule:
        self.catalog.assert_term_writable(term_id)
        if start_time >= end_time:
            raise ValueError("INVALID_TIME_RANGE")
        course = self.db.get(Course, course_id)
        if course is None:
            raise LookupError("COURSE_NOT_FOUND")
        if course.term_id != term_id:
            raise ValueError("TERM_COURSE_MISMATCH")
        if self.db.get(Teacher, teacher_id) is None:
            raise LookupError("TEACHER_NOT_FOUND")
        if self.db.get(Classroom, classroom_id) is None:
            raise LookupError("CLASSROOM_NOT_FOUND")
        if not self.teaching_assignment_exists(
            teacher_id=teacher_id, course_id=course_id, term_id=term_id
        ):
            raise ValueError("TEACHER_NOT_ASSIGNED")

        day = day_of_week.upper()
        existing = self.db.scalars(
            select(Schedule).where(
                Schedule.term_id == term_id,
                Schedule.day_of_week == day,
            )
        ).all()
        for row in existing:
            if not self._overlaps(start_time, end_time, row.start_time, row.end_time):
                continue
            if row.teacher_id == teacher_id:
                raise ScheduleConflictError("TEACHER_BUSY")
            if row.classroom_id == classroom_id:
                raise ScheduleConflictError("CLASSROOM_BUSY")
            if row.course_id == course_id:
                raise ScheduleConflictError("COURSE_DUPLICATE_SLOT")

        sched = Schedule(
            course_id=course_id,
            teacher_id=teacher_id,
            classroom_id=classroom_id,
            term_id=term_id,
            day_of_week=day,
            start_time=start_time,
            end_time=end_time,
        )
        self.db.add(sched)
        self.db.commit()
        self.db.refresh(sched)
        return sched

    def list_schedules(self, term_id: Optional[int] = None) -> Sequence[Schedule]:
        stmt = select(Schedule).order_by(Schedule.id)
        if term_id is not None:
            stmt = stmt.where(Schedule.term_id == term_id)
        return self.db.scalars(stmt).all()

    def delete_schedule(self, schedule_id: int) -> Schedule:
        row = self.db.get(Schedule, schedule_id)
        if row is None:
            raise LookupError("SCHEDULE_NOT_FOUND")
        self.db.delete(row)
        self.db.commit()
        return row
