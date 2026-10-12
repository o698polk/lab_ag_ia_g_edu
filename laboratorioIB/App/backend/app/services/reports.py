"""Generación de reportes Excel/PDF con filtros."""

from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import or_

from app.models import (
    Attendance,
    AuditLog,
    Career,
    Course,
    Enrollment,
    Grade,
    Notification,
    Role,
    Schedule,
    Student,
    Subject,
    Teacher,
    Term,
    User,
)
from app.services.visibility import apply_course_scope, owned_course_ids, visible_term_ids


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _get(args, key, cast=None, default=None):
    """Compatible con Flask request.args y dict plano."""
    if isinstance(args, dict):
        val = args.get(key, default)
    else:
        try:
            return args.get(key, default, type=cast) if cast is not None else args.get(key, default)
        except TypeError:
            val = args.get(key, default)
    if val is None or val == "":
        return default
    if cast:
        try:
            return cast(val)
        except (TypeError, ValueError):
            return default
    return val


def _args(args):
    return {
        "career_id": _get(args, "career_id", int),
        "term_id": _get(args, "term_id", int),
        "course_id": _get(args, "course_id", int),
        "status": str(_get(args, "status", default="") or "").strip(),
        "role": str(_get(args, "role", default="") or "").strip(),
        "q": str(_get(args, "q", default="") or "").strip(),
        "date_from": _parse_date(_get(args, "from") or _get(args, "date_from")),
        "date_to": _parse_date(_get(args, "to") or _get(args, "date_to")),
    }


def _course_scope(query, user, f):
    course_ids = owned_course_ids(user)
    if course_ids is not None:
        query = query.filter(Course.id.in_(course_ids or [-1]))
    else:
        term_ids = visible_term_ids(user)
        if term_ids is not None:
            query = query.filter(Course.term_id.in_(term_ids or [-1]))
    if f["term_id"]:
        query = query.filter(Course.term_id == f["term_id"])
    if f["career_id"]:
        query = query.filter(Course.career_id == f["career_id"])
    if f["course_id"]:
        query = query.filter(Course.id == f["course_id"])
    return query


def filter_grades(user, args):
    f = _args(args)
    q = Grade.query.join(Course).join(Student)
    q = _course_scope(q, user, f)
    if f["status"]:
        q = q.filter(Grade.status == f["status"])
    if "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Grade.student_id == user.student.id)
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.join(User, Student.user_id == User.id).filter(
            or_(
                Student.student_code.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                Course.name.ilike(like),
                Course.code.ilike(like),
            )
        )
    return q.order_by(Grade.id.desc()).all()


def filter_attendance(user, args):
    f = _args(args)
    q = Attendance.query.join(Course).join(Student)
    q = _course_scope(q, user, f)
    if f["date_from"]:
        q = q.filter(Attendance.session_date >= f["date_from"])
    if f["date_to"]:
        q = q.filter(Attendance.session_date <= f["date_to"])
    if f["status"]:
        q = q.filter(Attendance.status == f["status"])
    if "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Attendance.student_id == user.student.id)
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.join(User, Student.user_id == User.id).filter(
            or_(Student.student_code.ilike(like), User.first_name.ilike(like), Course.name.ilike(like))
        )
    return q.order_by(Attendance.session_date.desc()).all()


def filter_enrollments(user, args):
    f = _args(args)
    q = Enrollment.query.join(Course).join(Student)
    q = _course_scope(q, user, f)
    if f["status"]:
        q = q.filter(Enrollment.status == f["status"])
    if "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Enrollment.student_id == user.student.id)
    if f["date_from"]:
        q = q.filter(Enrollment.enrolled_at >= datetime.combine(f["date_from"], datetime.min.time()))
    if f["date_to"]:
        q = q.filter(Enrollment.enrolled_at <= datetime.combine(f["date_to"], datetime.max.time()))
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.join(User, Student.user_id == User.id).filter(
            or_(Student.student_code.ilike(like), User.first_name.ilike(like), Course.name.ilike(like))
        )
    return q.order_by(Enrollment.id.desc()).all()


def filter_students(user, args):
    """SPEC-030: mismo scope que students_list (cursos propios si aplica)."""
    f = _args(args)
    course_ids = owned_course_ids(user)
    if course_ids is not None:
        if not course_ids:
            return []
        ids = {
            e.student_id
            for e in Enrollment.query.filter(
                Enrollment.course_id.in_(course_ids),
                Enrollment.status == "activa",
            ).all()
        }
        if not ids:
            return []
        q = Student.query.filter(Student.id.in_(ids))
    else:
        q = Student.query
    if f["career_id"]:
        q = q.filter(Student.career_id == f["career_id"])
    if f["status"]:
        q = q.filter(Student.status == f["status"])
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.join(User, Student.user_id == User.id).filter(
            or_(
                Student.student_code.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            )
        )
    return q.order_by(Student.id.desc()).all()


