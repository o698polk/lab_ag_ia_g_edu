"""
Seeder masivo académico:
- 3 carreras: Desarrollo de Software, Mecánica Automotriz, Mecanización Agrícola
- 30 docentes (10 por carrera)
- 420 estudiantes (140 por carrera)
- 4 periodos académicos con cursos, matrículas y notas
- Solo 1–2 periodos habilitados (is_active) visibles para estudiantes/docentes
"""

from __future__ import annotations

import random
from datetime import date, timedelta

FIRST_NAMES = [
    "Ana", "Luis", "María", "Carlos", "Sofía", "Diego", "Valentina", "Andrés",
    "Camila", "José", "Paula", "Miguel", "Lucía", "Pedro", "Elena", "Jorge",
    "Daniela", "Fernando", "Isabel", "Ricardo", "Gabriela", "Héctor", "Natalia",
    "Óscar", "Patricia", "Roberto", "Andrea", "Sebastián", "Carolina", "Felipe",
]
LAST_NAMES = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez",
    "Ramírez", "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Cruz", "Morales",
    "Reyes", "Ortiz", "Gutiérrez", "Chávez", "Ramos", "Vargas", "Castillo",
    "Jiménez", "Moreno", "Romero", "Alvarez", "Mendoza", "Herrera", "Medina",
]

CAREERS_DEF = [
    {
        "code": "DSW",
        "name": "Desarrollo de Software",
        "subjects": [
            ("DSW101", "Fundamentos de Programación", 4),
            ("DSW102", "Bases de Datos", 4),
            ("DSW103", "Desarrollo Web", 3),
            ("DSW104", "Ingeniería de Software", 3),
            ("DSW105", "Estructuras de Datos", 4),
            ("DSW106", "Aplicaciones Móviles", 3),
        ],
    },
    {
        "code": "MAU",
        "name": "Mecánica Automotriz",
        "subjects": [
            ("MAU101", "Sistemas del Automóvil", 4),
            ("MAU102", "Electricidad Automotriz", 3),
            ("MAU103", "Motores de Combustión", 4),
            ("MAU104", "Diagnóstico Electrónico", 3),
            ("MAU105", "Suspensión y Frenos", 3),
            ("MAU106", "Mantenimiento Preventivo", 3),
        ],
    },
    {
        "code": "MAG",
        "name": "Mecanización Agrícola",
        "subjects": [
            ("MAG101", "Maquinaria Agrícola", 4),
            ("MAG102", "Suelos y Cultivos", 3),
            ("MAG103", "Riego Tecnificado", 3),
            ("MAG104", "Mecanización de Cosecha", 4),
            ("MAG105", "Motores Agrícolas", 3),
            ("MAG106", "Gestión de Fincas", 3),
        ],
    },
]

TERMS_DEF = [
    # code, name, days_ago_start, days_ago_end, is_active, grades_closed
    ("2024-1", "Periodo 2024-1", 700, 520, False, True),
    ("2024-2", "Periodo 2024-2", 510, 330, False, True),
    ("2025-1", "Periodo 2025-1", 320, 140, True, False),   # habilitado
    ("2025-2", "Periodo 2025-2", 130, -50, True, False),    # habilitado (actual)
]


def _rand_grade():
    p1 = round(random.uniform(4.0, 10.0), 1)
    p2 = round(random.uniform(4.0, 10.0), 1)
    avg = (p1 + p2) / 2
    supp = None
    if avg < 7.0:
        supp = round(random.uniform(5.0, 9.5), 1)
    return p1, p2, supp


def clear_academic_data(db):
    from app.models import (
        AILog,
        Assignment,
        Attendance,
        AuditLog,
        Career,
        Course,
        Curriculum,
        Enrollment,
        Grade,
        Notification,
        RefreshToken,
        Schedule,
        Student,
        Subject,
        Teacher,
        Term,
        User,
    )
    from app.models.iam import user_roles

    # Orden por FKs
    for model in (
        Attendance,
        Grade,
        Schedule,
        Enrollment,
        Assignment,
        Course,
        Curriculum,
        Subject,
        Student,
        Teacher,
        Term,
        Notification,
        AILog,
        AuditLog,
        RefreshToken,
    ):
        model.query.delete()
    db.session.commit()

    # Eliminar usuarios no admin / no protegidos
    for u in User.query.filter(User.is_protected.is_(False)).all():
        u.roles = []
        db.session.delete(u)
    Career.query.delete()
    db.session.commit()


def ensure_role_perms(db):
    """SPEC-009: sincroniza permisos de visibilidad por perfil."""
    from seed_data import sync_profile_visibility_perms

    sync_profile_visibility_perms(db)


