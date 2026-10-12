"""Handlers de tools del gateway IA (SPEC-016)."""

from datetime import datetime

from app.extensions import db
from app.models import (
    Assignment,
    Attendance,
    AuditLog,
    Career,
    Course,
    Enrollment,
    ElevationRequest,
    Grade,
    Notification,
    Role,
    Student,
    Subject,
    Teacher,
    Term,
    User,
)
from app.ai.insecure_mode import is_insecure_mode
from app.services.ai_reports import REPORT_TYPES, generate_report_artifact, user_can_report
from app.services.audit import log_event
from app.services.enrollment import count_active_enrollments, validate_course_capacity
from app.services.grades import apply_grade_rules
from app.services.visibility import apply_course_scope, owned_course_ids, visible_term_ids


def _perm_ok(user, perm: str) -> bool:
    """SPEC-031: en laboratorio no se exige IAM del dominio."""
    if is_insecure_mode():
        return True
    return user.has_permission(perm)


def _owned_courses(user):
    if is_insecure_mode():
        return None
    return owned_course_ids(user)


def _course_scope(query, user, course_column=None):
    if is_insecure_mode():
        return query
    if course_column is not None:
        return apply_course_scope(query, user, course_column)
    return apply_course_scope(query, user)


def _paginate(query, page=1, per_page=50):
    page = max(1, int(page or 1))
    per_page = min(100, max(1, int(per_page or 50)))
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return {"items": items, "page": page, "per_page": per_page, "count": len(items)}


def _page_meta(p):
    """Meta de paginación sin ORM (evita User/Model en JSON de tool_payload)."""
    return {"page": p["page"], "per_page": p["per_page"], "count": p["count"]}


def _deny(msg, required=None):
    return {"ok": False, "error": msg, "required": required}


def _ok(data=None, **extra):
    out = {"ok": True}
    if data is not None:
        out["data"] = data
    # Nunca filtrar 'items' ORM por accidente
    extra.pop("items", None)
    out.update(extra)
    return out


# ─── Lectura ─────────────────────────────────────────────────
def system_stats(user, args):
    # SPEC-030: visión institucional (no disponible para TEACHER/STUDENT del seed)
    if not is_insecure_mode() and not (
        user.has_permission("dashboard.view")
        or user.has_permission("reports.view")
        or user.has_permission("users.view")
    ):
        return _deny(
            "Sin permiso para estadísticas institucionales",
            "dashboard.view|reports.view|users.view",
        )
    return _ok(
        {
            "students": Student.query.count(),
            "teachers": Teacher.query.count(),
            "careers": Career.query.count(),
            "courses": Course.query.count(),
            "enrollments_active": Enrollment.query.filter_by(status="activa").count(),
            "roles": user.get_role_codes(),
        }
    )


def careers_list(user, args):
    if not _perm_ok(user, "careers.view"):
        return _deny("Sin permiso careers.view", "careers.view")
    q = Career.query.order_by(Career.name)
    if args.get("is_active") is not None:
        q = q.filter_by(is_active=bool(args["is_active"]))
    p = _paginate(q, args.get("page"), args.get("per_page"))
    return _ok([c.to_dict() for c in p["items"]], **_page_meta(p))


def careers_get(user, args):
    if not _perm_ok(user, "careers.view"):
        return _deny("Sin permiso careers.view", "careers.view")
    c = Career.query.get(args.get("id"))
    return _ok(c.to_dict()) if c else _deny("Carrera no encontrada")


def subjects_list(user, args):
    if not _perm_ok(user, "subjects.view"):
        return _deny("Sin permiso subjects.view", "subjects.view")
    q = Subject.query.order_by(Subject.name)
    if args.get("career_id"):
        q = q.filter_by(career_id=int(args["career_id"]))
    p = _paginate(q, args.get("page"), args.get("per_page"))
    return _ok([s.to_dict() for s in p["items"]], **_page_meta(p))


def terms_list(user, args):
    if not _perm_ok(user, "terms.view"):
        return _deny("Sin permiso terms.view", "terms.view")
    q = Term.query.order_by(Term.start_date.desc())
    term_ids = None if is_insecure_mode() else visible_term_ids(user)
    if term_ids is not None:
        q = q.filter(Term.id.in_(term_ids or [-1]))
    p = _paginate(q, args.get("page"), args.get("per_page"))
    return _ok([t.to_dict() for t in p["items"]], **_page_meta(p))