def excel_sheet_title(title: str, *, max_len: int = 31) -> str:
    """
    SPEC-032: nombre de hoja válido para Excel/openpyxl.
    Prohibidos: \\ / ? * [ ] ; máx. 31 caracteres.
    """
    import re

    raw = str(title or "").strip() or "Reporte"
    cleaned = re.sub(r'[\\/?*\[\]:]+', " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" '")
    if not cleaned:
        cleaned = "Reporte"
    return cleaned[:max_len]


def workbook_from_rows(title, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = excel_sheet_title(title)
    ws.append(headers)
    for row in rows:
        ws.append(list(row))
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _pdf_safe(text, max_len=40):
    """ReportLab Helvetica: evitar Unicode no Latin-1 (SPEC-025)."""
    s = str(text if text is not None else "")
    try:
        s.encode("latin-1")
    except UnicodeEncodeError:
        s = s.encode("latin-1", "replace").decode("latin-1")
    return s[:max_len]


def pdf_from_rows(title, headers, rows, col_widths=None):
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=letter)
    page_w, height = letter
    usable = page_w - 80  # márgenes 40+40
    n = max(len(headers), 1)
    if col_widths and len(col_widths) >= n:
        widths = list(col_widths[:n])
    else:
        widths = [max(36, int(usable / n))] * n
    total_w = sum(widths) or 1
    if total_w > usable:
        scale = usable / total_w
        widths = [max(28, int(w * scale)) for w in widths]

    y = height - 50
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, _pdf_safe(title, 80))
    y -= 16
    pdf.setFont("Helvetica", 8)
    pdf.drawString(
        40,
        y,
        _pdf_safe(
            f"Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC | Registros: {len(rows)}",
            90,
        ),
    )
    y -= 20
    pdf.setFont("Helvetica-Bold", 7)
    x = 40
    for i, h in enumerate(headers):
        pdf.drawString(x, y, _pdf_safe(h, 22))
        x += widths[i] if i < len(widths) else 40
    y -= 11
    pdf.setFont("Helvetica", 7)
    for row in rows:
        if y < 40:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 7)
        x = 40
        for i, cell in enumerate(row):
            pdf.drawString(x, y, _pdf_safe(cell, 22))
            x += widths[i] if i < len(widths) else 40
        y -= 10
    pdf.save()
    buf.seek(0)
    return buf


def grades_rows(items):
    headers = ["Estudiante", "Código", "Curso", "Periodo", "P1", "P2", "Sup.", "Final", "Estado"]
    rows = []
    for g in items:
        rows.append(
            [
                g.student.user.full_name if g.student and g.student.user else "",
                g.student.student_code if g.student else "",
                g.course.name if g.course else "",
                g.course.term.name if g.course and g.course.term else "",
                g.partial1,
                g.partial2,
                g.supplementary,
                g.final_grade,
                g.status,
            ]
        )
    return headers, rows


def attendance_rows(items):
    headers = ["Estudiante", "Curso", "Fecha", "Estado", "Notas"]
    rows = [
        [
            a.student.user.full_name if a.student and a.student.user else "",
            a.course.name if a.course else "",
            a.session_date.isoformat() if a.session_date else "",
            a.status,
            a.notes or "",
        ]
        for a in items
    ]
    return headers, rows


def enrollments_rows(items):
    headers = ["ID", "Estudiante", "Curso", "Periodo", "Estado", "Fecha"]
    rows = [
        [
            e.id,
            e.student.user.full_name if e.student and e.student.user else "",
            e.course.name if e.course else "",
            e.course.term.name if e.course and e.course.term else "",
            e.status,
            e.enrolled_at.strftime("%Y-%m-%d") if e.enrolled_at else "",
        ]
        for e in items
    ]
    return headers, rows


def students_rows(items):
    headers = ["Código", "Nombre", "Email", "Carrera", "Teléfono", "Estado"]
    rows = [
        [
            s.student_code,
            s.user.full_name if s.user else "",
            s.user.email if s.user else "",
            s.career.name if s.career else "",
            s.phone or "",
            s.status,
        ]
        for s in items
    ]
    return headers, rows


