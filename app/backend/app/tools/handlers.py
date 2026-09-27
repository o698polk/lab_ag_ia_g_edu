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
    Schedule,
    Student,
    User,
)
from app.services.platform_service import PlatformService


def _fallback_student(db: Session) -> Student | None:
    preferred = db.scalar(
        select(Student)
        .join(User, User.id == Student.user_id)
        .where(User.username == "student1", Student.deleted_at.is_(None))
    )
    if preferred:
        return preferred
    return db.scalar(
        select(Student).where(Student.deleted_at.is_(None)).order_by(Student.id.asc())
    )


def _student_id(params: dict, db: Session | None = None, *, bypass: bool = False) -> int | dict[str, str]:
    raw = params.get("student_id")
    if raw in (None, "", "CURRENT_USER", "{{CURRENT_USER}}", "ASSIGNED"):
        if bypass and db is not None:
            student = _fallback_student(db)
            if student:
                return student.id
        return {"error": "STUDENT_PROFILE_REQUIRED"}
    try:
        return int(raw)
    except (TypeError, ValueError):
        return {"error": "STUDENT_NOT_FOUND"}


def _teacher_assigned_student_ids(db: Session, current: CurrentUser) -> list[int]:
    from app.models import Teacher
    from app.models.operations import Enrollment, TeachingAssignment

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == current.user.id))
    if teacher is None:
        return []
    course_ids = list(
        db.scalars(
            select(TeachingAssignment.course_id).where(
                TeachingAssignment.teacher_id == teacher.id,
                TeachingAssignment.status == "ACTIVE",
            )
        )
    )
    if not course_ids:
        return []
    return list(
        db.scalars(
            select(Enrollment.student_id)
            .where(Enrollment.course_id.in_(course_ids), Enrollment.status == "ACTIVE")
            .distinct()
        )
    )


def _scope_student_ids(
    params: dict, db: Session, current: CurrentUser, *, bypass: bool = False
) -> list[int] | dict[str, str]:
    raw = params.get("student_id")
    if raw not in (None, "", "CURRENT_USER", "{{CURRENT_USER}}", "ASSIGNED"):
        try:
            return [int(raw)]
        except (TypeError, ValueError):
            return {"error": "STUDENT_NOT_FOUND"}
    roles = current.roles or []
    if "STUDENT" in roles:
        sid = _student_id({"student_id": "CURRENT_USER"}, db, bypass=bypass)
        if isinstance(sid, dict):
            return sid
        return [sid]
    if "TEACHER" in roles:
        return _teacher_assigned_student_ids(db, current)
    if bypass or "ADMINISTRATOR" in roles:
        return list(
            db.scalars(
                select(Student.id)
                .where(Student.deleted_at.is_(None))
                .order_by(Student.id.asc())
                .limit(25)
            )
        )
    return {"error": "STUDENT_PROFILE_REQUIRED"}


def _grade_items_for_student(db: Session, sid: int) -> list[dict[str, Any]]:
    from app.services.evaluation_service import EvaluationService

    grades = list(db.scalars(select(Grade).where(Grade.student_id == sid)))
    items: list[dict[str, Any]] = [
        {
            "id": g.id,
            "evaluation_id": g.evaluation_id,
            "student_id": g.student_id,
            "score": str(g.score),
            "source": "evaluation",
        }
        for g in grades
    ]
    for row in EvaluationService(db).student_academic(sid):
        official = row.get("official_grade")
        average = row.get("final_average")
        score = official if official is not None else average
        items.append(
            {
                "student_id": sid,
                "course_id": row.get("course_id"),
                "subject_name": row.get("subject_name") or "",
                "course_name": row.get("course_name") or "",
                "teacher_name": row.get("teacher_name") or "",
                "term_name": row.get("term_name") or "",
                "first_partial": row.get("first_partial"),
                "second_partial": row.get("second_partial"),
                "official_grade": official,
                "academic_status": row.get("academic_status"),
                "attendance_pct": row.get("attendance_pct"),
                "score": str(score if score is not None else 0),
                "source": "official",
            }
        )
    return items


