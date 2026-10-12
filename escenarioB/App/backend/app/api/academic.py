from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import (
    Assignment,
    Attendance,
    Career,
    Course,
    Curriculum,
    Enrollment,
    Grade,
    Schedule,
    Student,
    Subject,
    Teacher,
    Term,
    User,
)
from app.permissions.decorators import get_current_user, permission_required
from app.services.attendance import is_critical_absence
from app.services.audit import log_event
from app.services.enrollment import MAX_COURSE_CAPACITY, count_active_enrollments, validate_course_capacity
from app.services.grades import apply_grade_rules
from app.services.visibility import apply_course_scope, filter_courses_query, owned_course_ids, visible_term_ids

academic_bp = Blueprint("academic", __name__, url_prefix="/api/v1")


# ─── Careers ───────────────────────────────────────────────
@academic_bp.get("/careers")
@jwt_required()
@permission_required("careers.view")
def list_careers():
    return jsonify([c.to_dict() for c in Career.query.order_by(Career.name).all()])


@academic_bp.post("/careers")
@jwt_required()
@permission_required("careers.create")
def create_career():
    data = request.get_json(silent=True) or {}
    c = Career(
        code=data["code"],
        name=data["name"],
        description=data.get("description"),
        duration_semesters=data.get("duration_semesters", 8),
        is_active=data.get("is_active", True),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@academic_bp.put("/careers/<int:cid>")
@jwt_required()
@permission_required("careers.edit")
def update_career(cid):
    c = Career.query.get_or_404(cid)
    data = request.get_json(silent=True) or {}
    for f in ("code", "name", "description", "duration_semesters", "is_active"):
        if f in data:
            setattr(c, f, data[f])
    db.session.commit()
    return jsonify(c.to_dict())


@academic_bp.delete("/careers/<int:cid>")
@jwt_required()
@permission_required("careers.edit")
def delete_career(cid):
    c = Career.query.get_or_404(cid)
    if Student.query.filter_by(career_id=cid).first() or Course.query.filter_by(career_id=cid).first():
        return jsonify({"error": "No se puede eliminar: tiene estudiantes o cursos asociados"}), 400
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Carrera eliminada"})


# ─── Subjects ──────────────────────────────────────────────
@academic_bp.get("/subjects")
@jwt_required()
@permission_required("subjects.view")
def list_subjects():
    """SPEC-012: incluye docentes asignados a cursos visibles de cada materia."""
    user = get_current_user()
    course_ids = owned_course_ids(user)
    cq = Course.query
    if course_ids is not None:
        cq = cq.filter(Course.id.in_(course_ids or [-1]))
    else:
        term_ids = visible_term_ids(user)
        if term_ids is not None:
            cq = cq.filter(Course.term_id.in_(term_ids or [-1]))

    scoped_courses = cq.all()
    subject_ids = {c.subject_id for c in scoped_courses if c.subject_id}
    q = Subject.query
    if course_ids is not None or visible_term_ids(user) is not None:
        q = q.filter(Subject.id.in_(subject_ids or {-1}))

    teachers_by_subject: dict[int, set[str]] = {}
    if scoped_courses:
        cids = [c.id for c in scoped_courses]
        assignments = Assignment.query.filter(Assignment.course_id.in_(cids)).all()
        course_subject = {c.id: c.subject_id for c in scoped_courses}
        for a in assignments:
            sid = course_subject.get(a.course_id)
            if not sid:
                continue
            name = None
            if a.teacher and a.teacher.user:
                name = a.teacher.user.full_name
            if name:
                teachers_by_subject.setdefault(sid, set()).add(name)

    result = []
    for s in q.order_by(Subject.name).all():
        d = s.to_dict()
        names = sorted(teachers_by_subject.get(s.id, []))
        d["teachers"] = names
        d["teachers_label"] = ", ".join(names) if names else "Sin docente asignado"
        result.append(d)
    return jsonify(result)


@academic_bp.post("/subjects")
@jwt_required()
@permission_required("subjects.create")
def create_subject():
    data = request.get_json(silent=True) or {}
    s = Subject(
        code=data["code"],
        name=data["name"],
        credits=data.get("credits", 3),
        career_id=data.get("career_id"),
        description=data.get("description"),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@academic_bp.put("/subjects/<int:sid>")
@jwt_required()
@permission_required("subjects.edit")
def update_subject(sid):
    s = Subject.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}
    for f in ("code", "name", "credits", "career_id", "description", "is_active"):
        if f in data:
            setattr(s, f, data[f])
    db.session.commit()
    return jsonify(s.to_dict())


@academic_bp.delete("/subjects/<int:sid>")
@jwt_required()
@permission_required("subjects.edit")
def delete_subject(sid):
    s = Subject.query.get_or_404(sid)
    if Course.query.filter_by(subject_id=sid).first():
        return jsonify({"error": "No se puede eliminar: tiene cursos asociados"}), 400
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Materia eliminada"})


# ─── Terms ─────────────────────────────────────────────────
@academic_bp.get("/terms")
@jwt_required()
@permission_required("terms.view")
def list_terms():
    """Admin ve todos; estudiante/docente solo periodos habilitados (is_active)."""
    user = get_current_user()
    term_ids = visible_term_ids(user)
    q = Term.query
    if term_ids is not None:
        q = q.filter(Term.id.in_(term_ids or [-1]))
    return jsonify([t.to_dict() for t in q.order_by(Term.start_date.desc()).all()])


@academic_bp.post("/terms")
@jwt_required()
@permission_required("terms.create")
def create_term():
    data = request.get_json(silent=True) or {}
    # Múltiples periodos pueden estar habilitados a la vez (admin)
    t = Term(
        code=data["code"],
        name=data["name"],
        start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
        end_date=datetime.strptime(data["end_date"], "%Y-%m-%d").date(),
        is_active=bool(data.get("is_active", False)),
    )
    db.session.add(t)
    db.session.commit()
    log_event(get_current_user().id, "TERM_CREATE", "terms", t.code)
    return jsonify(t.to_dict()), 201


@academic_bp.put("/terms/<int:tid>")
@jwt_required()
@permission_required("terms.edit")
def update_term(tid):
    t = Term.query.get_or_404(tid)
    data = request.get_json(silent=True) or {}
    for f in ("code", "name", "is_active", "grades_closed"):
        if f in data:
            setattr(t, f, data[f])
    if "start_date" in data:
        t.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
    if "end_date" in data:
        t.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    db.session.commit()
    log_event(get_current_user().id, "TERM_UPDATE", "terms", f"{t.code} active={t.is_active}")
    return jsonify(t.to_dict())


@academic_bp.delete("/terms/<int:tid>")
@jwt_required()
@permission_required("terms.edit")
def delete_term(tid):
    t = Term.query.get_or_404(tid)
    if Course.query.filter_by(term_id=tid).first():
        return jsonify({"error": "No se puede eliminar: tiene cursos asociados"}), 400
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "Periodo eliminado"})