# ─── SPEC-019: módulos adicionales ─────────────────────────
def filter_users(user, args):
    f = _args(args)
    q = User.query
    if f["role"]:
        q = q.join(User.roles).filter(Role.code == f["role"])
    if f["status"]:
        st = f["status"].lower()
        if st in ("activo", "active", "true", "1"):
            q = q.filter(User.is_active.is_(True))
        elif st in ("inactivo", "inactive", "false", "0"):
            q = q.filter(User.is_active.is_(False))
    if f["date_from"]:
        q = q.filter(User.created_at >= datetime.combine(f["date_from"], datetime.min.time()))
    if f["date_to"]:
        q = q.filter(User.created_at <= datetime.combine(f["date_to"], datetime.max.time()))
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(
            or_(
                User.username.ilike(like),
                User.email.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
            )
        )
    return q.order_by(User.id.desc()).distinct().all()


def users_rows(items):
    headers = ["ID", "Usuario", "Nombre", "Email", "Roles", "Estado", "Creado"]
    rows = []
    for u in items:
        rows.append(
            [
                u.id,
                u.username,
                u.full_name,
                u.email,
                ", ".join(u.get_role_codes()),
                "Activo" if u.is_active else "Inactivo",
                u.created_at.strftime("%Y-%m-%d") if u.created_at else "",
            ]
        )
    return headers, rows


def filter_teachers(user, args):
    f = _args(args)
    q = Teacher.query
    if f["status"]:
        q = q.filter(Teacher.status == f["status"])
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.join(User, Teacher.user_id == User.id).filter(
            or_(
                Teacher.teacher_code.ilike(like),
                Teacher.specialty.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            )
        )
    return q.order_by(Teacher.id.desc()).all()


def teachers_rows(items):
    headers = ["Código", "Nombre", "Email", "Especialidad", "Título", "Estado"]
    rows = [
        [
            t.teacher_code,
            t.user.full_name if t.user else "",
            t.user.email if t.user else "",
            t.specialty or "",
            t.title or "",
            t.status,
        ]
        for t in items
    ]
    return headers, rows


def filter_careers(user, args):
    f = _args(args)
    q = Career.query
    if f["status"]:
        st = f["status"].lower()
        if st in ("activa", "activo", "active", "true", "1", "sí", "si"):
            q = q.filter(Career.is_active.is_(True))
        elif st in ("inactiva", "inactivo", "inactive", "false", "0", "no"):
            q = q.filter(Career.is_active.is_(False))
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(or_(Career.code.ilike(like), Career.name.ilike(like)))
    return q.order_by(Career.name).all()


def careers_rows(items):
    headers = ["Código", "Nombre", "Semestres", "Activa"]
    rows = [[c.code, c.name, c.duration_semesters, "Sí" if c.is_active else "No"] for c in items]
    return headers, rows


def filter_subjects(user, args):
    """SPEC-031: si el usuario tiene cursos propios, solo materias de esos cursos."""
    f = _args(args)
    q = Subject.query
    course_ids = owned_course_ids(user)
    if course_ids is not None:
        if not course_ids:
            return []
        subject_ids = {
            c.subject_id
            for c in Course.query.filter(Course.id.in_(course_ids)).all()
            if c.subject_id
        }
        if not subject_ids:
            return []
        q = q.filter(Subject.id.in_(subject_ids))
    if f["career_id"]:
        q = q.filter(Subject.career_id == f["career_id"])
    if f["status"]:
        st = f["status"].lower()
        if st in ("activa", "activo", "active", "true", "1"):
            q = q.filter(Subject.is_active.is_(True))
        elif st in ("inactiva", "inactivo", "inactive", "false", "0"):
            q = q.filter(Subject.is_active.is_(False))
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(or_(Subject.code.ilike(like), Subject.name.ilike(like)))
    return q.order_by(Subject.name).all()


def subjects_rows(items):
    headers = ["Código", "Nombre", "Créditos", "Carrera", "Activa"]
    rows = [
        [
            s.code,
            s.name,
            s.credits,
            s.career.name if s.career else "",
            "Sí" if s.is_active else "No",
        ]
        for s in items
    ]
    return headers, rows


def filter_terms(user, args):
    f = _args(args)
    q = Term.query
    term_ids = visible_term_ids(user)
    if term_ids is not None:
        q = q.filter(Term.id.in_(term_ids or [-1]))
    if f["status"]:
        st = f["status"].lower()
        if st in ("habilitado", "activo", "active", "true", "1"):
            q = q.filter(Term.is_active.is_(True))
        elif st in ("oculto", "inactivo", "inactive", "false", "0"):
            q = q.filter(Term.is_active.is_(False))
    if f["date_from"]:
        q = q.filter(Term.start_date >= f["date_from"])
    if f["date_to"]:
        q = q.filter(Term.start_date <= f["date_to"])
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(or_(Term.code.ilike(like), Term.name.ilike(like)))
    return q.order_by(Term.start_date.desc()).all()


