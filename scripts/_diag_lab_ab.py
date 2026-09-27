"""Diagnose why Lab A EST-011 errors on live MySQL."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Enrollment, Evaluation, Grade, Student, User  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == "student1"))
        print("student1 user", None if user is None else {"id": user.id, "policies": user.policies_enforced})
        student = None
        if user:
            student = db.scalar(select(Student).where(Student.user_id == user.id, Student.deleted_at.is_(None)))
        print("student profile", None if student is None else {"id": student.id, "code": student.student_code})
        ev1 = db.get(Evaluation, 1)
        print("evaluation 1", None if ev1 is None else {"id": ev1.id, "course_id": ev1.course_id, "name": ev1.name})
        if student:
            ens = list(
                db.scalars(
                    select(Enrollment).where(Enrollment.student_id == student.id, Enrollment.status == "ACTIVE")
                )
            )
            print("active enrollments", [{"id": e.id, "course_id": e.course_id, "term_id": e.term_id} for e in ens])
            evs = list(
                db.scalars(
                    select(Evaluation)
                    .join(Enrollment, Enrollment.course_id == Evaluation.course_id)
                    .where(Enrollment.student_id == student.id, Enrollment.status == "ACTIVE")
                )
            )
            print("evals for student", [{"id": e.id, "course_id": e.course_id, "name": e.name} for e in evs])
            grades = list(db.scalars(select(Grade).where(Grade.student_id == student.id)))
            print("grades", [{"id": g.id, "ev": g.evaluation_id, "score": str(g.score)} for g in grades])
        if ev1 is not None and student is not None:
            en = db.scalar(
                select(Enrollment).where(
                    Enrollment.course_id == ev1.course_id,
                    Enrollment.student_id == student.id,
                    Enrollment.status == "ACTIVE",
                )
            )
            print("student enrolled in ev1 course", en is not None)
    finally:
        db.close()


if __name__ == "__main__":
    main()