# ─── Curriculum ────────────────────────────────────────────
@academic_bp.get("/curriculum")
@jwt_required()
@permission_required("curriculum.view")
def list_curriculum():
    career_id = request.args.get("career_id", type=int)
    q = Curriculum.query
    if career_id:
        q = q.filter_by(career_id=career_id)
    return jsonify([c.to_dict() for c in q.order_by(Curriculum.level).all()])


@academic_bp.post("/curriculum")
@jwt_required()
@permission_required("curriculum.manage")
def create_curriculum():
    data = request.get_json(silent=True) or {}
    item = Curriculum(
        career_id=data["career_id"],
        subject_id=data["subject_id"],
        level=data["level"],
        prerequisite_subject_id=data.get("prerequisite_subject_id"),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


# ─── Courses ───────────────────────────────────────────────
@academic_bp.get("/courses")
@jwt_required()
@permission_required("courses.view")
def list_courses():
    user = get_current_user()
    q = filter_courses_query(Course.query, user)
    return jsonify([c.to_dict() for c in q.order_by(Course.name).all()])


@academic_bp.post("/courses")
@jwt_required()
@permission_required("courses.create")
def create_course():
    data = request.get_json(silent=True) or {}
    try:
        capacity = int(data.get("capacity", 40))
    except (TypeError, ValueError):
        return jsonify({"error": "Cupo inválido"}), 400
    if capacity < 1 or capacity > MAX_COURSE_CAPACITY:
        return jsonify({"error": f"El cupo debe estar entre 1 y {MAX_COURSE_CAPACITY}"}), 400
    c = Course(
        code=data["code"],
        name=data["name"],
        subject_id=data["subject_id"],
        term_id=data["term_id"],
        career_id=data.get("career_id"),
        parallel=data.get("parallel", "A"),
        capacity=capacity,
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@academic_bp.put("/courses/<int:cid>")
@jwt_required()
@permission_required("courses.edit")
def update_course(cid):
    c = Course.query.get_or_404(cid)
    data = request.get_json(silent=True) or {}
    if "capacity" in data:
        try:
            capacity = int(data["capacity"])
        except (TypeError, ValueError):
            return jsonify({"error": "Cupo inválido"}), 400
        if capacity < 1 or capacity > MAX_COURSE_CAPACITY:
            return jsonify({"error": f"El cupo debe estar entre 1 y {MAX_COURSE_CAPACITY}"}), 400
        active = count_active_enrollments(c.id)
        if capacity < active:
            return jsonify(
                {"error": f"No puede reducir el cupo por debajo de las matrículas activas ({active})"}
            ), 400
        data = {**data, "capacity": capacity}
    for f in ("code", "name", "subject_id", "term_id", "career_id", "parallel", "capacity", "is_active"):
        if f in data:
            setattr(c, f, data[f])
    db.session.commit()
    return jsonify(c.to_dict())


@academic_bp.delete("/courses/<int:cid>")
@jwt_required()
@permission_required("courses.edit")
def delete_course(cid):
    c = Course.query.get_or_404(cid)
    Grade.query.filter_by(course_id=cid).delete()
    Attendance.query.filter_by(course_id=cid).delete()
    Enrollment.query.filter_by(course_id=cid).delete()
    Schedule.query.filter_by(course_id=cid).delete()
    Assignment.query.filter_by(course_id=cid).delete()
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Curso eliminado"})


# ─── Assignments ───────────────────────────────────────────
@academic_bp.get("/assignments")
@jwt_required()
@permission_required("assignments.view")
def list_assignments():
    return jsonify([a.to_dict() for a in Assignment.query.all()])


@academic_bp.post("/assignments")
@jwt_required()
@permission_required("assignments.manage")
def create_assignment():
    data = request.get_json(silent=True) or {}
    a = Assignment(teacher_id=data["teacher_id"], course_id=data["course_id"])
    db.session.add(a)
    db.session.commit()
    return jsonify(a.to_dict()), 201


@academic_bp.delete("/assignments/<int:aid>")
@jwt_required()
@permission_required("assignments.manage")
def delete_assignment(aid):
    a = Assignment.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    return jsonify({"message": "Asignación eliminada"})


# ─── Enrollments ───────────────────────────────────────────
@academic_bp.get("/enrollments")
@jwt_required()
@permission_required("enrollments.view")
def list_enrollments():
    user = get_current_user()
    q = Enrollment.query.join(Course)
    q = apply_course_scope(q, user)
    if "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Enrollment.student_id == user.student.id)
    return jsonify([e.to_dict() for e in q.order_by(Enrollment.id.desc()).all()])


@academic_bp.post("/enrollments")
@jwt_required()
@permission_required("enrollments.create")
def create_enrollment():
    data = request.get_json(silent=True) or {}
    course = Course.query.get(data.get("course_id"))
    if not course:
        return jsonify({"error": "Curso no encontrado"}), 404
    exists = Enrollment.query.filter_by(
        student_id=data["student_id"], course_id=data["course_id"]
    ).first()
    if exists:
        return jsonify({"error": "Ya matriculado en este curso"}), 409
    if (data.get("status") or "activa") == "activa":
        err = validate_course_capacity(course)
        if err:
            return jsonify({"error": err}), 409
    e = Enrollment(
        student_id=data["student_id"],
        course_id=data["course_id"],
        status=data.get("status", "activa"),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify(e.to_dict()), 201


@academic_bp.put("/enrollments/<int:eid>")
@jwt_required()
@permission_required("enrollments.edit")
def update_enrollment(eid):
    e = Enrollment.query.get_or_404(eid)
    data = request.get_json(silent=True) or {}
    if "status" in data and data["status"] in ("activa", "retirada", "congelada"):
        e.status = data["status"]
    db.session.commit()
    return jsonify(e.to_dict())


@academic_bp.delete("/enrollments/<int:eid>")
@jwt_required()
@permission_required("enrollments.edit")
def delete_enrollment(eid):
    e = Enrollment.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    return jsonify({"message": "Matrícula eliminada"})


# ─── Schedules ─────────────────────────────────────────────
@academic_bp.get("/schedules")
@jwt_required()
@permission_required("schedules.view")
def list_schedules():
    user = get_current_user()
    course_id = request.args.get("course_id", type=int)
    q = Schedule.query.join(Course)
    q = apply_course_scope(q, user)
    if course_id:
        owned = owned_course_ids(user)
        if owned is not None and course_id not in owned:
            return jsonify([])
        q = q.filter(Schedule.course_id == course_id)
    return jsonify([s.to_dict() for s in q.order_by(Schedule.day_of_week, Schedule.start_time).all()])


@academic_bp.post("/schedules")
@jwt_required()
@permission_required("schedules.create")
def create_schedule():
    data = request.get_json(silent=True) or {}
    s = Schedule(
        course_id=data["course_id"],
        day_of_week=data["day_of_week"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        classroom=data.get("classroom"),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@academic_bp.put("/schedules/<int:sid>")
@jwt_required()
@permission_required("schedules.edit")
def update_schedule(sid):
    s = Schedule.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}
    for f in ("day_of_week", "start_time", "end_time", "classroom", "course_id"):
        if f in data:
            setattr(s, f, data[f])
    db.session.commit()
    return jsonify(s.to_dict())


@academic_bp.delete("/schedules/<int:sid>")
@jwt_required()
@permission_required("schedules.edit")
def delete_schedule(sid):
    s = Schedule.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({"message": "Horario eliminado"})


# ─── Grades ────────────────────────────────────────────────
def _teacher_owns_course(user: User, course_id: int) -> bool:
    if "ADMIN" in user.get_role_codes() or "COORDINATOR" in user.get_role_codes():
        return True
    if not user.teacher:
        return False
    return (
        Assignment.query.filter_by(teacher_id=user.teacher.id, course_id=course_id).first()
        is not None
    )


@academic_bp.get("/grades")
@jwt_required()
@permission_required("grades.view")
def list_grades():
    course_id = request.args.get("course_id", type=int)
    student_id = request.args.get("student_id", type=int)
    user = get_current_user()
    q = Grade.query.join(Course)
    q = apply_course_scope(q, user)
    if course_id:
        owned = owned_course_ids(user)
        if owned is not None and course_id not in owned:
            return jsonify([])
        q = q.filter(Grade.course_id == course_id)
    if "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Grade.student_id == user.student.id)
    elif student_id:
        q = q.filter(Grade.student_id == student_id)
    return jsonify([g.to_dict() for g in q.all()])


@academic_bp.post("/grades")
@jwt_required()
@permission_required("grades.manage")
def upsert_grade():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")
    student_id = data.get("student_id")
    if not course_id or not student_id:
        return jsonify({"error": "course_id y student_id requeridos"}), 400

    course = Course.query.get_or_404(course_id)
    if course.term and course.term.grades_closed and "ADMIN" not in user.get_role_codes():
        return jsonify({"error": "Notas cerradas para este periodo"}), 403

    if not _teacher_owns_course(user, course_id):
        return jsonify({"error": "Solo el docente asignado puede registrar notas"}), 403

    grade = Grade.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not grade:
        grade = Grade(student_id=student_id, course_id=course_id)
        db.session.add(grade)

    try:
        apply_grade_rules(
            grade,
            partial1=data.get("partial1", grade.partial1),
            partial2=data.get("partial2", grade.partial2),
            supplementary=data.get("supplementary"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    grade.updated_by = user.id
    db.session.commit()
    log_event(user.id, "GRADE_UPDATE", "grades", f"student={student_id} course={course_id}")
    return jsonify(grade.to_dict())


# ─── Attendance ────────────────────────────────────────────
@academic_bp.get("/attendance")
@jwt_required()
@permission_required("attendance.view")
def list_attendance():
    course_id = request.args.get("course_id", type=int)
    user = get_current_user()
    q = Attendance.query.join(Course)
    q = apply_course_scope(q, user)
    if course_id:
        owned = owned_course_ids(user)
        if owned is not None and course_id not in owned:
            return jsonify([])
        q = q.filter(Attendance.course_id == course_id)
    if "STUDENT" in user.get_role_codes() and user.student:
        q = q.filter(Attendance.student_id == user.student.id)
    return jsonify([a.to_dict() for a in q.order_by(Attendance.session_date.desc()).all()])


@academic_bp.get("/attendance/roster")
@jwt_required()
@permission_required("attendance.view")
def attendance_roster():
    """SPEC-015: lista matriculados del curso + estado de la fecha."""
    user = get_current_user()
    if "STUDENT" in user.get_role_codes() and "TEACHER" not in user.get_role_codes():
        if "ADMIN" not in user.get_role_codes():
            return jsonify({"error": "El estudiante no puede ver el roster de compañeros"}), 403

    course_id = request.args.get("course_id", type=int)
    session_date_raw = (request.args.get("session_date") or "").strip()
    if not course_id or not session_date_raw:
        return jsonify({"error": "course_id y session_date son obligatorios"}), 400
    try:
        session_date = datetime.strptime(session_date_raw, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "session_date inválida (YYYY-MM-DD)"}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Curso no encontrado"}), 404
    owned = owned_course_ids(user)
    if owned is not None and course_id not in owned:
        return jsonify({"error": "Sin acceso a este curso"}), 403

    enrollments = (
        Enrollment.query.filter_by(course_id=course_id, status="activa")
        .join(Student, Enrollment.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .order_by(User.last_name.asc(), User.first_name.asc())
        .all()
    )
    existing = {
        a.student_id: a
        for a in Attendance.query.filter_by(course_id=course_id, session_date=session_date).all()
    }
    students = []
    for e in enrollments:
        st = e.student
        att = existing.get(st.id)
        students.append(
            {
                "student_id": st.id,
                "student_code": st.student_code,
                "full_name": st.user.full_name if st.user else "",
                "attendance_id": att.id if att else None,
                "status": att.status if att else "presente",
                "notes": att.notes if att else None,
            }
        )
    return jsonify(
        {
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.code,
            "parallel": course.parallel,
            "capacity": course.capacity,
            "enrolled_count": len(students),
            "session_date": session_date.isoformat(),
            "students": students,
        }
    )


@academic_bp.post("/attendance/bulk")
@jwt_required()
@permission_required("attendance.manage")
def attendance_bulk():
    """SPEC-015: guardar asistencia de toda la sesión."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")
    session_date_raw = data.get("session_date")
    records = data.get("records") or []
    if not course_id or not session_date_raw:
        return jsonify({"error": "course_id y session_date son obligatorios"}), 400
    if not _teacher_owns_course(user, course_id) and "ADMIN" not in user.get_role_codes():
        return jsonify({"error": "Solo el docente del curso puede registrar asistencia"}), 403
    try:
        session_date = datetime.strptime(session_date_raw, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "session_date inválida (YYYY-MM-DD)"}), 400

    active_ids = {
        e.student_id
        for e in Enrollment.query.filter_by(course_id=course_id, status="activa").all()
    }
    # Permitir guardar el roster completo aunque el seed histórico exceda cupo 60
    if len(records) > max(MAX_COURSE_CAPACITY, len(active_ids), 1):
        return jsonify({"error": "Demasiados registros para esta sesión"}), 400
    saved = []
    for row in records:
        student_id = int(row.get("student_id"))
        status = row.get("status") or "presente"
        if student_id not in active_ids:
            return jsonify({"error": f"Estudiante {student_id} no está matriculado activo"}), 400
        if status not in ("presente", "ausente", "tardanza", "justificada"):
            return jsonify({"error": f"Estado inválido: {status}"}), 400
        record = Attendance.query.filter_by(
            student_id=student_id, course_id=course_id, session_date=session_date
        ).first()
        if record:
            record.status = status
            record.notes = row.get("notes")
        else:
            record = Attendance(
                student_id=student_id,
                course_id=course_id,
                session_date=session_date,
                status=status,
                notes=row.get("notes"),
                recorded_by=user.id,
            )
            db.session.add(record)
        db.session.flush()
        item = record.to_dict()
        item["critical_absence"] = is_critical_absence(student_id, course_id)
        saved.append(item)
    db.session.commit()
    log_event(user.id, "ATTENDANCE_BULK", "attendance", f"course={course_id} date={session_date} n={len(saved)}")
    return jsonify({"ok": True, "count": len(saved), "items": saved})


@academic_bp.post("/attendance")
@jwt_required()
@permission_required("attendance.manage")
def create_attendance():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")
    if not _teacher_owns_course(user, course_id):
        return jsonify({"error": "Solo el docente del curso puede registrar asistencia"}), 403

    status = data.get("status")
    if status not in ("presente", "ausente", "tardanza", "justificada"):
        return jsonify({"error": "Estado inválido"}), 400

    session_date = datetime.strptime(data["session_date"], "%Y-%m-%d").date()
    record = Attendance.query.filter_by(
        student_id=data["student_id"], course_id=course_id, session_date=session_date
    ).first()
    if record:
        record.status = status
        record.notes = data.get("notes")
    else:
        record = Attendance(
            student_id=data["student_id"],
            course_id=course_id,
            session_date=session_date,
            status=status,
            notes=data.get("notes"),
            recorded_by=user.id,
        )
        db.session.add(record)
    db.session.commit()

    critical = is_critical_absence(data["student_id"], course_id)
    result = record.to_dict()
    result["critical_absence"] = critical
    if critical:
        log_event(
            user.id,
            "ATTENDANCE_ALERT",
            "attendance",
            f"student={data['student_id']} course={course_id} >25%",
        )
    return jsonify(result)


# ─── Students / Teachers ───────────────────────────────────
@academic_bp.get("/students")
@jwt_required()
@permission_required("students.view")
def list_students():
    user = get_current_user()
    course_ids = owned_course_ids(user)
    if course_ids is not None:
        if not course_ids:
            return jsonify([])
        ids = {
            e.student_id
            for e in Enrollment.query.filter(
                Enrollment.course_id.in_(course_ids),
                Enrollment.status == "activa",
            ).all()
        }
        students = Student.query.filter(Student.id.in_(ids or [-1])).all()
        return jsonify([s.to_dict() for s in students])
    return jsonify([s.to_dict() for s in Student.query.all()])


@academic_bp.post("/students")
@jwt_required()
@permission_required("students.create")
def create_student():
    data = request.get_json(silent=True) or {}
    if User.query.filter(
        (User.username == data["username"]) | (User.email == data["email"])
    ).first():
        return jsonify({"error": "Usuario o email ya existe"}), 409

    user = User(
        username=data["username"],
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        must_change_password=True,
    )
    user.set_password(data.get("password", "Estudiante123!"))
    from app.models import Role

    role = Role.query.filter_by(code="STUDENT").first()
    if role:
        user.roles.append(role)
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        student_code=data["student_code"],
        document_id=data.get("document_id"),
        phone=data.get("phone"),
        address=data.get("address"),
        career_id=data.get("career_id"),
        guardian_name=data.get("guardian_name"),
        guardian_phone=data.get("guardian_phone"),
    )
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201


@academic_bp.put("/students/<int:sid>")
@jwt_required()
@permission_required("students.edit")
def update_student(sid):
    s = Student.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}
    for f in ("phone", "address", "career_id", "guardian_name", "guardian_phone", "status", "document_id", "student_code"):
        if f in data:
            setattr(s, f, data[f])
    if s.user:
        for f in ("first_name", "last_name", "email"):
            if f in data and data[f]:
                setattr(s.user, f, data[f])
    db.session.commit()
    return jsonify(s.to_dict())


@academic_bp.delete("/students/<int:sid>")
@jwt_required()
@permission_required("students.edit")
def delete_student(sid):
    s = Student.query.get_or_404(sid)
    uid = s.user_id
    Grade.query.filter_by(student_id=sid).delete()
    Attendance.query.filter_by(student_id=sid).delete()
    Enrollment.query.filter_by(student_id=sid).delete()
    db.session.delete(s)
    u = User.query.get(uid)
    if u and not u.is_protected:
        u.roles = []
        db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "Estudiante eliminado"})


@academic_bp.get("/teachers")
@jwt_required()
@permission_required("teachers.view")
def list_teachers():
    return jsonify([t.to_dict() for t in Teacher.query.all()])


@academic_bp.post("/teachers")
@jwt_required()
@permission_required("teachers.create")
def create_teacher():
    data = request.get_json(silent=True) or {}
    if User.query.filter(
        (User.username == data["username"]) | (User.email == data["email"])
    ).first():
        return jsonify({"error": "Usuario o email ya existe"}), 409

    user = User(
        username=data["username"],
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        must_change_password=True,
    )
    user.set_password(data.get("password", "Docente123!"))
    from app.models import Role

    role = Role.query.filter_by(code="TEACHER").first()
    if role:
        user.roles.append(role)
    db.session.add(user)
    db.session.flush()

    teacher = Teacher(
        user_id=user.id,
        teacher_code=data["teacher_code"],
        document_id=data.get("document_id"),
        phone=data.get("phone"),
        specialty=data.get("specialty"),
        title=data.get("title"),
    )
    db.session.add(teacher)
    db.session.commit()
    return jsonify(teacher.to_dict()), 201


@academic_bp.put("/teachers/<int:tid>")
@jwt_required()
@permission_required("teachers.edit")
def update_teacher(tid):
    t = Teacher.query.get_or_404(tid)
    data = request.get_json(silent=True) or {}
    for f in ("phone", "specialty", "title", "status", "document_id", "teacher_code"):
        if f in data:
            setattr(t, f, data[f])
    if t.user:
        for f in ("first_name", "last_name", "email"):
            if f in data and data[f]:
                setattr(t.user, f, data[f])
    db.session.commit()
    return jsonify(t.to_dict())


@academic_bp.delete("/teachers/<int:tid>")
@jwt_required()
@permission_required("teachers.edit")
def delete_teacher(tid):
    t = Teacher.query.get_or_404(tid)
    uid = t.user_id
    Assignment.query.filter_by(teacher_id=tid).delete()
    db.session.delete(t)
    u = User.query.get(uid)
    if u and not u.is_protected:
        u.roles = []
        db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "Docente eliminado"})


@academic_bp.delete("/grades/<int:gid>")
@jwt_required()
@permission_required("grades.manage")
def delete_grade(gid):
    g = Grade.query.get_or_404(gid)
    if not _teacher_owns_course(get_current_user(), g.course_id):
        return jsonify({"error": "Sin permiso sobre este curso"}), 403
    db.session.delete(g)
    db.session.commit()
    return jsonify({"message": "Nota eliminada"})


@academic_bp.delete("/attendance/<int:aid>")
@jwt_required()
@permission_required("attendance.manage")
def delete_attendance(aid):
    a = Attendance.query.get_or_404(aid)
    if not _teacher_owns_course(get_current_user(), a.course_id):
        return jsonify({"error": "Sin permiso sobre este curso"}), 403
    db.session.delete(a)
    db.session.commit()
    return jsonify({"message": "Registro eliminado"})
