"""
Seeder académico coherente — SPEC-033 / SKILL-032 (+ legacy SPEC-011).

Dataset para testing avanzado:
- 3 carreras (DSW, MAU, MAG) × 6 materias
- 2 periodos académicos
- 20 docentes / 400 estudiantes
- Staff: rector, auditor, 3 coordinadores, secretaria, tutor, soporte TI
- Cursos (paralelos ≤50), asignaciones, horarios, matrículas, notas, asistencias
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from seed_massive import (
    CAREERS_DEF,
    FIRST_NAMES,
    LAST_NAMES,
    clear_academic_data,
)

# Periodo → índices de materias (0..5)
TERM_SUBJECT_MAP = {
    "2025-1": (0, 1, 2),
    "2025-2": (3, 4, 5),
}

# code, name, start_offset_days, end_offset_days, is_active, grades_closed
TERMS_COHERENT = [
    ("2025-1", "Periodo 2025-1", 200, 20, True, True),
    ("2025-2", "Periodo 2025-2", 10, -170, True, False),
]

# Distribución por carrera (orden CAREERS_DEF: DSW, MAU, MAG)
TEACHERS_PER_CAREER = {"DSW": 7, "MAU": 7, "MAG": 6}
STUDENTS_PER_CAREER = {"DSW": 134, "MAU": 133, "MAG": 133}

SESSIONS_PER_COURSE = 10
PARALLEL_SIZE = 45  # cupo por paralelo (≤ 60)
COURSE_CAPACITY = 50

# Perfil: (p1_lo, p1_hi, p2_lo, p2_hi, presente, ausente, tardanza, justificada)
PROFILES = [
    (8.5, 10.0, 8.5, 10.0, 0.92, 0.03, 0.03, 0.02),
    (7.5, 9.2, 7.5, 9.2, 0.85, 0.06, 0.06, 0.03),
    (6.0, 8.2, 6.0, 8.2, 0.75, 0.12, 0.08, 0.05),
    (4.5, 7.2, 4.5, 7.2, 0.62, 0.22, 0.10, 0.06),
    (5.0, 8.8, 5.0, 8.8, 0.68, 0.15, 0.12, 0.05),
]

STAFF_USERS = [
    ("rector", "Rector123!", "RECTOR", "Elena", "Rectora"),
    ("auditor", "Auditor123!", "AUDITOR", "Marco", "Auditor"),
    ("coord01", "Coord123!", "COORDINATOR", "Laura", "Coordinadora DSW"),
    ("coord02", "Coord123!", "COORDINATOR", "Pedro", "Coordinador MAU"),
    ("coord03", "Coord123!", "COORDINATOR", "Rosa", "Coordinadora MAG"),
    ("secretaria", "Secretaria123!", "SECRETARY", "Carmen", "Secretaria"),
    ("soporte", "Soporte123!", "IT_SUPPORT", "Diego", "Soporte TI"),
]


def _clamp_grade(v: float) -> float:
    return round(min(10.0, max(1.0, v)), 1)


def _profile_for(student_id: int):
    return PROFILES[student_id % len(PROFILES)]


def _session_dates(term_start: date, term_end: date, weekday: int, count: int) -> list[date]:
    start = term_start
    while start.weekday() != weekday:
        start += timedelta(days=1)
        if start > term_end:
            return []
    dates = []
    cur = start
    while cur <= term_end and len(dates) < count:
        dates.append(cur)
        cur += timedelta(days=7)
    return dates


def _pick_status(weights, rng: random.Random) -> str:
    labels = ["presente", "ausente", "tardanza", "justificada"]
    return rng.choices(labels, weights=weights, k=1)[0]


def _make_grades(profile, absence_ratio: float, rng: random.Random):
    p1_lo, p1_hi, p2_lo, p2_hi, *_ = profile
    penalty = min(1.5, absence_ratio * 2.5)
    p1 = _clamp_grade(rng.uniform(p1_lo, p1_hi) - penalty * rng.uniform(0, 1))
    p2 = _clamp_grade(rng.uniform(p2_lo, p2_hi) - penalty * rng.uniform(0, 1))
    avg = (p1 + p2) / 2.0
    supp = None
    if avg < 7.0:
        base = 5.5 + (p1_lo - 4.5) * 0.4
        supp = _clamp_grade(rng.uniform(base, min(10.0, base + 3.0)))
    return p1, p2, supp


def _chunks(items: list, size: int) -> list[list]:
    if not items:
        return []
    return [items[i : i + size] for i in range(0, len(items), size)]


def _create_staff(db, Role, User, rng: random.Random) -> dict:
    """Crea usuarios institucionales. Devuelve mapa code→User (incluye tutor)."""
    created = {}
    for username, password, role_code, first, last in STAFF_USERS:
        role = Role.query.filter_by(code=role_code).first()
        if not role:
            raise RuntimeError(f"Rol faltante: {role_code}")
        u = User(
            username=username,
            email=f"{username}@institucion.edu",
            first_name=first,
            last_name=last,
            must_change_password=False,
            is_active=True,
        )
        u.set_password(password)
        u.roles.append(role)
        db.session.add(u)
        db.session.flush()
        created[role_code if role_code not in created else username] = u
        created[username] = u
    return created


def seed_coherent(app, reset: bool = True):
    from app.extensions import db
    from app.models import (
        Assignment,
        Attendance,
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
    from seed_data import seed_all, sync_profile_visibility_perms

    rng = random.Random(42)

    with app.app_context():
        if not Role.query.first():
            seed_all(app)

        if reset:
            print("SPEC-033: limpiando datos academicos...")
            clear_academic_data(db)

        today = date.today()
        role_teacher = Role.query.filter_by(code="TEACHER").first()
        role_student = Role.query.filter_by(code="STUDENT").first()
        role_guardian = Role.query.filter_by(code="GUARDIAN").first()

        # Staff institucional
        staff = _create_staff(db, Role, User, rng)
        print(
            "Staff:",
            "rector, auditor, coord01..03, secretaria, soporte (+ tutor luego)",
        )

        # Periodos (solo 2)
        terms = []
        for code, name, start_off, end_off, active, closed in TERMS_COHERENT:
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
        print(
            "Periodos:",
            [(t.code, t.is_active, t.grades_closed, str(t.start_date), str(t.end_date)) for t in terms],
        )

        # Carreras + materias
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

        # Docentes (20)
        teachers_by_career = {c.id: [] for c in careers}
        ti = 1
        for career in careers:
            n = TEACHERS_PER_CAREER[career.code]
            for _ in range(n):
                u = User(
                    username=f"docente{ti:02d}",
                    email=f"docente{ti:02d}@institucion.edu",
                    first_name=rng.choice(FIRST_NAMES),
                    last_name=rng.choice(LAST_NAMES),
                    must_change_password=False,
                    is_active=True,
                )
                u.set_password("Docente123!")
                u.roles.append(role_teacher)
                db.session.add(u)
                db.session.flush()
                tch = Teacher(
                    user_id=u.id,
                    teacher_code=f"D-{ti:03d}",
                    specialty=career.name,
                    title="Ing.",
                    phone=f"09{10000000 + ti}",
                )
                db.session.add(tch)
                db.session.flush()
                teachers_by_career[career.id].append(tch)
                ti += 1
        db.session.flush()

        # Estudiantes (400)
        students_by_career = {c.id: [] for c in careers}
        si = 1
        for career in careers:
            n = STUDENTS_PER_CAREER[career.code]
            for _ in range(n):
                u = User(
                    username=f"est{si:04d}",
                    email=f"est{si:04d}@estudiante.edu",
                    first_name=rng.choice(FIRST_NAMES),
                    last_name=rng.choice(LAST_NAMES),
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
        db.session.flush()
        print(f"Docentes: {ti - 1} | Estudiantes: {si - 1}")

        # Tutor vinculado a primer estudiante DSW
        dsw = next(c for c in careers if c.code == "DSW")
        ward = students_by_career[dsw.id][0]
        tutor = User(
            username="tutor1",
            email="tutor1@institucion.edu",
            first_name="Ana",
            last_name="Tutora",
            must_change_password=False,
            is_active=True,
        )
        tutor.set_password("Tutor123!")
        tutor.roles.append(role_guardian)
        db.session.add(tutor)
        db.session.flush()
        ward.guardian_user_id = tutor.id
        ward.guardian_name = f"{tutor.first_name} {tutor.last_name}"
        ward.guardian_phone = "0987654321"
        staff["tutor1"] = tutor
        print(f"Tutor tutor1 -> estudiante {ward.student_code}")

        classrooms = ["A-101", "A-102", "B-201", "B-202", "Lab-Soft", "Taller-1", "Campo-1"]
        parallels = "ABCDEFGH"
        enroll_count = grade_count = attend_count = course_count = assign_count = 0

        for term_idx, term in enumerate(terms):
            subj_idxs = TERM_SUBJECT_MAP[term.code]
            for career in careers:
                subjects = subjects_by_career[career.id]
                teachers = teachers_by_career[career.id]
                students = students_by_career[career.id]
                cohorts = _chunks(students, PARALLEL_SIZE)

                for local_i, sidx in enumerate(subj_idxs):
                    subject = subjects[sidx]
                    for p_i, cohort in enumerate(cohorts):
                        parallel = parallels[p_i]
                        teacher = teachers[(term_idx * 3 + local_i + p_i) % len(teachers)]
                        course = Course(
                            code=f"{subject.code}-{term.code}-{parallel}",
                            name=f"{subject.name} ({term.code}) - {parallel}",
                            subject_id=subject.id,
                            term_id=term.id,
                            career_id=career.id,
                            parallel=parallel,
                            capacity=COURSE_CAPACITY,
                            is_active=True,
                        )
                        db.session.add(course)
                        db.session.flush()
                        course_count += 1

                        db.session.add(Assignment(teacher_id=teacher.id, course_id=course.id))
                        assign_count += 1

                        weekday = (sidx + term_idx + p_i) % 5
                        hour = 8 + ((local_i + p_i) % 4) * 2
                        db.session.add(
                            Schedule(
                                course_id=course.id,
                                day_of_week=weekday,
                                start_time=f"{hour:02d}:00",
                                end_time=f"{hour + 2:02d}:00",
                                classroom=classrooms[(sidx + p_i) % len(classrooms)],
                            )
                        )

                        session_dates = _session_dates(
                            term.start_date, term.end_date, weekday, SESSIONS_PER_COURSE
                        )
                        if len(session_dates) < 4:
                            session_dates = [
                                term.start_date + timedelta(days=7 * i)
                                for i in range(SESSIONS_PER_COURSE)
                                if term.start_date + timedelta(days=7 * i) <= term.end_date
                            ]

                        for st in cohort:
                            db.session.add(
                                Enrollment(
                                    student_id=st.id,
                                    course_id=course.id,
                                    status="activa",
                                )
                            )
                            enroll_count += 1

                            profile = _profile_for(st.id)
                            weights = profile[4:8]
                            statuses = [_pick_status(weights, rng) for _ in session_dates]
                            absences = sum(1 for s in statuses if s == "ausente")
                            absence_ratio = absences / max(1, len(statuses))

                            for d, status in zip(session_dates, statuses):
                                db.session.add(
                                    Attendance(
                                        student_id=st.id,
                                        course_id=course.id,
                                        session_date=d,
                                        status=status,
                                        notes=(
                                            "Justificado medico"
                                            if status == "justificada"
                                            else None
                                        ),
                                        recorded_by=teacher.user_id,
                                    )
                                )
                                attend_count += 1

                            p1, p2, supp = _make_grades(profile, absence_ratio, rng)
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
            print(f"Periodo {term.code}: cursos OK (active={term.is_active}, closed={term.grades_closed})")

        db.session.commit()
        sync_profile_visibility_perms(db)

        result = {
            "careers": len(careers),
            "terms": len(terms),
            "teachers": ti - 1,
            "students": si - 1,
            "courses": course_count,
            "assignments": assign_count,
            "enrollments": enroll_count,
            "grades": grade_count,
            "attendance": attend_count,
            "active_terms": [t.code for t in terms if t.is_active],
        }
        print(
            f"OK - Carreras: {result['careers']} | Periodos: {result['terms']} | "
            f"Cursos: {course_count} | Asignaciones: {assign_count} | "
            f"Matriculas: {enroll_count} | Notas: {grade_count} | Asistencias: {attend_count}"
        )
        print("Periodos visibles:", result["active_terms"])
        print("--- Credenciales testing ---")
        print("admin / (ADMIN_PASSWORD del .env)")
        print("rector / Rector123!  | auditor / Auditor123!")
        print("coord01..coord03 / Coord123!")
        print("secretaria / Secretaria123!  | tutor1 / Tutor123!  | soporte / Soporte123!")
        print("docente01..docente20 / Docente123!")
        print("est0001..est0400 / Estudiante123!")
        return result


if __name__ == "__main__":
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from run import app

    print(seed_coherent(app, reset=True))