def courses_list(user, args):
    if not _perm_ok(user, "courses.view"):
        return _deny("Sin permiso courses.view", "courses.view")
    q = _course_scope(Course.query, user).order_by(Course.name)
    p = _paginate(q, args.get("page"), args.get("per_page"))
    data = []
    for c in p["items"]:
        d = c.to_dict()
        d["enrolled_count"] = count_active_enrollments(c.id)
        data.append(d)
    return _ok(data, **_page_meta(p))


def students_list(user, args):
    if not _perm_ok(user, "students.view"):
        return _deny("Sin permiso students.view", "students.view")
    course_ids = _owned_courses(user)
    if course_ids is not None:
        if not course_ids:
            return _ok([])
        ids = {
            e.student_id
            for e in Enrollment.query.filter(
                Enrollment.course_id.in_(course_ids),
                Enrollment.status == "activa",
            ).all()
        }
        q = Student.query.filter(Student.id.in_(ids or [-1]))
    else:
        q = Student.query
    if args.get("career_id"):
        q = q.filter_by(career_id=int(args["career_id"]))
    p = _paginate(q.order_by(Student.id), args.get("page"), args.get("per_page"))
    return _ok([s.to_dict() for s in p["items"]], **_page_meta(p))


def teachers_list(user, args):
    if not _perm_ok(user, "teachers.view"):
        return _deny("Sin permiso teachers.view", "teachers.view")
    p = _paginate(Teacher.query.order_by(Teacher.id), args.get("page"), args.get("per_page"))
    return _ok([t.to_dict() for t in p["items"]], **_page_meta(p))


def enrollments_list(user, args):
    if not _perm_ok(user, "enrollments.view"):
        return _deny("Sin permiso enrollments.view", "enrollments.view")
    q = _course_scope(Enrollment.query.join(Course), user)
    if not is_insecure_mode() and "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Enrollment.student_id == user.student.id)
    if args.get("course_id"):
        q = q.filter(Enrollment.course_id == int(args["course_id"]))
    p = _paginate(q.order_by(Enrollment.id.desc()), args.get("page"), args.get("per_page"))
    return _ok([e.to_dict() for e in p["items"]], **_page_meta(p))


def grades_list(user, args):
    if not _perm_ok(user, "grades.view"):
        return _deny("Sin permiso grades.view", "grades.view")
    q = _course_scope(Grade.query.join(Course), user)
    if args.get("course_id"):
        q = q.filter(Grade.course_id == int(args["course_id"]))
    if args.get("student_id"):
        q = q.filter(Grade.student_id == int(args["student_id"]))
    if not is_insecure_mode() and "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Grade.student_id == user.student.id)
    p = _paginate(q, args.get("page"), args.get("per_page"))
    return _ok([g.to_dict() for g in p["items"]], **_page_meta(p))


def attendance_list(user, args):
    if not _perm_ok(user, "attendance.view"):
        return _deny("Sin permiso attendance.view", "attendance.view")
    q = _course_scope(Attendance.query.join(Course), user)
    if args.get("course_id"):
        q = q.filter(Attendance.course_id == int(args["course_id"]))
    if not is_insecure_mode() and "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Attendance.student_id == user.student.id)
    p = _paginate(q.order_by(Attendance.session_date.desc()), args.get("page"), args.get("per_page"))
    return _ok([a.to_dict() for a in p["items"]], **_page_meta(p))


def users_list(user, args):
    if not _perm_ok(user, "users.view"):
        return _deny("Sin permiso users.view", "users.view")
    q = User.query.order_by(User.username)
    search = (args.get("search") or args.get("q") or args.get("name") or "").strip()
    if search:
        like = f"%{search}%"
        # full_name es property → buscar por partes / concat
        q = q.filter(
            db.or_(
                User.username.ilike(like),
                User.email.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                (User.first_name + " " + User.last_name).ilike(like),
            )
        )
    p = _paginate(q, args.get("page"), args.get("per_page"))
    return _ok([u.to_dict() for u in p["items"]], **_page_meta(p))


def roles_list(user, args):
    if not _perm_ok(user, "roles.view"):
        return _deny("Sin permiso roles.view", "roles.view")
    return _ok([r.to_dict() for r in Role.query.order_by(Role.code).all()])


