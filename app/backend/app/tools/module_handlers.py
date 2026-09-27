"""Execute module CRUD tools through domain services."""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.models import Student, Teacher, User
from app.tools.module_ops import MODULE_TOOLS


def _limit(params: dict, default: int = 25) -> int:
    try:
        value = int(params.get("limit") or default)
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, 50))


def _matches(row: dict[str, Any], q: str | None, status: str | None) -> bool:
    if status and str(row.get("status") or "").upper() != str(status).upper():
        return False
    if not q:
        return True
    needle = str(q).lower()
    return any(needle in str(v).lower() for v in row.values() if v is not None)


def _filter(rows: list[dict[str, Any]], params: dict) -> list[dict[str, Any]]:
    q = params.get("q") or params.get("query") or params.get("filtro")
    status = params.get("status")
    out = [row for row in rows if _matches(row, q, status)]
    return out[: _limit(params)]


def _public_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "cedula": user.cedula,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "status": user.status,
        "roles": user.role_codes() if hasattr(user, "role_codes") else [],
    }


def _opt_int(params: dict, key: str) -> int | None:
    raw = params.get(key)
    if raw in (None, "", "CURRENT_USER"):
        return None
    return int(raw)


def execute_module(db: Session, tool_name: str, params: dict, current: CurrentUser, *, bypass: bool = False) -> Any:
    if tool_name not in MODULE_TOOLS:
        raise ValueError(f"UNKNOWN_TOOL:{tool_name}")
    try:
        return _dispatch(db, tool_name, dict(params or {}), current, bypass=bypass)
    except (LookupError, ValueError, PermissionError) as exc:
        return {"error": str(exc)}