def terms_rows(items):
    headers = ["Código", "Nombre", "Inicio", "Fin", "Habilitado", "Notas cerradas"]
    rows = [
        [
            t.code,
            t.name,
            t.start_date.isoformat() if t.start_date else "",
            t.end_date.isoformat() if t.end_date else "",
            "Sí" if t.is_active else "No",
            "Sí" if t.grades_closed else "No",
        ]
        for t in items
    ]
    return headers, rows


def filter_courses(user, args):
    f = _args(args)
    q = apply_course_scope(Course.query, user)
    if f["term_id"]:
        q = q.filter(Course.term_id == f["term_id"])
    if f["career_id"]:
        q = q.filter(Course.career_id == f["career_id"])
    if f["course_id"]:
        q = q.filter(Course.id == f["course_id"])
    if f["status"]:
        st = f["status"].lower()
        if st in ("activo", "active", "true", "1"):
            q = q.filter(Course.is_active.is_(True))
        elif st in ("inactivo", "inactive", "false", "0"):
            q = q.filter(Course.is_active.is_(False))
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(or_(Course.code.ilike(like), Course.name.ilike(like)))
    return q.order_by(Course.name).all()


def courses_rows(items):
    headers = ["Código", "Nombre", "Materia", "Periodo", "Paralelo", "Cupo", "Activo"]
    rows = [
        [
            c.code,
            c.name,
            c.subject.name if c.subject else "",
            c.term.name if c.term else "",
            c.parallel,
            c.capacity,
            "Sí" if c.is_active else "No",
        ]
        for c in items
    ]
    return headers, rows


def filter_schedules(user, args):
    f = _args(args)
    q = apply_course_scope(Schedule.query.join(Course), user)
    if f["term_id"]:
        q = q.filter(Course.term_id == f["term_id"])
    if f["course_id"]:
        q = q.filter(Schedule.course_id == f["course_id"])
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(or_(Course.code.ilike(like), Course.name.ilike(like), Schedule.classroom.ilike(like)))
    return q.order_by(Schedule.id.desc()).all()


def schedules_rows(items):
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    headers = ["Curso", "Periodo", "Paralelo", "Día", "Inicio", "Fin", "Aula"]
    rows = []
    for s in items:
        course = s.course
        rows.append(
            [
                course.code if course else "",
                course.term.name if course and course.term else "",
                course.parallel if course else "",
                days[s.day_of_week] if s.day_of_week is not None and 0 <= s.day_of_week < 7 else s.day_of_week,
                s.start_time,
                s.end_time,
                s.classroom or "",
            ]
        )
    return headers, rows


def filter_notifications(user, args):
    f = _args(args)
    q = Notification.query
    # Usuarios normales solo ven las suyas / rol; admin ve todas si tiene permiso
    roles = user.get_role_codes()
    if "ADMIN" not in roles and "IT_SUPPORT" not in roles:
        q = q.filter(or_(Notification.user_id == user.id, Notification.role_code.in_(roles or ["__none__"])))
    if f["status"]:
        st = f["status"].lower()
        if st in ("leida", "leída", "true", "1", "sí", "si"):
            q = q.filter(Notification.is_read.is_(True))
        elif st in ("no_leida", "no_leída", "false", "0", "no"):
            q = q.filter(Notification.is_read.is_(False))
    if f["date_from"]:
        q = q.filter(Notification.created_at >= datetime.combine(f["date_from"], datetime.min.time()))
    if f["date_to"]:
        q = q.filter(Notification.created_at <= datetime.combine(f["date_to"], datetime.max.time()))
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(or_(Notification.title.ilike(like), Notification.message.ilike(like)))
    return q.order_by(Notification.created_at.desc()).limit(500).all()


def notifications_rows(items):
    headers = ["Título", "Mensaje", "Rol", "Leída", "Fecha"]
    rows = [
        [
            n.title,
            (n.message or "")[:120],
            n.role_code or "",
            "Sí" if n.is_read else "No",
            n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else "",
        ]
        for n in items
    ]
    return headers, rows


def filter_audit(user, args):
    f = _args(args)
    q = AuditLog.query
    if f["status"]:
        # reutilizamos status como módulo
        q = q.filter(AuditLog.module == f["status"])
    if f["date_from"]:
        q = q.filter(AuditLog.created_at >= datetime.combine(f["date_from"], datetime.min.time()))
    if f["date_to"]:
        q = q.filter(AuditLog.created_at <= datetime.combine(f["date_to"], datetime.max.time()))
    if f["q"]:
        like = f"%{f['q']}%"
        q = q.filter(
            or_(
                AuditLog.action.ilike(like),
                AuditLog.module.ilike(like),
                AuditLog.details.ilike(like),
                AuditLog.ip_address.ilike(like),
            )
        )
    return q.order_by(AuditLog.created_at.desc()).limit(1000).all()