def audit_logs_list(user, args):
    if not _perm_ok(user, "audit.view"):
        return _deny("Sin permiso audit.view", "audit.view")
    p = _paginate(AuditLog.query.order_by(AuditLog.created_at.desc()), args.get("page"), args.get("per_page"))
    return _ok([a.to_dict() for a in p["items"]], **_page_meta(p))


def reports_list_types(user, args):
    types = []
    for code, cfg in REPORT_TYPES.items():
        if is_insecure_mode() or user_can_report(user, code):
            types.append({"report_type": code, "title": cfg["title"], "formats": ["pdf", "xlsx", "json", "md"]})
    return _ok(types)


# ─── Mutaciones ──────────────────────────────────────────────
def careers_create(user, args):
    if not _perm_ok(user, "careers.create"):
        return _deny("Sin permiso careers.create", "careers.create")
    c = Career(
        code=args["code"],
        name=args["name"],
        description=args.get("description"),
        duration_semesters=int(args.get("duration_semesters") or 8),
        is_active=bool(args.get("is_active", True)),
    )
    db.session.add(c)
    db.session.commit()
    log_event(user.id, "AI_TOOL_CREATE", "careers", f"id={c.id}")
    return _ok(c.to_dict())


def careers_update(user, args):
    if not _perm_ok(user, "careers.edit"):
        return _deny("Sin permiso careers.edit", "careers.edit")
    c = Career.query.get(args.get("id"))
    if not c:
        return _deny("Carrera no encontrada")
    for f in ("code", "name", "description", "duration_semesters", "is_active"):
        if f in args:
            setattr(c, f, args[f])
    db.session.commit()
    log_event(user.id, "AI_TOOL_UPDATE", "careers", f"id={c.id}")
    return _ok(c.to_dict())


def enrollments_create(user, args):
    if not _perm_ok(user, "enrollments.create"):
        return _deny("Sin permiso enrollments.create", "enrollments.create")
    course_id = int(args["course_id"])
    student_id = int(args["student_id"])
    course = Course.query.get(course_id)
    if not course:
        return _deny("Curso no encontrado")
    err = validate_course_capacity(course)
    if err:
        return _deny(err)
    if Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first():
        return _deny("Ya matriculado en este curso")
    e = Enrollment(student_id=student_id, course_id=course_id, status=args.get("status", "activa"))
    db.session.add(e)
    db.session.commit()
    log_event(user.id, "AI_TOOL_CREATE", "enrollments", f"student={student_id} course={course_id}")
    return _ok(e.to_dict())


def grades_upsert(user, args):
    if not _perm_ok(user, "grades.manage"):
        return _deny("Sin permiso grades.manage", "grades.manage")
    course_id = int(args["course_id"])
    student_id = int(args["student_id"])
    course = Course.query.get(course_id)
    if not course:
        return _deny("Curso no encontrado")
    if (
        not is_insecure_mode()
        and course.term
        and course.term.grades_closed
        and "ADMIN" not in user.get_role_codes()
    ):
        return _deny("Notas cerradas para este periodo")
    owned = _owned_courses(user)
    if owned is not None and course_id not in owned:
        return _deny("No puede editar notas de este curso")
    grade = Grade.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not grade:
        grade = Grade(student_id=student_id, course_id=course_id)
        db.session.add(grade)
    try:
        apply_grade_rules(
            grade,
            partial1=args.get("partial1", grade.partial1),
            partial2=args.get("partial2", grade.partial2),
            supplementary=args.get("supplementary"),
        )
    except ValueError as exc:
        return _deny(str(exc))
    grade.updated_by = user.id
    db.session.commit()
    log_event(user.id, "AI_TOOL_UPSERT", "grades", f"student={student_id} course={course_id}")
    return _ok(grade.to_dict())