def _dispatch(db: Session, tool: str, params: dict, current: CurrentUser, *, bypass: bool) -> Any:
    from app.services.catalog_service import CatalogService
    from app.services.operations_service import OperationsService
    from app.services.platform_service import PlatformService
    from app.services.role_service import RoleService
    from app.services.user_service import UserService

    catalog = CatalogService(db)
    ops = OperationsService(db)
    users = UserService(db)
    roles = RoleService(db)
    platform = PlatformService(db)

    if tool == "list_users":
        rows = [_public_user(u) for u in users.list_users()]
        role = (params.get("role") or "").upper()
        if role:
            rows = [r for r in rows if role in (r.get("roles") or [])]
        return _filter(rows, params)
    if tool == "get_user":
        return _public_user(users.get_user(int(params["user_id"])))
    if tool == "create_user":
        user = users.create_user(
            username=str(params["username"]),
            email=str(params["email"]),
            password=str(params.get("password") or "Lab12345!"),
            cedula=str(params["cedula"]),
            role_codes=list(params.get("role_codes") or []),
            first_name=str(params.get("first_name") or ""),
            last_name=str(params.get("last_name") or ""),
        )
        return _public_user(user)
    if tool == "update_user":
        user = users.update_user(
            int(params["user_id"]),
            first_name=params.get("first_name"),
            last_name=params.get("last_name"),
            email=params.get("email"),
            phone=params.get("phone"),
        )
        return _public_user(user)
    if tool == "set_user_status":
        return _public_user(users.set_status(int(params["user_id"]), str(params["status"]).upper()))
    if tool == "delete_user":
        return _public_user(users.soft_delete(int(params["user_id"])))
    if tool == "assign_user_roles":
        return _public_user(users.assign_roles(int(params["user_id"]), list(params.get("role_codes") or [])))
    if tool == "list_roles":
        return _filter(
            [{"id": r.id, "code": r.code, "name": r.name, "status": "ACTIVE" if r.is_active else "INACTIVE"} for r in roles.list_roles()],
            params,
        )
    if tool == "list_permissions":
        return _filter(
            [{"id": p.id, "code": p.code, "module": p.module, "description": p.description} for p in roles.list_permissions()],
            params,
        )
    if tool == "create_role":
        role = roles.create_role(str(params["code"]).upper(), str(params["name"]), str(params.get("description") or ""))
        return {"id": role.id, "code": role.code, "name": role.name}
    if tool == "assign_role_permissions":
        role = roles.assign_permissions(str(params["role_code"]).upper(), list(params.get("permission_codes") or []))
        return {"id": role.id, "code": role.code, "name": role.name}
    if tool == "list_careers":
        return _filter([{"id": c.id, "code": c.code, "name": c.name, "status": c.status} for c in catalog.list_careers()], params)
    if tool == "create_career":
        c = catalog.create_career(
            code=str(params["code"]),
            name=str(params["name"]),
            modality=str(params.get("modality") or "PRESENCIAL"),
            duration_semesters=int(params.get("duration_semesters") or 10),
        )
        return {"id": c.id, "code": c.code, "name": c.name, "status": c.status}
    if tool == "set_career_status":
        c = catalog.set_career_status(int(params["career_id"]), str(params["status"]).upper())
        return {"id": c.id, "code": c.code, "status": c.status}
    if tool == "list_subjects":
        return _filter([{"id": s.id, "code": s.code, "name": s.name, "status": s.status} for s in catalog.list_subjects()], params)
    if tool == "create_subject":
        s = catalog.create_subject(
            code=str(params["code"]),
            name=str(params["name"]),
            credits=Decimal(str(params.get("credits") or "3")),
        )
        return {"id": s.id, "code": s.code, "name": s.name, "status": s.status}
    if tool == "set_subject_status":
        s = catalog.set_subject_status(int(params["subject_id"]), str(params["status"]).upper())
        return {"id": s.id, "code": s.code, "status": s.status}
    if tool == "list_curricula":
        return _filter(
            [{"id": c.id, "career_id": c.career_id, "version": c.version, "status": c.status} for c in catalog.list_curricula()],
            params,
        )
    if tool == "create_curriculum":
        c = catalog.create_curriculum(career_id=int(params["career_id"]), version=str(params["version"]))
        return {"id": c.id, "career_id": c.career_id, "version": c.version, "status": c.status}
    if tool == "list_terms":
        return _filter(
            [
                {
                    "id": t.id,
                    "code": t.code,
                    "name": t.name,
                    "status": t.status,
                    "is_current": t.is_current,
                }
                for t in catalog.list_terms()
            ],
            params,
        )
    if tool == "create_term":
        t = catalog.create_term(
            code=str(params["code"]),
            name=str(params["name"]),
            start_date=date.fromisoformat(str(params["start_date"])),
            end_date=date.fromisoformat(str(params["end_date"])),
            status=str(params.get("status") or "PLANNED"),
        )
        return {"id": t.id, "code": t.code, "name": t.name, "status": t.status}
    if tool == "set_term_status":
        t = catalog.set_term_status(int(params["term_id"]), str(params["status"]).upper())
        return {"id": t.id, "code": t.code, "status": t.status}
    if tool == "list_students":
        return _filter(
            [
                {"id": s.id, "student_code": s.student_code, "user_id": s.user_id, "status": s.status}
                for s in catalog.list_students()
            ],
            params,
        )
    if tool == "create_student":
        s = catalog.create_student(
            user_id=int(params["user_id"]),
            student_code=str(params["student_code"]),
            career_id=_opt_int(params, "career_id"),
        )
        return {"id": s.id, "student_code": s.student_code, "status": s.status}
    if tool == "set_student_status":
        s = catalog.set_student_status(int(params["student_id"]), str(params["status"]).upper())
        return {"id": s.id, "student_code": s.student_code, "status": s.status}
    if tool == "list_teachers":
        return _filter(
            [
                {"id": t.id, "teacher_code": t.teacher_code, "user_id": t.user_id, "status": t.status}
                for t in catalog.list_teachers()
            ],
            params,
        )
    if tool == "create_teacher":
        t = catalog.create_teacher(
            user_id=int(params["user_id"]),
            teacher_code=str(params["teacher_code"]),
            specialty=params.get("specialty"),
        )
        return {"id": t.id, "teacher_code": t.teacher_code, "status": t.status}
    if tool == "set_teacher_status":
        t = catalog.set_teacher_status(int(params["teacher_id"]), str(params["status"]).upper())
        return {"id": t.id, "teacher_code": t.teacher_code, "status": t.status}
    if tool == "list_courses":
        teacher_id = None
        student_id = None
        if "TEACHER" in current.roles and "ADMINISTRATOR" not in current.roles:
            teacher = db.scalar(select(Teacher).where(Teacher.user_id == current.user.id))
            teacher_id = teacher.id if teacher else None
        if "STUDENT" in current.roles and "ADMINISTRATOR" not in current.roles:
            student = db.scalar(
                select(Student).where(Student.user_id == current.user.id, Student.deleted_at.is_(None))
            )
            student_id = student.id if student else None
        rows = ops.list_courses(
            term_id=_opt_int(params, "term_id"),
            teacher_id=teacher_id,
            student_id=student_id,
        )
        return _filter(
            [
                {
                    "id": c.id,
                    "subject_id": c.subject_id,
                    "term_id": c.term_id,
                    "parallel_code": c.parallel_code,
                    "status": c.status,
                    "capacity": c.capacity,
                }
                for c in rows
            ],
            params,
        )
    if tool == "create_course":
        c = ops.create_course(
            subject_id=int(params["subject_id"]),
            term_id=int(params["term_id"]),
            parallel_code=str(params.get("parallel_code") or "A"),
            capacity=int(params.get("capacity") or 40),
        )
        return {"id": c.id, "subject_id": c.subject_id, "term_id": c.term_id, "status": c.status}
    if tool == "update_course":
        c = ops.update_course(
            int(params["course_id"]),
            capacity=_opt_int(params, "capacity"),
            parallel_code=params.get("parallel_code"),
        )
        return {"id": c.id, "parallel_code": c.parallel_code, "capacity": c.capacity, "status": c.status}
    if tool == "set_course_status":
        c = ops.set_course_status(int(params["course_id"]), str(params["status"]).upper())
        return {"id": c.id, "status": c.status}
    if tool == "list_assignments":
        rows = ops.list_assignments(course_id=_opt_int(params, "course_id"))
        return _filter(
            [
                {
                    "id": a.id,
                    "teacher_id": a.teacher_id,
                    "course_id": a.course_id,
                    "term_id": a.term_id,
                    "status": a.status,
                }
                for a in rows
            ],
            params,
        )
    if tool == "create_assignment":
        a = ops.assign_teacher(
            teacher_id=int(params["teacher_id"]),
            course_id=int(params["course_id"]),
            term_id=int(params["term_id"]),
        )
        return {"id": a.id, "teacher_id": a.teacher_id, "course_id": a.course_id, "status": a.status}
    if tool == "list_enrollments":
        rows = ops.list_enrollments(course_id=_opt_int(params, "course_id"))
        sid = _opt_int(params, "student_id")
        items = [
            {
                "id": e.id,
                "student_id": e.student_id,
                "course_id": e.course_id,
                "term_id": e.term_id,
                "status": e.status,
            }
            for e in rows
            if sid is None or e.student_id == sid
        ]
        return _filter(items, params)
    if tool == "list_classrooms":
        return _filter(
            [{"id": r.id, "code": r.code, "name": r.name, "capacity": r.capacity} for r in ops.list_classrooms()],
            params,
        )
    if tool == "create_classroom":
        room = ops.create_classroom(
            code=str(params["code"]),
            name=str(params["name"]),
            capacity=int(params.get("capacity") or 40),
        )
        return {"id": room.id, "code": room.code, "name": room.name}
    if tool == "create_schedule":
        sch = ops.create_schedule(
            course_id=int(params["course_id"]),
            teacher_id=int(params["teacher_id"]),
            classroom_id=int(params["classroom_id"]),
            term_id=int(params["term_id"]),
            day_of_week=str(params.get("day_of_week") or "MON"),
            start_time=time.fromisoformat(str(params["start_time"])),
            end_time=time.fromisoformat(str(params["end_time"])),
        )
        return {"id": sch.id, "course_id": sch.course_id, "day_of_week": sch.day_of_week}
    if tool == "delete_schedule":
        sch = ops.delete_schedule(int(params["schedule_id"]))
        return {"id": sch.id, "status": "DELETED"}
    if tool == "list_evaluations":
        from app.models.evaluation import Evaluation
        from app.services.evaluation_service import EvaluationService

        course_id = _opt_int(params, "course_id")
        if course_id:
            rows = EvaluationService(db).list_evaluations(course_id)
        else:
            rows = list(db.scalars(select(Evaluation).order_by(Evaluation.id.asc()).limit(50)))
        return _filter(
            [
                {
                    "id": ev.id,
                    "course_id": ev.course_id,
                    "name": ev.name,
                    "weight_percent": str(ev.weight_percent),
                    "status": ev.status,
                }
                for ev in rows
            ],
            params,
        )
    if tool == "create_evaluation":
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService(db)
        as_admin = bypass or "ADMINISTRATOR" in current.roles
        teacher = None if as_admin else svc.teacher_for_user(current.user.id)
        ev = svc.create_evaluation(
            teacher=teacher,
            course_id=int(params["course_id"]),
            name=str(params["name"]),
            weight_percent=Decimal(str(params.get("weight_percent") or "20")),
            as_admin=as_admin,
        )
        return {"id": ev.id, "name": ev.name, "course_id": ev.course_id, "status": ev.status}
    if tool == "create_attendance_session":
        from app.services.evaluation_service import EvaluationService

        svc = EvaluationService(db)
        as_admin = bypass or "ADMINISTRATOR" in current.roles
        teacher = None if as_admin else svc.teacher_for_user(current.user.id)
        session = svc.create_attendance_session(
            teacher=teacher,
            course_id=int(params["course_id"]),
            session_date=date.fromisoformat(str(params["session_date"])),
            topic=params.get("topic"),
            as_admin=as_admin,
        )
        return {"id": session.id, "course_id": session.course_id, "session_date": str(session.session_date)}
    if tool == "list_notifications":
        unread = str(params.get("unread_only") or "").lower() in {"1", "true", "si", "sí"}
        rows = platform.list_notifications(current.user.id, unread_only=unread)
        return [
            {"id": n.id, "title": n.title, "body": n.body, "read": n.read_flag}
            for n in rows[: _limit(params)]
        ]
    if tool == "create_notification":
        target = _opt_int(params, "user_id") or current.user.id
        n = platform.create_notification(
            user_id=target,
            type_=str(params.get("type") or "INFO"),
            title=str(params.get("title") or "Aviso"),
            body=str(params.get("body") or params.get("message") or ""),
        )
        return {"id": n.id, "title": n.title, "user_id": n.user_id}
    if tool == "get_dashboard":
        return platform.dashboard_for(user=current.user, roles=current.roles)
    if tool == "list_audit":
        from app.models import AuditEvent

        rows = list(db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(_limit(params))))
        return [
            {
                "id": a.id,
                "action": a.action,
                "module": a.module,
                "status": a.status,
                "user_id": a.user_id,
            }
            for a in rows
        ]
    raise ValueError(f"UNKNOWN_TOOL:{tool}")