def seed_massive(app, reset: bool = True):
    from app.extensions import db
    from app.models import (
        Assignment,
        Career,
        Course,
        Enrollment,
        Grade,
        Role,
        Schedule,
        Student,
        Subject,
        Teacher,
        Term,
        User,
    )

    with app.app_context():
        if not Role.query.first():
            from seed_data import seed_all

            seed_all(app)

        ensure_role_perms(db)

        if Career.query.filter(Career.code.in_(["DSW", "MAU", "MAG"])).first():
            if not reset:
                print("Datos masivos ya existen. Use reset=True para recrear.")
                return False
            print("Limpiando datos académicos previos…")
            clear_academic_data(db)
        elif reset and (Student.query.count() > 0 or Career.query.count() > 0):
            print("Limpiando datos académicos previos…")
            clear_academic_data(db)

        role_teacher = Role.query.filter_by(code="TEACHER").first()
        role_student = Role.query.filter_by(code="STUDENT").first()
        today = date.today()

        # Periodos
        terms = []
        for code, name, start_off, end_off, active, closed in TERMS_DEF:
            t = Term(
                code=code,
                name=name,
                start_date=today - timedelta(days=start_off),
                end_date=today - timedelta(days=end_off),
                is_active=active,
                grades_closed=closed,
            )
            db.session.add(t)
            terms.append(t)
        db.session.flush()

        careers = []
        subjects_by_career = {}
        for cdef in CAREERS_DEF:
            c = Career(
                code=cdef["code"],
                name=cdef["name"],
                description=f"Carrera técnica de {cdef['name']}",
                duration_semesters=6,
                is_active=True,
            )
            db.session.add(c)
            db.session.flush()
            careers.append(c)
            subjects_by_career[c.id] = []
            for scode, sname, credits in cdef["subjects"]:
                s = Subject(
                    code=scode,
                    name=sname,
                    credits=credits,
                    career_id=c.id,
                    is_active=True,
                )
                db.session.add(s)
                subjects_by_career[c.id].append(s)
        db.session.flush()

        # 30 docentes: 10 por carrera
        teachers_by_career = {c.id: [] for c in careers}
        ti = 1
        for career in careers:
            for i in range(10):
                fn = random.choice(FIRST_NAMES)
                ln = random.choice(LAST_NAMES)
                username = f"docente{ti:02d}"
                u = User(
                    username=username,
                    email=f"{username}@institucion.edu",
                    first_name=fn,
                    last_name=ln,
                    must_change_password=False,
                    is_active=True,
                )
                u.set_password("Docente123!")
                u.roles.append(role_teacher)
                db.session.add(u)
                db.session.flush()
                t = Teacher(
                    user_id=u.id,
                    teacher_code=f"T-{ti:03d}",
                    specialty=career.name,
                    title="Ing.",
                    phone=f"09{10000000 + ti}",
                )
                db.session.add(t)
                db.session.flush()
                teachers_by_career[career.id].append(t)
                ti += 1
        db.session.flush()

        # 420 estudiantes: 140 por carrera
        students_by_career = {c.id: [] for c in careers}
        si = 1
        for career in careers:
            for i in range(140):
                fn = random.choice(FIRST_NAMES)
                ln = random.choice(LAST_NAMES)
                username = f"est{si:04d}"
                u = User(
                    username=username,
                    email=f"{username}@estudiante.edu",
                    first_name=fn,
                    last_name=ln,
                    must_change_password=False,
                    is_active=True,
                )
                u.set_password("Estudiante123!")
                u.roles.append(role_student)
                db.session.add(u)
                db.session.flush()
                st = Student(
                    user_id=u.id,
                    student_code=f"E-{si:04d}",
                    career_id=career.id,
                    phone=f"09{20000000 + si}",
                    status="active",
                )
                db.session.add(st)
                db.session.flush()
                students_by_career[career.id].append(st)
                si += 1
            if si % 50 == 0:
                db.session.flush()
        db.session.flush()
        print(f"Usuarios creados: {ti - 1} docentes, {si - 1} estudiantes")

        # Cursos por periodo × materia (paralelo A), asignación, matrícula y notas
        classrooms = ["A-101", "A-102", "B-201", "B-202", "Taller-1", "Lab-Soft", "Campo-1"]
        grade_count = 0
        enroll_count = 0

        for term in terms:
            for career in careers:
                subjects = subjects_by_career[career.id]
                teachers = teachers_by_career[career.id]
                students = students_by_career[career.id]

                for idx, subject in enumerate(subjects):
                    teacher = teachers[idx % len(teachers)]
                    course = Course(
                        code=f"{subject.code}-{term.code}-A",
                        name=f"{subject.name} ({term.code})",
                        subject_id=subject.id,
                        term_id=term.id,
                        career_id=career.id,
                        parallel="A",
                        capacity=50,
                        is_active=True,
                    )
                    db.session.add(course)
                    db.session.flush()

                    db.session.add(Assignment(teacher_id=teacher.id, course_id=course.id))
                    db.session.add(
                        Schedule(
                            course_id=course.id,
                            day_of_week=idx % 5,
                            start_time=f"{8 + (idx % 4) * 2:02d}:00",
                            end_time=f"{10 + (idx % 4) * 2:02d}:00",
                            classroom=random.choice(classrooms),
                        )
                    )

                    # Matricular ~35 estudiantes por curso (rotando)
                    start = (idx * 35) % max(1, len(students) - 35)
                    cohort = students[start : start + 35]
                    for st in cohort:
                        db.session.add(
                            Enrollment(student_id=st.id, course_id=course.id, status="activa")
                        )
                        enroll_count += 1
                        p1, p2, supp = _rand_grade()
                        g = Grade(
                            student_id=st.id,
                            course_id=course.id,
                            partial1=p1,
                            partial2=p2,
                            supplementary=supp,
                        )
                        g.compute()
                        db.session.add(g)
                        grade_count += 1

            db.session.flush()
            print(f"Periodo {term.code}: cursos y notas generados (active={term.is_active})")

        db.session.commit()
        print(
            f"OK — Carreras: {len(careers)} | Periodos: {len(terms)} | "
            f"Docentes: {ti - 1} | Estudiantes: {si - 1} | "
            f"Matrículas: {enroll_count} | Notas: {grade_count}"
        )
        print("Periodos habilitados (visibles):", [t.code for t in terms if t.is_active])
        print("Credenciales docentes: docente01..docente30 / Docente123!")
        print("Credenciales estudiantes: est0001..est0420 / Estudiante123!")
        return True


if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path

    BACKEND = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(BACKEND))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    os.chdir(BACKEND)

    from run import app

    seed_massive(app, reset=True)