def attendance_upsert(user, args):
    if not _perm_ok(user, "attendance.manage"):
        return _deny("Sin permiso attendance.manage", "attendance.manage")
    course_id = int(args["course_id"])
    student_id = int(args["student_id"])
    status = args.get("status")
    if status not in ("presente", "ausente", "tardanza", "justificada"):
        return _deny("Estado inválido")
    owned = _owned_courses(user)
    if owned is not None and course_id not in owned:
        return _deny("No puede registrar asistencia en este curso")
    session_date = datetime.strptime(args["session_date"], "%Y-%m-%d").date()
    record = Attendance.query.filter_by(
        student_id=student_id, course_id=course_id, session_date=session_date
    ).first()
    if record:
        record.status = status
        record.notes = args.get("notes")
    else:
        record = Attendance(
            student_id=student_id,
            course_id=course_id,
            session_date=session_date,
            status=status,
            notes=args.get("notes"),
            recorded_by=user.id,
        )
        db.session.add(record)
    db.session.commit()
    log_event(user.id, "AI_TOOL_UPSERT", "attendance", f"student={student_id} course={course_id}")
    return _ok(record.to_dict())


def users_assign_roles(user, args):
    if not _perm_ok(user, "users.edit"):
        return _deny("Sin permiso users.edit", "users.edit")
    target = User.query.get(int(args["user_id"]))
    if not target:
        return _deny("Usuario no encontrado")
    if (
        not is_insecure_mode()
        and target.is_protected
        and "ADMIN" not in user.get_role_codes()
    ):
        return _deny("Usuario protegido")
    codes = args.get("role_codes") or []
    roles = Role.query.filter(Role.code.in_(codes)).all()
    if len(roles) != len(codes):
        return _deny("Uno o más roles no existen")
    target.roles = roles
    db.session.commit()
    log_event(user.id, "AI_ROLE_ASSIGN", "users", f"user={target.id} roles={codes}")
    return _ok(target.to_dict(include_perms=True))


def privileges_request_elevation(user, args):
    perms = args.get("permissions") or []
    if not perms:
        return _deny("Indique permisos solicitados")
    req = ElevationRequest(
        user_id=user.id,
        requested_permissions=perms,
        reason=args.get("reason", ""),
        status="pending",
    )
    db.session.add(req)
    db.session.add(
        Notification(
            role_code="ADMIN",
            title="Solicitud de elevación de privilegios",
            message=f"{user.full_name} solicita: {', '.join(perms)}. Motivo: {args.get('reason', 'N/A')}",
            created_by=user.id,
        )
    )
    db.session.commit()
    log_event(user.id, "ELEVATION_REQUEST", "privileges", f"id={req.id}")
    return _ok(req.to_dict(), message="Solicitud enviada a administradores")


def reports_generate(user, args, conversation_id=None):
    report_type = args.get("report_type")
    fmt = args.get("format", "xlsx")
    filters = args.get("filters") or {}
    try:
        artifact, _mime = generate_report_artifact(user, report_type, fmt, filters, conversation_id)
    except PermissionError as exc:
        return _deny(str(exc))
    except ValueError as exc:
        return _deny(str(exc))
    log_event(user.id, "AI_REPORT", "reports", f"{report_type}.{fmt} id={artifact.id}")
    return _ok(artifact.to_dict(), artifact=artifact.to_dict())


HANDLERS = {
    # perm None: chequeo propio (dashboard.view|reports.view|users.view) — SPEC-030
    "system_stats": (system_stats, None, False),
    "careers_list": (careers_list, "careers.view", False),
    "careers_get": (careers_get, "careers.view", False),
    "careers_create": (careers_create, "careers.create", True),
    "careers_update": (careers_update, "careers.edit", True),
    "subjects_list": (subjects_list, "subjects.view", False),
    "terms_list": (terms_list, "terms.view", False),
    "courses_list": (courses_list, "courses.view", False),
    "students_list": (students_list, "students.view", False),
    "teachers_list": (teachers_list, "teachers.view", False),
    "enrollments_list": (enrollments_list, "enrollments.view", False),
    "enrollments_create": (enrollments_create, "enrollments.create", True),
    "grades_list": (grades_list, "grades.view", False),
    "grades_upsert": (grades_upsert, "grades.manage", True),
    "attendance_list": (attendance_list, "attendance.view", False),
    "attendance_upsert": (attendance_upsert, "attendance.manage", True),
    "users_list": (users_list, "users.view", False),
    "roles_list": (roles_list, "roles.view", False),
    "users_assign_roles": (users_assign_roles, "users.edit", True),
    "audit_logs_list": (audit_logs_list, "audit.view", False),
    "reports_list_types": (reports_list_types, "reports.view", False),
    "reports_generate": (reports_generate, None, False),
}
