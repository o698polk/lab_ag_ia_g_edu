"""Seeds: roles, permisos, admin, config inicial. SPEC-003 + SPEC-007 + SKILL-003/007."""

from datetime import date, timedelta

MODULES = {
    "users": ["view", "create", "edit", "delete", "login-as"],
    "roles": ["view", "create", "edit", "delete"],
    "permissions": ["view", "create", "edit", "delete", "assign"],
    "students": ["view", "create", "edit"],
    "teachers": ["view", "create", "edit"],
    "careers": ["view", "create", "edit"],
    "subjects": ["view", "create", "edit"],
    "curriculum": ["view", "manage"],
    "terms": ["view", "create", "edit"],
    "courses": ["view", "create", "edit"],
    "assignments": ["view", "manage"],
    "enrollments": ["view", "create", "edit"],
    "schedules": ["view", "create", "edit"],
    "grades": ["view", "manage"],
    "attendance": ["view", "manage"],
    "kardex": ["view", "export"],
    "dashboard": ["view"],
    "reports": ["view", "export", "schedule"],
    "notifications": ["view", "send"],
    "history": ["view"],
    "ai": ["use", "configure", "view_logs"],
    "audit": ["view"],
}

ROLES = [
    ("ADMIN", "Administrador General", "Control total del sistema"),
    ("RECTOR", "Rector / Director", "Supervisión institucional"),
    ("COORDINATOR", "Coordinador Académico", "Gestión académica"),
    ("TEACHER", "Docente", "Notas y asistencia"),
    ("STUDENT", "Estudiante", "Consulta propia"),
    ("SECRETARY", "Secretaría", "Matrículas y registros"),
    ("REVIEWER", "Revisor", "Revisión solo lectura"),
    ("AUDITOR", "Auditor", "Logs y seguridad"),
    ("GUARDIAN", "Tutor / Representante", "Consulta del estudiante a cargo"),
    ("IT_SUPPORT", "Soporte TI", "Configuración técnica"),
]

ROLE_PERMS = {
    "ADMIN": "ALL",
    "RECTOR": [
        "dashboard.view", "reports.view", "reports.export", "students.view", "teachers.view",
        "careers.view", "subjects.view", "courses.view", "grades.view", "attendance.view",
        "kardex.view", "enrollments.view", "schedules.view", "notifications.view", "ai.use",
    ],
    "COORDINATOR": [
        "dashboard.view", "careers.view", "careers.create", "careers.edit",
        "subjects.view", "subjects.create", "subjects.edit",
        "curriculum.view", "curriculum.manage",
        "terms.view", "terms.create", "terms.edit",
        "courses.view", "courses.create", "courses.edit",
        "assignments.view", "assignments.manage",
        "schedules.view", "schedules.create", "schedules.edit",
        "students.view", "teachers.view", "enrollments.view",
        "grades.view", "attendance.view", "reports.view", "reports.export",
        "notifications.view", "notifications.send", "ai.use",
    ],
    "TEACHER": [
        "courses.view", "schedules.view", "terms.view", "subjects.view",
        "grades.view", "grades.manage", "attendance.view", "attendance.manage",
        "students.view", "notifications.view", "ai.use",
    ],
    "STUDENT": [
        "grades.view", "attendance.view", "schedules.view",
        "terms.view", "subjects.view", "courses.view", "enrollments.view",
        "notifications.view", "ai.use",
    ],
    "SECRETARY": [
        "dashboard.view", "students.view", "students.create", "students.edit",
        "enrollments.view", "enrollments.create", "enrollments.edit",
        "teachers.view", "careers.view", "courses.view", "terms.view",
        "reports.view", "reports.export", "notifications.view", "notifications.send",
        "kardex.view", "kardex.export", "ai.use",
    ],
    "REVIEWER": [
        "dashboard.view", "grades.view", "attendance.view", "students.view",
        "courses.view", "reports.view", "notifications.view",
    ],
    "AUDITOR": [
        "dashboard.view", "audit.view", "history.view", "reports.view", "reports.export",
        "ai.view_logs", "notifications.view",
    ],
    "GUARDIAN": [
        "grades.view", "attendance.view", "kardex.view",
        "schedules.view", "notifications.view",
    ],
    "IT_SUPPORT": [
        "dashboard.view", "users.view", "users.create", "users.edit",
        "roles.view", "permissions.view", "ai.configure", "ai.view_logs",
        "notifications.view", "history.view",
    ],
}


