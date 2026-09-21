# Ref: RNF-UX / demo UI | Skill: K-022/K-024 | Fase: post-F12
"""Seed academic demo so /ui/ Notas + Asistencia work with teacher1/student1."""

from __future__ import annotations

import sys
from datetime import date, time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from sqlalchemy import select

from app.db.session import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.models import (
    AcademicTerm,
    AttendanceRecord,
    AttendanceSession,
    Career,
    Classroom,
    Course,
    Curriculum,
    CurriculumSubject,
    Enrollment,
    Evaluation,
    EvaluationType,
    Grade,
    KardexEntry,
    Notification,
    Schedule,
    Student,
    Subject,
    Teacher,
    TeachingAssignment,
    User,
)


def _one(db, model, **filters):
    return db.scalar(select(model).filter_by(**filters))


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        teacher_user = _one(db, User, username="teacher1")
        student_user = _one(db, User, username="student1")
        if not teacher_user or not student_user:
            raise SystemExit("FAIL: run scripts/seed_iam.py first (teacher1/student1 missing)")

        career = _one(db, Career, code="IS-DEMO")
        if career is None:
            career = Career(code="IS-DEMO", name="Ingeniería de Software (demo)", status="ACTIVE")
            db.add(career)
            db.flush()

        subject = _one(db, Subject, code="ZT101")
        if subject is None:
            subject = Subject(
                code="ZT101",
                name="Zero Trust Aplicado",
                description="Curso demo laboratorio",
                credits=Decimal("3.00"),
                hours=48,
                status="ACTIVE",
            )
            db.add(subject)
            db.flush()

        term = _one(db, AcademicTerm, code="2026-DEMO")
        if term is None:
            term = AcademicTerm(
                code="2026-DEMO",
                name="Periodo Demo 2026",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 6, 30),
                status="ACTIVE",
                is_current=True,
            )
            db.add(term)
            db.flush()

        teacher = _one(db, Teacher, user_id=teacher_user.id)
        if teacher is None:
            teacher = Teacher(
                user_id=teacher_user.id,
                teacher_code="DOC-DEMO",
                specialty="Seguridad",
                status="ACTIVE",
            )
            db.add(teacher)
            db.flush()

        student = _one(db, Student, user_id=student_user.id)
        if student is None:
            student = Student(
                user_id=student_user.id,
                student_code="EST-DEMO",
                career_id=career.id,
                level="1",
                admission_date=date(2026, 1, 10),
                status="ACTIVE",
            )
            db.add(student)
            db.flush()

        curriculum = _one(db, Curriculum, career_id=career.id, version="2026.1")
        if curriculum is None:
            curriculum = Curriculum(career_id=career.id, version="2026.1", status="ACTIVE")
            db.add(curriculum)
            db.flush()
        cs = _one(db, CurriculumSubject, curriculum_id=curriculum.id, subject_id=subject.id)
        if cs is None:
            db.add(
                CurriculumSubject(
                    curriculum_id=curriculum.id,
                    subject_id=subject.id,
                    level=1,
                    semester=1,
                    credits=subject.credits or Decimal("3.00"),
                )
            )

        course = _one(db, Course, subject_id=subject.id, term_id=term.id, parallel_code="A")
        if course is None:
            course = Course(
                subject_id=subject.id,
                term_id=term.id,
                parallel_code="A",
                capacity=30,
                status="ACTIVE",
            )
            db.add(course)
            db.flush()

        assignment = _one(
            db,
            TeachingAssignment,
            teacher_id=teacher.id,
            course_id=course.id,
            term_id=term.id,
        )
        if assignment is None:
            db.add(
                TeachingAssignment(
                    teacher_id=teacher.id,
                    course_id=course.id,
                    term_id=term.id,
                    status="ACTIVE",
                )
            )

        enrollment = _one(
            db,
            Enrollment,
            student_id=student.id,
            course_id=course.id,
            term_id=term.id,
        )
        if enrollment is None:
            db.add(
                Enrollment(
                    student_id=student.id,
                    course_id=course.id,
                    term_id=term.id,
                    status="ACTIVE",
                )
            )

        classroom = _one(db, Classroom, code="AULA-DEMO")
        if classroom is None:
            classroom = Classroom(code="AULA-DEMO", name="Aula Demo", capacity=40)
            db.add(classroom)
            db.flush()

        sched = db.scalar(
            select(Schedule).where(
                Schedule.course_id == course.id,
                Schedule.day_of_week == "MON",
            )
        )
        if sched is None:
            db.add(
                Schedule(
                    course_id=course.id,
                    teacher_id=teacher.id,
                    classroom_id=classroom.id,
                    term_id=term.id,
                    day_of_week="MON",
                    start_time=time(8, 0),
                    end_time=time(10, 0),
                )
            )

        ev_type = _one(db, EvaluationType, code="PARTIAL")
        if ev_type is None:
            ev_type = EvaluationType(code="PARTIAL", name="Parcial")
            db.add(ev_type)
            db.flush()

        evaluation = db.scalar(
            select(Evaluation).where(
                Evaluation.course_id == course.id,
                Evaluation.name == "Parcial 1 Demo",
            )
        )
        if evaluation is None:
            evaluation = Evaluation(
                course_id=course.id,
                evaluation_type_id=ev_type.id,
                name="Parcial 1 Demo",
                weight_percent=Decimal("30.00"),
                due_date=date(2026, 3, 15),
                status="ACTIVE",
            )
            db.add(evaluation)
            db.flush()

        grade = _one(db, Grade, evaluation_id=evaluation.id, student_id=student.id)
        if grade is None:
            db.add(
                Grade(
                    evaluation_id=evaluation.id,
                    student_id=student.id,
                    score=Decimal("85.50"),
                    comment="Nota demo seed",
                    graded_by_teacher_id=teacher.id,
                )
            )

        kardex = db.scalar(
            select(KardexEntry).where(
                KardexEntry.student_id == student.id,
                KardexEntry.term_id == term.id,
                KardexEntry.subject_id == subject.id,
            )
        )
        if kardex is None:
            db.add(
                KardexEntry(
                    student_id=student.id,
                    term_id=term.id,
                    subject_id=subject.id,
                    course_id=course.id,
                    final_grade=Decimal("85.50"),
                    academic_status="IN_PROGRESS",
                    credits=Decimal("3.00"),
                )
            )

        session = db.scalar(
            select(AttendanceSession).where(
                AttendanceSession.course_id == course.id,
                AttendanceSession.session_date == date(2026, 2, 10),
            )
        )
        if session is None:
            session = AttendanceSession(
                course_id=course.id,
                session_date=date(2026, 2, 10),
                topic="Intro Zero Trust",
            )
            db.add(session)
            db.flush()

        att = _one(db, AttendanceRecord, session_id=session.id, student_id=student.id)
        if att is None:
            db.add(
                AttendanceRecord(
                    session_id=session.id,
                    student_id=student.id,
                    status="PRESENT",
                    notes="Demo",
                )
            )

        notif = db.scalar(
            select(Notification).where(
                Notification.user_id == student_user.id,
                Notification.title == "Bienvenido al laboratorio SIGA",
            )
        )
        if notif is None:
            db.add(
                Notification(
                    user_id=student_user.id,
                    type="ACADEMIC",
                    title="Bienvenido al laboratorio SIGA",
                    body="Ya puedes ver tus notas demo en /ui/ → Notas.",
                    read_flag=False,
                )
            )
        notif_t = db.scalar(
            select(Notification).where(
                Notification.user_id == teacher_user.id,
                Notification.title == "Curso demo asignado",
            )
        )
        if notif_t is None:
            db.add(
                Notification(
                    user_id=teacher_user.id,
                    type="INFO",
                    title="Curso demo asignado",
                    body=f"Curso id={course.id} · evaluación id={evaluation.id} · estudiante id={student.id}",
                    read_flag=False,
                )
            )

        db.commit()
        print("OK: academic demo seed completed")
        print(f"  course_id={course.id}")
        print(f"  evaluation_id={evaluation.id}")
        print(f"  student_id={student.id}")
        print(f"  teacher_id={teacher.id}")
        print(f"  attendance_session_id={session.id}")
        print("  UI: login student1 -> Notas -> Mis notas")
        print("  UI: login teacher1 -> Notas (curso) / Asistencia")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