def execute(
    db: Session, tool_name: str, params: dict, current: CurrentUser, *, bypass: bool = False
) -> Any:
    if tool_name == "get_student_profile":
        sid = _student_id(params, db, bypass=bypass)
        if isinstance(sid, dict):
            return sid
        student = db.get(Student, sid)
        if student is None:
            return {"error": "STUDENT_NOT_FOUND"}
        return {
            "id": student.id,
            "student_code": student.student_code,
            "status": student.status,
        }
    if tool_name == "get_grades":
        sids = _scope_student_ids(params, db, current, bypass=bypass)
        if isinstance(sids, dict):
            return sids
        items: list[dict[str, Any]] = []
        for sid in sids:
            items.extend(_grade_items_for_student(db, sid))
        return items
    if tool_name == "get_attendance":
        sids = _scope_student_ids(params, db, current, bypass=bypass)
        if isinstance(sids, dict):
            return sids
        from app.services.evaluation_service import EvaluationService

        items: list[dict[str, Any]] = []
        for sid in sids:
            q = select(AttendanceRecord).where(AttendanceRecord.student_id == sid)
            if params.get("course_id"):
                q = q.join(AttendanceSession).where(
                    AttendanceSession.course_id == int(params["course_id"])
                )
            rows = list(db.scalars(q))
            if rows:
                items.extend(
                    {
                        "session_id": r.session_id,
                        "student_id": r.student_id,
                        "status": r.status,
                    }
                    for r in rows
                )
                continue
            items.extend(
                {
                    "student_id": sid,
                    "course_id": row.get("course_id"),
                    "subject_name": row.get("subject_name") or "",
                    "attendance_pct": row.get("attendance_pct"),
                    "status": row.get("academic_status") or "IN_PROGRESS",
                }
                for row in EvaluationService(db).student_academic(sid)
            )
        return items
    if tool_name == "get_kardex":
        sids = _scope_student_ids(params, db, current, bypass=bypass)
        if isinstance(sids, dict):
            return sids
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService(db)
        items: list[dict[str, Any]] = []
        for sid in sids:
            for k in svc.list_kardex(sid):
                items.append(
                    {
                        "id": k.id,
                        "student_id": sid,
                        "subject_id": k.subject_id,
                        **svc.kardex_labels(k),
                        "final_grade": str(k.final_grade) if k.final_grade is not None else None,
                        "academic_status": k.academic_status,
                        "score": str(k.final_grade if k.final_grade is not None else 0),
                    }
                )
        return items
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
        # Sensitive — only reached on ALLOW or lab-open bypass
        from app.services.evaluation_service import EvaluationService

        sid = _student_id(params, db, bypass=bypass)
        if isinstance(sid, dict):
            return sid
        svc = EvaluationService(db)
        as_admin = bypass or "ADMINISTRATOR" in current.roles
        teacher = None if as_admin else svc.teacher_for_user(current.user.id)
        grade = svc.upsert_grade(
            teacher=teacher,
            evaluation_id=int(params["evaluation_id"]),
            student_id=sid,
            score=Decimal(str(params["score"])),
            comment=params.get("comment"),
            as_admin=as_admin,
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
        as_admin = bypass or "ADMINISTRATOR" in current.roles
        teacher = None if as_admin else svc.teacher_for_user(current.user.id)
        rec = svc.mark_attendance(
            teacher=teacher,
            session_id=int(params["session_id"]),
            student_id=int(params["student_id"]),
            status=params["status"],
            notes=params.get("notes"),
            as_admin=as_admin,
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
    from app.tools.module_handlers import execute_module
    from app.tools.module_ops import MODULE_TOOLS

    if tool_name in MODULE_TOOLS:
        return execute_module(db, tool_name, params, current, bypass=bypass)
    raise ValueError(f"UNKNOWN_TOOL:{tool_name}")