def sync_profile_visibility_perms(db=None):
    """SPEC-009 / SPEC-014: sincroniza permisos de perfiles restringidos.

    - Quita kardex.* y dashboard.view a STUDENT/TEACHER
    - Quita dashboard.view a GUARDIAN
    - Asegura enrollments.view a STUDENT y terms/subjects/courses.view
    """
    from app.extensions import db as _db
    from app.models import Permission, Role

    db = db or _db
    add_map = {
        "TEACHER": ["terms.view", "subjects.view", "courses.view"],
        "STUDENT": [
            "terms.view",
            "subjects.view",
            "courses.view",
            "enrollments.view",
        ],
    }
    remove_map = {
        "TEACHER": ["kardex.view", "kardex.export", "dashboard.view"],
        "STUDENT": ["kardex.view", "kardex.export", "dashboard.view"],
        "GUARDIAN": ["dashboard.view"],
    }
    changed = False
    role_codes = set(add_map) | set(remove_map)
    for role_code in role_codes:
        role = Role.query.filter_by(code=role_code).first()
        if not role:
            continue
        have = {f"{p.module}.{p.action}" for p in role.permissions}
        for code in add_map.get(role_code, []):
            if code in have:
                continue
            module, action = code.split(".", 1)
            p = Permission.query.filter_by(module=module, action=action).first()
            if p:
                role.permissions.append(p)
                changed = True
                have.add(code)
        for code in remove_map.get(role_code, []):
            module, action = code.split(".", 1)
            p = Permission.query.filter_by(module=module, action=action).first()
            if p and p in role.permissions:
                role.permissions.remove(p)
                changed = True
    if changed:
        db.session.commit()
    return changed


def seed_all(app):
    from app.extensions import db
    from app.models import (
        AIConfig,
        Career,
        Course,
        Permission,
        Role,
        Student,
        Subject,
        SystemConfig,
        Teacher,
        Term,
        User,
    )

    with app.app_context():
        if Role.query.first():
            sync_profile_visibility_perms(db)
            return False  # already seeded

        # Permissions
        perm_map = {}
        for module, actions in MODULES.items():
            for action in actions:
                p = Permission(module=module, action=action, description=f"{module}.{action}")
                db.session.add(p)
                perm_map[f"{module}.{action}"] = p
        db.session.flush()

        # Roles
        role_map = {}
        for code, name, desc in ROLES:
            r = Role(code=code, name=name, description=desc)
            if ROLE_PERMS[code] == "ALL":
                r.permissions = list(perm_map.values())
            else:
                r.permissions = [perm_map[c] for c in ROLE_PERMS[code] if c in perm_map]
            db.session.add(r)
            role_map[code] = r
        db.session.flush()

        # Admin
        admin = User(
            username=app.config["ADMIN_USERNAME"],
            email=app.config["ADMIN_EMAIL"],
            first_name="Administrador",
            last_name="General",
            is_active=True,
            is_protected=True,
            must_change_password=False,
            theme="light",
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        admin.roles.append(role_map["ADMIN"])
        db.session.add(admin)

        # Demo career / term / subject
        career = Career(code="SIS", name="Ingeniería en Sistemas", description="Carrera demo", duration_semesters=8)
        term = Term(
            code="2026-1",
            name="Periodo 2026-1",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=120),
            is_active=True,
        )
        subject = Subject(code="PROG1", name="Programación I", credits=4, career=career)
        db.session.add_all([career, term, subject])
        db.session.flush()

        course = Course(
            code="PROG1-A",
            name="Programación I - Paralelo A",
            subject_id=subject.id,
            term_id=term.id,
            career_id=career.id,
            parallel="A",
        )
        db.session.add(course)

        # Demo teacher
        t_user = User(
            username="docente1",
            email="docente1@institucion.edu",
            first_name="María",
            last_name="Docente",
            must_change_password=False,
        )
        t_user.set_password("Docente123!")
        t_user.roles.append(role_map["TEACHER"])
        db.session.add(t_user)
        db.session.flush()
        teacher = Teacher(user_id=t_user.id, teacher_code="T-001", specialty="Programación", title="Ing.")
        db.session.add(teacher)
        db.session.flush()

        from app.models import Assignment, Enrollment, Schedule

        db.session.add(Assignment(teacher_id=teacher.id, course_id=course.id))
        db.session.add(
            Schedule(
                course_id=course.id,
                day_of_week=0,
                start_time="08:00",
                end_time="10:00",
                classroom="Aula 101",
            )
        )

        # Demo student
        s_user = User(
            username="estudiante1",
            email="estudiante1@institucion.edu",
            first_name="Juan",
            last_name="Estudiante",
            must_change_password=False,
        )
        s_user.set_password("Estudiante123!")
        s_user.roles.append(role_map["STUDENT"])
        db.session.add(s_user)
        db.session.flush()
        student = Student(
            user_id=s_user.id,
            student_code="E-001",
            career_id=career.id,
            phone="0999999999",
        )
        db.session.add(student)
        db.session.flush()
        db.session.add(Enrollment(student_id=student.id, course_id=course.id, status="activa"))

        # System config
        defaults = {
            "system_name": app.config["SYSTEM_NAME"],
            "primary_color": "#0d6efd",
            "secondary_color": "#198754",
            "accent_color": "#0dcaf0",
            "default_theme": "light",
        }
        for k, v in defaults.items():
            db.session.add(SystemConfig(key=k, value=v, description=k))

        db.session.add(
            AIConfig(
                model="deepseek-chat",
                temperature=0.3,
                system_prompt="Eres el asistente del Sistema de Gestión Académica Institucional.",
                is_enabled=False,
            )
        )

        db.session.commit()
        sync_profile_visibility_perms(db)
        return True