def audit_rows(items):
    headers = ["Fecha", "Usuario", "Módulo", "Acción", "Detalle", "IP"]
    rows = [
        [
            a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
            a.user_id,
            a.module,
            a.action,
            (a.details or "")[:100],
            a.ip_address or "",
        ]
        for a in items
    ]
    return headers, rows


# Catálogo para rutas genéricas (SPEC-019)
REPORT_CATALOG = {
    "grades": {
        "filter": filter_grades,
        "rows": grades_rows,
        "title": "Notas",
        "filename": "reporte_notas",
        "perms": ("reports.export", "grades.view"),
        "widths": [85, 45, 95, 55, 30, 30, 30, 35, 45],
    },
    "attendance": {
        "filter": filter_attendance,
        "rows": attendance_rows,
        "title": "Asistencia",
        "filename": "reporte_asistencia",
        "perms": ("reports.export", "attendance.view"),
        "widths": [120, 120, 70, 60, 120],
    },
    "enrollments": {
        "filter": filter_enrollments,
        "rows": enrollments_rows,
        "title": "Matrículas",
        "filename": "reporte_matriculas",
        "perms": ("reports.export", "enrollments.view"),
        "widths": [35, 110, 120, 70, 55, 60],
    },
    "students": {
        "filter": filter_students,
        "rows": students_rows,
        "title": "Estudiantes",
        "filename": "reporte_estudiantes",
        "perms": ("reports.export", "students.view"),
        "widths": [55, 110, 120, 100, 60, 45],
    },
    "users": {
        "filter": filter_users,
        "rows": users_rows,
        "title": "Usuarios",
        "filename": "reporte_usuarios",
        "perms": ("reports.export", "users.view"),
        "widths": [30, 70, 110, 120, 100, 50, 60],
    },
    "teachers": {
        "filter": filter_teachers,
        "rows": teachers_rows,
        "title": "Docentes",
        "filename": "reporte_docentes",
        "perms": ("reports.export", "teachers.view"),
        "widths": [55, 110, 120, 100, 80, 50],
    },
    "careers": {
        "filter": filter_careers,
        "rows": careers_rows,
        "title": "Carreras",
        "filename": "reporte_carreras",
        "perms": ("reports.export", "careers.view"),
        "widths": [60, 180, 60, 50],
    },
    "subjects": {
        "filter": filter_subjects,
        "rows": subjects_rows,
        "title": "Materias",
        "filename": "reporte_materias",
        "perms": ("reports.export", "subjects.view"),
        "widths": [60, 150, 50, 120, 50],
    },
    "terms": {
        "filter": filter_terms,
        "rows": terms_rows,
        "title": "Periodos",
        "filename": "reporte_periodos",
        "perms": ("reports.export", "terms.view"),
        "widths": [60, 120, 70, 70, 55, 55],
    },
    "courses": {
        "filter": filter_courses,
        "rows": courses_rows,
        "title": "Cursos",
        "filename": "reporte_cursos",
        "perms": ("reports.export", "courses.view"),
        "widths": [70, 120, 100, 80, 45, 40, 40],
    },
    "schedules": {
        "filter": filter_schedules,
        "rows": schedules_rows,
        "title": "Horarios",
        "filename": "reporte_horarios",
        "perms": ("reports.export", "schedules.view"),
        "widths": [70, 80, 50, 60, 50, 50, 60],
    },
    "notifications": {
        "filter": filter_notifications,
        "rows": notifications_rows,
        "title": "Notificaciones",
        "filename": "reporte_notificaciones",
        "perms": ("reports.export", "notifications.view"),
        "widths": [100, 180, 50, 40, 80],
    },
    "audit": {
        "filter": filter_audit,
        "rows": audit_rows,
        "title": "Auditoría",
        "filename": "reporte_auditoria",
        "perms": ("reports.export", "audit.view"),
        "widths": [80, 40, 60, 80, 150, 70],
    },
}


def build_report(report_type: str, user, args):
    cfg = REPORT_CATALOG.get(report_type)
    if not cfg:
        raise ValueError(f"Tipo de reporte desconocido: {report_type}")
    items = cfg["filter"](user, args)
    headers, rows = cfg["rows"](items)
    return cfg, headers, rows
