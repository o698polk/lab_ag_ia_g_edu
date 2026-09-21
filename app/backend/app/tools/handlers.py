# Ref: BL-O6-004 | Skill: K-019 | Fase: F6
"""Tool handlers — executed only after Gateway ALLOW. No AI→SQL."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.models import (
    AttendanceRecord,
    AttendanceSession,
    Grade,
    KardexEntry,
    Schedule,
    Student,
)
from app.services.platform_service import PlatformService


def execute(
    db: Session, tool_name: str, params: dict, current: CurrentUser
) -> Any:
    if tool_name == "get_student_profile":
        sid = int(params["student_id"])
        student = db.get(Student, sid)
        if student is None:
            return {"error": "STUDENT_NOT_FOUND"}
        return {
            "id": student.id,
            "student_code": student.student_code,
            "status": student.status,
        }
    if tool_name == "get_grades":
        sid = int(params["student_id"])
        grades = list(db.scalars(select(Grade).where(Grade.student_id == sid)))
        return [
            {
                "id": g.id,
                "evaluation_id": g.evaluation_id,
                "student_id": g.student_id,
                "score": str(g.score),
            }
            for g in grades
        ]
    if tool_name == "get_attendance":
        sid = int(params["student_id"])
        q = select(AttendanceRecord).where(AttendanceRecord.student_id == sid)
        if params.get("course_id"):
            q = q.join(AttendanceSession).where(
                AttendanceSession.course_id == int(params["course_id"])
            )
        rows = list(db.scalars(q))
        return [
            {"session_id": r.session_id, "student_id": r.student_id, "status": r.status}
            for r in rows
        ]
    if tool_name == "get_kardex":
        sid = int(params["student_id"])
        rows = list(db.scalars(select(KardexEntry).where(KardexEntry.student_id == sid)))
        return [
            {
                "id": k.id,
                "subject_id": k.subject_id,
                "final_grade": str(k.final_grade) if k.final_grade is not None else None,
                "academic_status": k.academic_status,
            }
            for k in rows
        ]
    if tool_name == "get_schedule":
        rows = list(db.scalars(select(Schedule).limit(50)))
        return [
            {
                "id": s.id,
                "course_id": s.course_id,
                "day_of_week": s.day_of_week,
                "start_time": str(s.start_time),
                "end_time": str(s.end_time),
            }
            for s in rows
        ]
    if tool_name == "generate_report":
        return PlatformService(db).generate_report(
            user=current.user,
            report_type=params.get("report_type", "students"),
            format_=params.get("format", "JSON"),
            parameters=params.get("parameters"),
        )
    if tool_name == "update_grade":
        # Sensitive — only reached on ALLOW
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService(db)
        teacher = svc.teacher_for_user(current.user.id)
        grade = svc.upsert_grade(
            teacher=teacher,
            evaluation_id=int(params["evaluation_id"]),
            student_id=int(params["student_id"]),
            score=Decimal(str(params["score"])),
            comment=params.get("comment"),
        )
        return {
            "id": grade.id,
            "evaluation_id": grade.evaluation_id,
            "student_id": grade.student_id,
            "score": str(grade.score),
        }
    if tool_name == "update_attendance":
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService(db)
        teacher = svc.teacher_for_user(current.user.id)
        rec = svc.mark_attendance(
            teacher=teacher,
            session_id=int(params["session_id"]),
            student_id=int(params["student_id"]),
            status=params["status"],
            notes=params.get("notes"),
        )
        return {"id": rec.id, "status": rec.status}
    if tool_name == "create_enrollment":
        from app.services.operations_service import OperationsService

        enr = OperationsService(db).enroll_student(
            student_id=int(params["student_id"]),
            course_id=int(params["course_id"]),
            term_id=int(params["term_id"]),
        )
        return {"id": enr.id, "status": enr.status}
    if tool_name == "cancel_enrollment":
        from app.services.operations_service import OperationsService

        enr = OperationsService(db).cancel_enrollment(int(params["enrollment_id"]))
        return {"id": enr.id, "status": enr.status}
    raise ValueError(f"UNKNOWN_TOOL:{tool_name}")
